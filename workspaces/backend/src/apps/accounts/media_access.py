from __future__ import annotations

import mimetypes
import time
from dataclasses import dataclass
from urllib.parse import urlencode

from django.core import signing
from django.core.exceptions import ValidationError
from django.http import FileResponse

from .models import UserProfile
from .services import SystemRole, user_has_any_role

PROFILE_MEDIA_FIELDS = {
    "profile_photo",
    "document_front_image",
    "document_back_image",
    "document_selfie_image",
    "biometric_photo",
}

PROFILE_MEDIA_TOKEN_SALT = "accounts.profile-media.v1"
PROFILE_MEDIA_DEFAULT_TTL_SECONDS = 900


@dataclass(frozen=True)
class ProfileMediaResolution:
    profile: UserProfile
    field_name: str
    file_name: str


def can_user_access_profile_media(*, user, profile_user_id: int) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if user.id == profile_user_id:
        return True

    if bool(getattr(user, "is_superuser", False)) or bool(
        getattr(user, "is_staff", False)
    ):
        return True

    return user_has_any_role(user, [SystemRole.ADMIN])


def build_profile_media_url(
    *,
    request,
    profile: UserProfile,
    field_name: str,
) -> str | None:
    if field_name not in PROFILE_MEDIA_FIELDS:
        return None

    file_field = getattr(profile, field_name, None)
    if not file_field:
        return None

    expires_at = int(time.time()) + PROFILE_MEDIA_DEFAULT_TTL_SECONDS
    token_payload = {
        "profile_id": profile.id,
        "field_name": field_name,
        "file_name": str(file_field.name),
        "expires_at": expires_at,
    }
    token = signing.dumps(token_payload, salt=PROFILE_MEDIA_TOKEN_SALT)
    relative_url = (
        f"/api/v1/accounts/profile-media/{profile.id}/{field_name}/?"
        f"{urlencode({'token': token})}"
    )

    if request:
        return request.build_absolute_uri(relative_url)
    return relative_url


def resolve_signed_profile_media(
    *, profile_id: int, field_name: str, token: str
) -> ProfileMediaResolution:
    if field_name not in PROFILE_MEDIA_FIELDS:
        raise ValidationError("Campo de midia invalido.")

    try:
        payload = signing.loads(token, salt=PROFILE_MEDIA_TOKEN_SALT)
    except signing.BadSignature as exc:
        raise ValidationError("Token de acesso a midia invalido.") from exc

    if not isinstance(payload, dict):
        raise ValidationError("Token de acesso a midia invalido.")

    signed_profile_id = int(payload.get("profile_id", 0) or 0)
    signed_field_name = str(payload.get("field_name", "")).strip()
    signed_file_name = str(payload.get("file_name", "")).strip()
    signed_expires_at = int(payload.get("expires_at", 0) or 0)

    if signed_profile_id != profile_id or signed_field_name != field_name:
        raise ValidationError("Token de acesso a midia invalido.")
    if not signed_file_name or signed_expires_at < int(time.time()):
        raise ValidationError("Token de acesso a midia expirado.")

    profile = UserProfile.objects.select_related("user").filter(pk=profile_id).first()
    if profile is None:
        raise ValidationError("Perfil nao encontrado.")

    file_field = getattr(profile, field_name, None)
    if not file_field or str(file_field.name) != signed_file_name:
        raise ValidationError("Arquivo nao encontrado para o token informado.")

    return ProfileMediaResolution(
        profile=profile,
        field_name=field_name,
        file_name=signed_file_name,
    )


def build_profile_media_response(
    *,
    profile: UserProfile,
    field_name: str,
) -> FileResponse:
    file_field = getattr(profile, field_name, None)
    if not file_field:
        raise ValidationError("Arquivo nao encontrado.")

    try:
        file_handle = file_field.open("rb")
    except OSError as exc:
        raise ValidationError("Arquivo de midia indisponivel.") from exc

    content_type, _encoding = mimetypes.guess_type(str(file_field.name))
    response = FileResponse(
        file_handle,
        content_type=content_type or "application/octet-stream",
    )
    response["Cache-Control"] = "private, no-store"
    return response
