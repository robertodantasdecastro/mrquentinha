from __future__ import annotations

import json
from io import BytesIO
from urllib.error import URLError

import pytest
from django.core.files.base import ContentFile
from django.core.management import call_command

from apps.catalog.models import Dish, Ingredient, IngredientUnit

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\nIDATx\x9cc\xf8\x0f\x00\x01"
    b"\x01\x01\x00\x18\xdd\x8f\xe1\x00\x00\x00\x00IEND\xaeB`\x82"
)


class FakeResponse:
    def __init__(self, body: bytes, content_type: str = "application/json"):
        self._stream = BytesIO(body)
        self.headers = {"Content-Type": content_type}

    def read(self) -> bytes:
        return self._stream.read()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def build_commons_search_response(image_url: str) -> bytes:
    payload = {
        "query": {
            "pages": {
                "123": {
                    "imageinfo": [
                        {
                            "url": image_url,
                            "mime": "image/jpeg",
                        }
                    ]
                }
            }
        }
    }
    return json.dumps(payload).encode("utf-8")


@pytest.mark.django_db(transaction=True)
def test_sync_catalog_photos_preenche_imagem_para_prato_e_ingrediente(
    settings,
    tmp_path,
    monkeypatch,
):
    settings.MEDIA_ROOT = tmp_path / "media"

    ingredient = Ingredient.objects.create(name="tomate", unit=IngredientUnit.KILOGRAM)
    dish = Dish.objects.create(name="frango grelhado", yield_portions=5)

    def fake_urlopen(request, timeout=0):  # noqa: ARG001
        request_url = getattr(request, "full_url", str(request))
        if "w/api.php" in request_url:
            return FakeResponse(
                build_commons_search_response("https://images.example.test/photo.jpg")
            )
        return FakeResponse(PNG_BYTES, content_type="image/png")

    monkeypatch.setattr(
        "apps.catalog.management.commands.sync_catalog_photos.urlopen",
        fake_urlopen,
    )

    call_command("sync_catalog_photos")

    ingredient.refresh_from_db()
    dish.refresh_from_db()

    assert ingredient.image.name
    assert dish.image.name


@pytest.mark.django_db(transaction=True)
def test_sync_catalog_photos_sem_force_nao_sobrescreve_imagem_existente(
    settings,
    tmp_path,
    monkeypatch,
):
    settings.MEDIA_ROOT = tmp_path / "media"

    ingredient = Ingredient.objects.create(name="tomate", unit=IngredientUnit.KILOGRAM)
    ingredient.image.save(
        "catalog/ingredients/existente.png",
        ContentFile(PNG_BYTES),
        save=True,
    )
    previous_image_name = ingredient.image.name

    urlopen_call_count = {"total": 0}

    def fake_urlopen(request, timeout=0):  # noqa: ARG001
        urlopen_call_count["total"] += 1
        return FakeResponse(
            build_commons_search_response("https://images.example.test/photo.jpg")
        )

    monkeypatch.setattr(
        "apps.catalog.management.commands.sync_catalog_photos.urlopen",
        fake_urlopen,
    )

    call_command("sync_catalog_photos", only="ingredients")

    ingredient.refresh_from_db()
    assert ingredient.image.name == previous_image_name
    assert urlopen_call_count["total"] == 0


@pytest.mark.django_db(transaction=True)
def test_sync_catalog_photos_aplica_placeholder_quando_falha_download(
    settings,
    tmp_path,
    monkeypatch,
):
    settings.MEDIA_ROOT = tmp_path / "media"

    dish = Dish.objects.create(name="prato sem foto", yield_portions=3)

    def fake_urlopen(_request, timeout=0):  # noqa: ARG001
        raise URLError("offline")

    monkeypatch.setattr(
        "apps.catalog.management.commands.sync_catalog_photos.urlopen",
        fake_urlopen,
    )

    call_command("sync_catalog_photos", only="dishes", force=True)

    dish.refresh_from_db()
    assert dish.image.name
    assert dish.image.name.endswith(".svg")
