from __future__ import annotations

from datetime import date
from decimal import Decimal
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.catalog.models import Dish, Ingredient, IngredientUnit
from apps.procurement.models import Purchase


def build_test_image(*, filename: str = "test.png") -> SimpleUploadedFile:
    from PIL import Image

    image = Image.new("RGB", (24, 24), color=(255, 106, 0))
    buffer = BytesIO()
    image.save(buffer, format="PNG")

    return SimpleUploadedFile(
        filename,
        buffer.getvalue(),
        content_type="image/png",
    )


def build_large_test_image(
    *,
    width: int,
    height: int,
    filename: str = "large.png",
) -> SimpleUploadedFile:
    from PIL import Image

    image = Image.new("RGB", (width, height), color=(255, 106, 0))
    buffer = BytesIO()
    image.save(buffer, format="PNG")

    return SimpleUploadedFile(
        filename,
        buffer.getvalue(),
        content_type="image/png",
    )


@pytest.mark.django_db
def test_upload_ingredient_image_endpoint(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    ingredient = Ingredient.objects.create(name="Tomate", unit=IngredientUnit.KILOGRAM)

    response = client.post(
        f"/api/v1/catalog/ingredients/{ingredient.id}/image/",
        data={"image": build_test_image(filename="ingrediente.png")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["image_url"] is not None
    assert "/media/catalog/ingredients/" in body["image_url"]

    ingredient.refresh_from_db()
    assert ingredient.image.name


@pytest.mark.django_db
def test_upload_dish_image_endpoint(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    dish = Dish.objects.create(name="Frango da Casa", yield_portions=10)

    response = client.post(
        f"/api/v1/catalog/dishes/{dish.id}/image/",
        data={"image": build_test_image(filename="prato.png")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["image_url"] is not None
    assert "/media/catalog/dishes/" in body["image_url"]

    dish.refresh_from_db()
    assert dish.image.name


@pytest.mark.django_db
def test_upload_dish_image_endpoint_aplica_crop_central(client, settings, tmp_path):
    from PIL import Image

    settings.MEDIA_ROOT = tmp_path / "media"
    dish = Dish.objects.create(name="Frango Cropped", yield_portions=10)

    response = client.post(
        f"/api/v1/catalog/dishes/{dish.id}/image/",
        data={
            "image": build_large_test_image(
                filename="prato-retangular.png",
                width=2200,
                height=1200,
            )
        },
    )

    assert response.status_code == 200
    dish.refresh_from_db()
    assert dish.image.name

    with Image.open(dish.image.path) as saved:
        assert saved.width == 1200
        assert saved.height == 900


@pytest.mark.django_db
def test_upload_automatico_catalogo_aplica_crop_em_fluxo_save_false(settings, tmp_path):
    from PIL import Image

    settings.MEDIA_ROOT = tmp_path / "media"
    ingredient = Ingredient.objects.create(
        name="Tomate automatico",
        unit=IngredientUnit.KILOGRAM,
    )

    uploaded = build_large_test_image(
        filename="ingrediente-automatico.png",
        width=1800,
        height=1200,
    )
    ingredient.image.save(uploaded.name, uploaded, save=False)
    ingredient.save(update_fields=["image", "updated_at"])

    ingredient.refresh_from_db()
    with Image.open(ingredient.image.path) as saved:
        assert saved.width == 1000
        assert saved.height == 1000


@pytest.mark.django_db
def test_upload_purchase_receipt_image_endpoint(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    purchase = Purchase.objects.create(
        supplier_name="Fornecedor Teste",
        purchase_date=date(2026, 2, 24),
        total_amount=Decimal("120.00"),
    )

    response = client.post(
        f"/api/v1/procurement/purchases/{purchase.id}/receipt-image/",
        data={"receipt_image": build_test_image(filename="nota.png")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["receipt_image_url"] is not None
    assert "/media/procurement/receipts/" in body["receipt_image_url"]

    purchase.refresh_from_db()
    assert purchase.receipt_image.name


@pytest.mark.django_db
def test_upload_purchase_receipt_image_endpoint_redimensiona_sem_corte(
    client, settings, tmp_path
):
    from PIL import Image

    settings.MEDIA_ROOT = tmp_path / "media"
    purchase = Purchase.objects.create(
        supplier_name="Fornecedor Resize",
        purchase_date=date(2026, 2, 24),
        total_amount=Decimal("120.00"),
    )

    response = client.post(
        f"/api/v1/procurement/purchases/{purchase.id}/receipt-image/",
        data={
            "receipt_image": build_large_test_image(
                filename="nota-grande.png",
                width=2600,
                height=1400,
            )
        },
    )

    assert response.status_code == 200

    purchase.refresh_from_db()
    with Image.open(purchase.receipt_image.path) as saved:
        assert max(saved.width, saved.height) <= 1800
        original_ratio = 2600 / 1400
        saved_ratio = saved.width / saved.height
        assert abs(original_ratio - saved_ratio) < 0.05
