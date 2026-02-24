from __future__ import annotations

import json
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
