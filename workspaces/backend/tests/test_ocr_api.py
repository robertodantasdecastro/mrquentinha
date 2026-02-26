from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.catalog.models import (
    Ingredient,
    IngredientUnit,
    NutritionFact,
    NutritionSource,
)
from apps.ocr_ai.models import OCRJob, OCRJobStatus, OCRKind
from apps.procurement.models import Purchase, PurchaseItem


def build_test_image(*, filename: str = "ocr.png") -> SimpleUploadedFile:
    from PIL import Image

    image = Image.new("RGB", (40, 40), color=(245, 245, 245))
    buffer = BytesIO()
    image.save(buffer, format="PNG")

    return SimpleUploadedFile(
        filename,
        buffer.getvalue(),
        content_type="image/png",
    )


@pytest.mark.django_db
def test_create_ocr_job_endpoint_processa_em_modo_simulado(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"

    raw_text = "\n".join(
        [
            "Produto: Arroz Branco",
            "Marca: Marca Teste",
            "Peso liquido: 1 kg",
            "Porcao: 100 g",
            "Porcoes por embalagem: 10",
            "Valor energetico 128 kcal",
            "Carboidratos 28 g",
            "Proteinas 2.5 g",
            "Gorduras totais 0.3 g",
            "Gorduras saturadas 0.1 g",
            "Fibras 0.9 g",
            "Sodio 1 mg",
        ]
    )

    response = client.post(
        "/api/v1/ocr/jobs/",
        data={
            "kind": OCRKind.LABEL_BACK,
            "image": build_test_image(),
            "raw_text": raw_text,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["kind"] == OCRKind.LABEL_BACK
    assert body["status"] == OCRJobStatus.PROCESSED
    assert body["parsed_json"]["product_name"] == "Arroz Branco"


@pytest.mark.django_db
def test_apply_ocr_job_para_ingredient_preenche_nutrition_fact(
    client, settings, tmp_path
):
    settings.MEDIA_ROOT = tmp_path / "media"

    ingredient = Ingredient.objects.create(
        name="arroz teste", unit=IngredientUnit.KILOGRAM
    )

    create_response = client.post(
        "/api/v1/ocr/jobs/",
        data={
            "kind": OCRKind.LABEL_BACK,
            "image": build_test_image(filename="apply.png"),
            "raw_text": "\n".join(
                [
                    "Produto: Arroz Teste",
                    "Porcao: 100 g",
                    "Valor energetico 130 kcal",
                    "Carboidratos 27 g",
                    "Proteinas 3 g",
                    "Gorduras totais 1 g",
                    "Gorduras saturadas 0.3 g",
                    "Fibras 1.1 g",
                    "Sodio 4 mg",
                ]
            ),
        },
    )

    assert create_response.status_code == 201
    job_id = create_response.json()["id"]

    apply_response = client.post(
        f"/api/v1/ocr/jobs/{job_id}/apply/",
        data=json.dumps(
            {
                "target_type": "INGREDIENT",
                "target_id": ingredient.id,
                "mode": "merge",
            }
        ),
        content_type="application/json",
    )

    assert apply_response.status_code == 200
    apply_body = apply_response.json()
    assert apply_body["status"] == OCRJobStatus.APPLIED
    assert apply_body["target_type"] == "INGREDIENT"
    assert apply_body["target_id"] == ingredient.id

    nutrition_fact = NutritionFact.objects.get(ingredient=ingredient)
    assert nutrition_fact.energy_kcal_100g == 130
    assert nutrition_fact.carbs_g_100g == 27
    assert nutrition_fact.protein_g_100g == 3
    assert nutrition_fact.source == NutritionSource.OCR

    job = OCRJob.objects.get(pk=job_id)
    assert job.status == OCRJobStatus.APPLIED


@pytest.mark.django_db
def test_apply_ocr_job_para_purchase_item_salva_imagem_de_rotulo(
    client, settings, tmp_path
):
    settings.MEDIA_ROOT = tmp_path / "media"

    ingredient = Ingredient.objects.create(
        name="cenoura teste",
        unit=IngredientUnit.KILOGRAM,
    )
    purchase = Purchase.objects.create(
        supplier_name="Fornecedor OCR",
        purchase_date=date(2026, 2, 26),
        total_amount=Decimal("10.00"),
    )
    purchase_item = PurchaseItem.objects.create(
        purchase=purchase,
        ingredient=ingredient,
        qty=Decimal("1.000"),
        unit=IngredientUnit.KILOGRAM,
        unit_price=Decimal("10.00"),
    )

    create_response = client.post(
        "/api/v1/ocr/jobs/",
        data={
            "kind": OCRKind.LABEL_FRONT,
            "image": build_test_image(filename="label-front.png"),
            "raw_text": "Produto: Cenoura teste",
        },
    )
    assert create_response.status_code == 201
    job_id = create_response.json()["id"]

    apply_response = client.post(
        f"/api/v1/ocr/jobs/{job_id}/apply/",
        data=json.dumps(
            {
                "target_type": "PURCHASE_ITEM",
                "target_id": purchase_item.id,
                "mode": "merge",
            }
        ),
        content_type="application/json",
    )

    assert apply_response.status_code == 200
    apply_body = apply_response.json()
    assert apply_body["status"] == OCRJobStatus.APPLIED
    assert apply_body["target_type"] == "PURCHASE_ITEM"
    assert apply_body["saved_image_field"] == "label_front_image"

    purchase_item.refresh_from_db()
    assert purchase_item.label_front_image.name
    assert purchase_item.metadata["ocr"]["job_id"] == job_id


@pytest.mark.django_db
def test_apply_ocr_job_para_purchase_salva_imagem_de_comprovante(
    client, settings, tmp_path
):
    settings.MEDIA_ROOT = tmp_path / "media"

    purchase = Purchase.objects.create(
        supplier_name="Fornecedor OCR",
        purchase_date=date(2026, 2, 26),
        total_amount=Decimal("58.90"),
    )

    create_response = client.post(
        "/api/v1/ocr/jobs/",
        data={
            "kind": OCRKind.RECEIPT,
            "image": build_test_image(filename="receipt.png"),
            "raw_text": "\n".join(
                [
                    "Fornecedor: Fornecedor OCR",
                    "NF: NF-77",
                    "Total R$ 58,90",
                ]
            ),
        },
    )
    assert create_response.status_code == 201
    job_id = create_response.json()["id"]

    apply_response = client.post(
        f"/api/v1/ocr/jobs/{job_id}/apply/",
        data=json.dumps(
            {
                "target_type": "PURCHASE",
                "target_id": purchase.id,
                "mode": "merge",
            }
        ),
        content_type="application/json",
    )
    assert apply_response.status_code == 200
    apply_body = apply_response.json()
    assert apply_body["target_type"] == "PURCHASE"
    assert apply_body["saved_image_field"] == "receipt_image"

    purchase.refresh_from_db()
    assert purchase.receipt_image.name
