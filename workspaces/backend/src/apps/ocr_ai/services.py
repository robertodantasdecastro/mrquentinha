import re
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.catalog.models import NutritionFact, NutritionSource
from apps.procurement.models import PurchaseItem

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


def parse_label_text(raw_text: str) -> dict:
    compact_text = re.sub(r"\s+", " ", raw_text).strip()

    product_name = _find_first_match(
        raw_text,
        [
            r"produto\s*[:\-]\s*(.+)",
            r"nome\s*[:\-]\s*(.+)",
            r"descricao\s*[:\-]\s*(.+)",
        ],
    )
    if not product_name:
        first_line = next(
            (line.strip() for line in raw_text.splitlines() if line.strip()), ""
        )
        product_name = first_line or None

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
    from apps.catalog.models import Ingredient

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


def _apply_to_purchase_item(*, job: OCRJob, purchase_item_id: int, mode: str) -> dict:
    purchase_item = PurchaseItem.objects.filter(pk=purchase_item_id).first()
    if purchase_item is None:
        raise ValidationError("Item de compra de destino nao encontrado.")

    incoming_metadata = {
        "ocr": {
            "job_id": job.id,
            "kind": job.kind,
            "status": job.status,
            "parsed": job.parsed_json,
        }
    }

    if mode == "overwrite":
        purchase_item.metadata = incoming_metadata
    else:
        purchase_item.metadata = _deep_merge_dicts(
            purchase_item.metadata or {}, incoming_metadata
        )

    purchase_item.save(update_fields=["metadata"])

    return {
        "target_type": "PURCHASE_ITEM",
        "target_id": purchase_item.id,
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
    else:
        raise ValidationError("target_type invalido. Use INGREDIENT ou PURCHASE_ITEM.")

    job.status = OCRJobStatus.APPLIED
    job.save(update_fields=["status", "updated_at"])

    return {
        "job_id": job.id,
        "status": job.status,
        **result,
    }
