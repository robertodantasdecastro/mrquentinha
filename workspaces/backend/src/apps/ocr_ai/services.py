import re
import unicodedata
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.text import slugify

from apps.catalog.models import Ingredient, NutritionFact, NutritionSource
from apps.procurement.models import Purchase, PurchaseItem

from .models import OCRJob, OCRJobStatus, OCRKind


def _to_decimal(raw_value: str | int | float | Decimal | None) -> Decimal | None:
    if raw_value is None:
        return None

    if isinstance(raw_value, Decimal):
        return raw_value

    value_str = str(raw_value).strip()
    if not value_str:
        return None

    normalized = (
        value_str.replace("\xa0", " ").replace("%", "").replace(",", ".").strip()
    )
    normalized = re.sub(r"[^0-9.\-]", "", normalized)

    if not normalized:
        return None

    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def _extract_text_with_tesseract(image_path: str) -> str | None:
    try:
        import pytesseract
        from PIL import Image
    except Exception:
        return None

    try:
        return pytesseract.image_to_string(Image.open(image_path), lang="por+eng")
    except Exception:
        return None


def _find_first_match(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
    return None


def _parse_size_field(raw_value: str | None) -> dict | None:
    if not raw_value:
        return None

    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(kg|g|ml|l)", raw_value, flags=re.I)
    if not match:
        return None

    return {
        "value": str(_to_decimal(match.group(1)) or ""),
        "unit": match.group(2).lower(),
    }


def _extract_nutrient_value(text: str, aliases: list[str]) -> str | None:
    for alias in aliases:
        pattern = rf"{alias}[^\d]*(\d+(?:[.,]\d+)?)\s*(kcal|kj|g|mg)?"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = _to_decimal(match.group(1))
            if value is not None:
                return str(value)
    return None


def _normalize_lookup_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_value.lower().strip()
    return re.sub(r"[^a-z0-9]+", " ", lowered).strip()


def _extract_product_name_from_text(raw_text: str) -> str | None:
    product_name = _find_first_match(
        raw_text,
        [
            r"produto\s*[:\-]\s*(.+)",
            r"nome\s*[:\-]\s*(.+)",
            r"descricao\s*[:\-]\s*(.+)",
        ],
    )
    if product_name:
        return product_name

    first_line = next(
        (line.strip() for line in raw_text.splitlines() if line.strip()), ""
    )
    return first_line or None


def _resolve_recognized_ingredient(
    *, product_name: str | None, raw_text: str
) -> dict | None:
    if not product_name:
        return None

    normalized_product = _normalize_lookup_text(product_name)
    if not normalized_product:
        return None

    raw_normalized = _normalize_lookup_text(raw_text)
    ingredients = Ingredient.objects.all().only("id", "name")

    best_match = None
    best_score = 0.0
    product_tokens = set(normalized_product.split())
    for ingredient in ingredients:
        normalized_candidate = _normalize_lookup_text(ingredient.name)
        if not normalized_candidate:
            continue

        if normalized_candidate == normalized_product:
            return {
                "ingredient_id": ingredient.id,
                "ingredient_name": ingredient.name,
                "confidence": 1.0,
                "match_type": "exact",
            }

        sequence_score = SequenceMatcher(
            None, normalized_product, normalized_candidate
        ).ratio()
        token_set = set(normalized_candidate.split())
        union = product_tokens | token_set
        token_score = (len(product_tokens & token_set) / len(union)) if union else 0

        in_text_score = (
            0.78
            if re.search(rf"\b{re.escape(normalized_candidate)}\b", raw_normalized)
            else 0
        )
        score = max(sequence_score, token_score, in_text_score)
        if score > best_score:
            best_score = score
            best_match = ingredient

    if best_match is None or best_score < 0.62:
        return None

    return {
        "ingredient_id": best_match.id,
        "ingredient_name": best_match.name,
        "confidence": round(float(best_score), 3),
        "match_type": "fuzzy",
    }


def parse_label_text(raw_text: str) -> dict:
    compact_text = re.sub(r"\s+", " ", raw_text).strip()

    product_name = _extract_product_name_from_text(raw_text)

    brand = _find_first_match(
        raw_text,
        [
            r"marca\s*[:\-]\s*(.+)",
            r"fabricante\s*[:\-]\s*(.+)",
        ],
    )

    package_size_raw = _find_first_match(
        raw_text,
        [
            r"peso\s*(?:liquido|líquido)?\s*[:\-]\s*([0-9.,]+\s*(?:kg|g|ml|l))",
            r"conteudo\s*[:\-]\s*([0-9.,]+\s*(?:kg|g|ml|l))",
            r"volume\s*[:\-]\s*([0-9.,]+\s*(?:kg|g|ml|l))",
        ],
    )

    serving_size_raw = _find_first_match(
        raw_text,
        [
            r"por[cç][aã]o\s*[:\-]\s*([0-9.,]+\s*(?:g|ml))",
            r"porcao\s*[:\-]\s*([0-9.,]+\s*(?:g|ml))",
        ],
    )

    servings_per_package_raw = _find_first_match(
        raw_text,
        [
            r"por[cç][oõ]es\s*por\s*embalagem\s*[:\-]\s*([0-9.,]+)",
            r"porcoes\s*por\s*embalagem\s*[:\-]\s*([0-9.,]+)",
            r"rendimento\s*[:\-]\s*([0-9.,]+)\s*por[cç][oõ]es",
        ],
    )

    nutrients = {
        "energy_kcal": _extract_nutrient_value(
            raw_text, [r"valor\s+energetico", r"energia"]
        ),
        "carbs_g": _extract_nutrient_value(raw_text, [r"carboidratos", r"carboidrato"]),
        "protein_g": _extract_nutrient_value(raw_text, [r"prote[ií]nas", r"proteina"]),
        "fat_g": _extract_nutrient_value(
            raw_text, [r"gorduras\s+totais", r"gordura\s+total"]
        ),
        "sat_fat_g": _extract_nutrient_value(
            raw_text, [r"gorduras\s+saturadas", r"gordura\s+saturada"]
        ),
        "fiber_g": _extract_nutrient_value(raw_text, [r"fibras", r"fibra\s+alimentar"]),
        "sodium_mg": _extract_nutrient_value(raw_text, [r"s[oó]dio"]),
        "sugars_total_g": _extract_nutrient_value(
            raw_text, [r"a[cç][uú]cares\s+totais"]
        ),
        "sugars_added_g": _extract_nutrient_value(
            raw_text, [r"a[cç][uú]cares\s+adicionados"]
        ),
    }

    return {
        "product_name": product_name,
        "brand": brand,
        "package_size": _parse_size_field(package_size_raw),
        "serving_size": _parse_size_field(serving_size_raw),
        "servings_per_package": (
            str(_to_decimal(servings_per_package_raw) or "")
            if servings_per_package_raw
            else None
        ),
        "nutrients": {
            key: value for key, value in nutrients.items() if value is not None
        },
        "raw_excerpt": compact_text[:400],
    }


def parse_product_text(raw_text: str) -> dict:
    base = parse_label_text(raw_text)
    base["context"] = "product"
    return base


def parse_price_tag_text(raw_text: str) -> dict:
    product_name = _extract_product_name_from_text(raw_text)
    compact_text = re.sub(r"\s+", " ", raw_text).strip()

    unit_price_raw = _find_first_match(
        raw_text,
        [
            r"(?:r\$|pre[cç]o)\s*[:\-]?\s*([0-9]+[.,][0-9]{2})",
            r"valor\s*unit[aá]rio\s*[:\-]?\s*([0-9]+[.,][0-9]{2})",
        ],
    )
    total_price_raw = _find_first_match(
        raw_text,
        [
            r"valor\s*total\s*[:\-]?\s*([0-9]+[.,][0-9]{2})",
            r"total\s*[:\-]?\s*([0-9]+[.,][0-9]{2})",
        ],
    )
    package_size_raw = _find_first_match(
        raw_text,
        [
            r"peso\s*(?:liquido|líquido)?\s*[:\-]\s*([0-9.,]+\s*(?:kg|g|ml|l))",
            r"conteudo\s*[:\-]\s*([0-9.,]+\s*(?:kg|g|ml|l))",
        ],
    )

    return {
        "product_name": product_name,
        "unit_price": (
            str(_to_decimal(unit_price_raw) or "") if unit_price_raw else None
        ),
        "total_price": (
            str(_to_decimal(total_price_raw) or "") if total_price_raw else None
        ),
        "package_size": _parse_size_field(package_size_raw),
        "raw_excerpt": compact_text[:400],
    }


def parse_receipt_text(raw_text: str) -> dict:
    supplier_name = _find_first_match(
        raw_text,
        [
            r"fornecedor\s*[:\-]\s*(.+)",
            r"emitente\s*[:\-]\s*(.+)",
        ],
    )

    invoice_number = _find_first_match(
        raw_text,
        [
            r"nf[-\s]?[e]?\s*[:\-]?\s*([a-zA-Z0-9\-/.]+)",
            r"nota\s*fiscal\s*[:\-]?\s*([a-zA-Z0-9\-/.]+)",
        ],
    )

    total_amount_raw = _find_first_match(
        raw_text,
        [
            r"total\s*(?:r\$)?\s*[:\-]?\s*([0-9.,]+)",
            r"valor\s*total\s*[:\-]?\s*([0-9.,]+)",
        ],
    )

    return {
        "supplier_name": supplier_name,
        "invoice_number": invoice_number,
        "total_amount": (
            str(_to_decimal(total_amount_raw) or "") if total_amount_raw else None
        ),
        "raw_excerpt": re.sub(r"\s+", " ", raw_text).strip()[:400],
    }


def _parse_raw_text(kind: str, raw_text: str) -> dict:
    if kind == OCRKind.RECEIPT:
        return parse_receipt_text(raw_text)
    if kind == OCRKind.PRICE_TAG:
        return parse_price_tag_text(raw_text)
    if kind == OCRKind.PRODUCT:
        return parse_product_text(raw_text)
    return parse_label_text(raw_text)


def process_ocr_job(job: OCRJob, *, raw_text_override: str | None = None) -> OCRJob:
    raw_text = raw_text_override or job.raw_text

    if not raw_text:
        raw_text = _extract_text_with_tesseract(job.image.path)

    if not raw_text:
        raise ValidationError(
            "Nao foi possivel extrair texto automaticamente. "
            "Envie raw_text para simulacao no MVP."
        )

    parsed_json = _parse_raw_text(job.kind, raw_text)
    if isinstance(parsed_json, dict) and job.kind != OCRKind.RECEIPT:
        parsed_json["recognized_ingredient"] = _resolve_recognized_ingredient(
            product_name=str(parsed_json.get("product_name") or ""),
            raw_text=raw_text,
        )

    job.raw_text = raw_text
    job.parsed_json = parsed_json
    job.status = OCRJobStatus.PROCESSED
    job.error_message = None
    job.save(
        update_fields=[
            "raw_text",
            "parsed_json",
            "status",
            "error_message",
            "updated_at",
        ]
    )

    return job


@transaction.atomic
def create_ocr_job(*, kind: str, image, raw_text: str | None = None) -> OCRJob:
    job = OCRJob.objects.create(kind=kind, image=image, raw_text=raw_text)

    try:
        process_ocr_job(job, raw_text_override=raw_text)
    except ValidationError as exc:
        job.status = OCRJobStatus.FAILED
        job.error_message = " ".join(exc.messages)
        job.save(update_fields=["status", "error_message", "updated_at"])

    return job


def _update_nutrition_fact_field(
    *, nutrition_fact: NutritionFact, field_name: str, value: Decimal | None, mode: str
) -> None:
    if value is None:
        return

    current_value = getattr(nutrition_fact, field_name)
    if mode == "overwrite" or current_value is None:
        setattr(nutrition_fact, field_name, value)


def _apply_to_ingredient(*, job: OCRJob, ingredient_id: int, mode: str) -> dict:
    ingredient = Ingredient.objects.filter(pk=ingredient_id).first()
    if ingredient is None:
        raise ValidationError("Ingrediente de destino nao encontrado.")

    nutrition_fact, _ = NutritionFact.objects.get_or_create(ingredient=ingredient)

    nutrients = (
        job.parsed_json.get("nutrients", {})
        if isinstance(job.parsed_json, dict)
        else {}
    )

    _update_nutrition_fact_field(
        nutrition_fact=nutrition_fact,
        field_name="energy_kcal_100g",
        value=_to_decimal(nutrients.get("energy_kcal")),
        mode=mode,
    )
    _update_nutrition_fact_field(
        nutrition_fact=nutrition_fact,
        field_name="carbs_g_100g",
        value=_to_decimal(nutrients.get("carbs_g")),
        mode=mode,
    )
    _update_nutrition_fact_field(
        nutrition_fact=nutrition_fact,
        field_name="protein_g_100g",
        value=_to_decimal(nutrients.get("protein_g")),
        mode=mode,
    )
    _update_nutrition_fact_field(
        nutrition_fact=nutrition_fact,
        field_name="fat_g_100g",
        value=_to_decimal(nutrients.get("fat_g")),
        mode=mode,
    )
    _update_nutrition_fact_field(
        nutrition_fact=nutrition_fact,
        field_name="sat_fat_g_100g",
        value=_to_decimal(nutrients.get("sat_fat_g")),
        mode=mode,
    )
    _update_nutrition_fact_field(
        nutrition_fact=nutrition_fact,
        field_name="fiber_g_100g",
        value=_to_decimal(nutrients.get("fiber_g")),
        mode=mode,
    )
    _update_nutrition_fact_field(
        nutrition_fact=nutrition_fact,
        field_name="sodium_mg_100g",
        value=_to_decimal(nutrients.get("sodium_mg")),
        mode=mode,
    )

    serving_size = None
    if isinstance(job.parsed_json, dict):
        serving_data = job.parsed_json.get("serving_size")
        if isinstance(serving_data, dict):
            serving_size = _to_decimal(serving_data.get("value"))

    _update_nutrition_fact_field(
        nutrition_fact=nutrition_fact,
        field_name="serving_size_g",
        value=serving_size,
        mode=mode,
    )

    nutrition_fact.source = NutritionSource.OCR
    nutrition_fact.save()

    return {
        "target_type": "INGREDIENT",
        "target_id": ingredient.id,
        "nutrition_fact_id": nutrition_fact.id,
    }


def _deep_merge_dicts(base: dict, incoming: dict) -> dict:
    merged = dict(base)
    for key, value in incoming.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def _save_ocr_image_into_field(
    *,
    job: OCRJob,
    target_instance,
    field_name: str,
    mode: str,
) -> bool:
    target_field = getattr(target_instance, field_name)
    if mode != "overwrite" and target_field:
        return False

    with job.image.open("rb"):
        image_bytes = job.image.read()

    extension = Path(job.image.name).suffix or ".jpg"
    target_slug = slugify(target_instance.__class__.__name__) or "target"
    filename = (
        f"ocr/applied/{target_slug}-{target_instance.id}-" f"job-{job.id}{extension}"
    )
    target_field.save(filename, ContentFile(image_bytes), save=False)
    return True


def _resolve_purchase_item_image_field(kind: str) -> str:
    if kind == OCRKind.LABEL_FRONT:
        return "label_front_image"
    if kind == OCRKind.LABEL_BACK:
        return "label_back_image"
    if kind == OCRKind.PRODUCT:
        return "product_image"
    if kind == OCRKind.PRICE_TAG:
        return "price_tag_image"
    raise ValidationError(
        "Somente LABEL_FRONT, LABEL_BACK, PRODUCT e PRICE_TAG podem ser "
        "aplicados em PURCHASE_ITEM."
    )


def _apply_to_purchase(*, job: OCRJob, purchase_id: int, mode: str) -> dict:
    purchase = Purchase.objects.filter(pk=purchase_id).first()
    if purchase is None:
        raise ValidationError("Compra de destino nao encontrada.")

    if job.kind != OCRKind.RECEIPT:
        raise ValidationError("Somente OCR de RECEIPT pode ser aplicado em PURCHASE.")

    saved_image = _save_ocr_image_into_field(
        job=job,
        target_instance=purchase,
        field_name="receipt_image",
        mode=mode,
    )

    parsed = job.parsed_json if isinstance(job.parsed_json, dict) else {}
    supplier_name = parsed.get("supplier_name")
    invoice_number = parsed.get("invoice_number")
    total_amount = _to_decimal(parsed.get("total_amount"))

    fields_to_update: list[str] = []
    if mode == "overwrite" or (not purchase.supplier_name and supplier_name):
        if supplier_name:
            purchase.supplier_name = str(supplier_name).strip()
            fields_to_update.append("supplier_name")

    if mode == "overwrite" or (not purchase.invoice_number and invoice_number):
        if invoice_number:
            purchase.invoice_number = str(invoice_number).strip()
            fields_to_update.append("invoice_number")

    if mode == "overwrite" or (purchase.total_amount <= 0 and total_amount is not None):
        if total_amount is not None and total_amount >= 0:
            purchase.total_amount = total_amount
            fields_to_update.append("total_amount")

    if saved_image:
        fields_to_update.append("receipt_image")

    if fields_to_update:
        purchase.save(update_fields=fields_to_update)

    return {
        "target_type": "PURCHASE",
        "target_id": purchase.id,
        "saved_image_field": "receipt_image" if saved_image else None,
    }


def _apply_to_purchase_item(*, job: OCRJob, purchase_item_id: int, mode: str) -> dict:
    purchase_item = PurchaseItem.objects.filter(pk=purchase_item_id).first()
    if purchase_item is None:
        raise ValidationError("Item de compra de destino nao encontrado.")

    kind_key = str(job.kind).lower()
    incoming_metadata = {
        "ocr": {
            "last_job_id": job.id,
            "last_kind": job.kind,
            "last_status": job.status,
            "jobs": {
                kind_key: {
                    "job_id": job.id,
                    "kind": job.kind,
                    "status": job.status,
                    "parsed": job.parsed_json,
                }
            },
        }
    }

    if mode == "overwrite":
        purchase_item.metadata = incoming_metadata
    else:
        purchase_item.metadata = _deep_merge_dicts(
            purchase_item.metadata or {}, incoming_metadata
        )

    image_field_name = _resolve_purchase_item_image_field(job.kind)
    saved_image = _save_ocr_image_into_field(
        job=job,
        target_instance=purchase_item,
        field_name=image_field_name,
        mode=mode,
    )

    parsed = job.parsed_json if isinstance(job.parsed_json, dict) else {}
    fields_to_update = ["metadata"]
    if job.kind == OCRKind.PRICE_TAG:
        unit_price = _to_decimal(parsed.get("unit_price"))
        if unit_price is not None and unit_price >= 0:
            if mode == "overwrite" or purchase_item.unit_price <= 0:
                purchase_item.unit_price = unit_price
                fields_to_update.append("unit_price")

    if saved_image:
        fields_to_update.append(image_field_name)

    purchase_item.save(update_fields=fields_to_update)

    return {
        "target_type": "PURCHASE_ITEM",
        "target_id": purchase_item.id,
        "saved_image_field": image_field_name if saved_image else None,
    }


@transaction.atomic
def apply_ocr_job(
    *,
    job_id: int,
    target_type: str,
    target_id: int,
    mode: str,
) -> dict:
    job = OCRJob.objects.select_for_update().filter(pk=job_id).first()
    if job is None:
        raise ValidationError("OCR job nao encontrado.")

    if mode not in {"overwrite", "merge"}:
        raise ValidationError("Modo invalido. Use overwrite ou merge.")

    if job.status == OCRJobStatus.PENDING:
        process_ocr_job(job)

    if job.status == OCRJobStatus.FAILED:
        raise ValidationError("OCR job esta em estado FAILED e nao pode ser aplicado.")

    if target_type == "INGREDIENT":
        result = _apply_to_ingredient(job=job, ingredient_id=target_id, mode=mode)
    elif target_type == "PURCHASE_ITEM":
        result = _apply_to_purchase_item(
            job=job,
            purchase_item_id=target_id,
            mode=mode,
        )
    elif target_type == "PURCHASE":
        result = _apply_to_purchase(
            job=job,
            purchase_id=target_id,
            mode=mode,
        )
    else:
        raise ValidationError(
            "target_type invalido. Use INGREDIENT, PURCHASE_ITEM ou PURCHASE."
        )

    job.status = OCRJobStatus.APPLIED
    job.save(update_fields=["status", "updated_at"])

    return {
        "job_id": job.id,
        "status": job.status,
        **result,
    }
