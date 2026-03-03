from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Literal

from django.apps import apps
from django.core.files.base import ContentFile
from django.db.models import ImageField
from django.db.models.signals import pre_save
from PIL import Image, ImageOps, UnidentifiedImageError

ImageMode = Literal["crop", "contain"]


@dataclass(frozen=True)
class ImageTransformSpec:
    mode: ImageMode
    width: int
    height: int
    quality: int = 88


# Perfis de transformacao por contexto.
# Cardapio usa corte central para manter vitrine consistente.
IMAGE_TRANSFORM_SPECS: dict[tuple[str, str], ImageTransformSpec] = {
    ("catalog.dish", "image"): ImageTransformSpec(mode="crop", width=1200, height=900),
    ("catalog.ingredient", "image"): ImageTransformSpec(
        mode="crop", width=1000, height=1000
    ),
    ("accounts.userprofile", "profile_photo"): ImageTransformSpec(
        mode="crop", width=800, height=800
    ),
    ("accounts.userprofile", "document_front_image"): ImageTransformSpec(
        mode="contain", width=1800, height=1800
    ),
    ("accounts.userprofile", "document_back_image"): ImageTransformSpec(
        mode="contain", width=1800, height=1800
    ),
    ("accounts.userprofile", "document_selfie_image"): ImageTransformSpec(
        mode="contain", width=1800, height=1800
    ),
    ("accounts.userprofile", "biometric_photo"): ImageTransformSpec(
        mode="contain", width=1400, height=1400
    ),
    ("procurement.purchase", "receipt_image"): ImageTransformSpec(
        mode="contain", width=1800, height=1800
    ),
    ("procurement.purchaseitem", "label_front_image"): ImageTransformSpec(
        mode="contain", width=1600, height=1600
    ),
    ("procurement.purchaseitem", "label_back_image"): ImageTransformSpec(
        mode="contain", width=1600, height=1600
    ),
    ("procurement.purchaseitem", "product_image"): ImageTransformSpec(
        mode="contain", width=1800, height=1800
    ),
    ("procurement.purchaseitem", "price_tag_image"): ImageTransformSpec(
        mode="contain", width=1400, height=1400
    ),
    ("ocr_ai.ocrjob", "image"): ImageTransformSpec(
        mode="contain", width=1800, height=1800
    ),
}

DEFAULT_IMAGE_TRANSFORM_SPEC = ImageTransformSpec(
    mode="contain", width=1600, height=1600
)
_SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}
_SIGNALS_REGISTERED = False


def _resample_filter() -> int:
    resampling = getattr(Image, "Resampling", None)
    if resampling is not None:
        return resampling.LANCZOS
    return Image.LANCZOS


def _resolve_spec(*, model_label_lower: str, field_name: str) -> ImageTransformSpec:
    return IMAGE_TRANSFORM_SPECS.get(
        (model_label_lower, field_name),
        DEFAULT_IMAGE_TRANSFORM_SPEC,
    )


def _normalize_image_bytes(
    *,
    raw_bytes: bytes,
    spec: ImageTransformSpec,
) -> bytes | None:
    if not raw_bytes:
        return None

    try:
        with Image.open(BytesIO(raw_bytes)) as opened:
            input_format = (opened.format or "").upper()
            if input_format not in _SUPPORTED_FORMATS:
                return None

            normalized = ImageOps.exif_transpose(opened)
            resample = _resample_filter()

            if spec.mode == "crop":
                transformed = ImageOps.fit(
                    normalized,
                    (spec.width, spec.height),
                    method=resample,
                    centering=(0.5, 0.5),
                )
            else:
                transformed = normalized.copy()
                transformed.thumbnail((spec.width, spec.height), resample)

            if input_format == "JPEG":
                transformed = transformed.convert("RGB")

            output = BytesIO()
            save_kwargs: dict[str, int | bool] = {"optimize": True}
            if input_format == "JPEG":
                save_kwargs["quality"] = spec.quality
                save_kwargs["progressive"] = True

            transformed.save(output, format=input_format, **save_kwargs)
            return output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError):
        return None


def _process_uncommitted_field(*, field_file, spec: ImageTransformSpec) -> None:
    uploaded = getattr(field_file, "file", None)
    if uploaded is None:
        return

    try:
        if hasattr(uploaded, "seek"):
            uploaded.seek(0)
        raw_bytes = uploaded.read()
    except OSError:
        return

    normalized = _normalize_image_bytes(raw_bytes=raw_bytes, spec=spec)
    if not normalized:
        return

    filename = Path(field_file.name).name or "upload.jpg"
    field_file.save(filename, ContentFile(normalized), save=False)


def _process_committed_field(*, field_file, spec: ImageTransformSpec) -> None:
    try:
        file_path = Path(field_file.path)
    except (NotImplementedError, ValueError):
        return

    if not file_path.exists() or not file_path.is_file():
        return

    try:
        raw_bytes = file_path.read_bytes()
    except OSError:
        return

    normalized = _normalize_image_bytes(raw_bytes=raw_bytes, spec=spec)
    if not normalized:
        return

    try:
        file_path.write_bytes(normalized)
    except OSError:
        return


def _register_model_receiver(*, model) -> None:
    image_field_names = [
        field.name
        for field in model._meta.get_fields()
        if isinstance(field, ImageField)
    ]
    if not image_field_names:
        return

    def _apply_image_pipeline(
        sender, instance, raw=False, update_fields=None, **kwargs
    ):
        if raw:
            return

        update_fields_set = set(update_fields) if update_fields is not None else None

        for field_name in image_field_names:
            if update_fields_set is not None and field_name not in update_fields_set:
                continue

            field_file = getattr(instance, field_name, None)
            if not field_file or not getattr(field_file, "name", ""):
                continue

            spec = _resolve_spec(
                model_label_lower=sender._meta.label_lower,
                field_name=field_name,
            )

            if not getattr(field_file, "_committed", True):
                _process_uncommitted_field(field_file=field_file, spec=spec)
                continue

            if update_fields_set is not None and field_name in update_fields_set:
                _process_committed_field(field_file=field_file, spec=spec)

    pre_save.connect(
        _apply_image_pipeline,
        sender=model,
        weak=False,
        dispatch_uid=f"mrq-image-pipeline:{model._meta.label_lower}",
    )


def register_image_pipeline_signals() -> None:
    global _SIGNALS_REGISTERED
    if _SIGNALS_REGISTERED:
        return

    for model in apps.get_models():
        _register_model_receiver(model=model)

    _SIGNALS_REGISTERED = True
