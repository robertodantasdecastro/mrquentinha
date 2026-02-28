from __future__ import annotations

import json
import time
from typing import Any
from urllib.parse import urlparse

from django.db.utils import DatabaseError, OperationalError, ProgrammingError

from .models import AdminActivityLog

SENSITIVE_KEYS = {
    "password",
    "token",
    "secret",
    "api_key",
    "access_token",
    "refresh_token",
    "authorization",
    "cookie",
    "private_key",
}

IGNORED_PATH_PREFIXES = ("/api/v1/admin-audit/admin-activity/",)


class AdminActivityLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _store_request_body_snapshot(request)
        started_at = time.perf_counter()
        response = None
        try:
            response = self.get_response(request)
            return response
        finally:
            try:
                self._persist_log(
                    request=request, response=response, started_at=started_at
                )
            except (DatabaseError, OperationalError, ProgrammingError):
                # Nao interrompe request quando tabela/banco ainda nao estao prontos.
                pass
            except Exception:
                # Auditoria nunca deve interromper a aplicacao.
                pass

    def _persist_log(self, *, request, response, started_at: float) -> None:
        path = str(getattr(request, "path", "") or "").strip()
        if not path.startswith("/api/v1/"):
            return
        if any(path.startswith(prefix) for prefix in IGNORED_PATH_PREFIXES):
            return

        user = getattr(request, "user", None)
        is_admin_actor = _is_admin_actor(user)
        is_admin_origin = _is_admin_origin(request)
        if not is_admin_actor and not is_admin_origin:
            return

        method = str(getattr(request, "method", "") or "GET").upper()[:8]
        status_code = int(getattr(response, "status_code", 500) or 500)
        duration_ms = max(0, int((time.perf_counter() - started_at) * 1000))

        action_group, resource = _resolve_action(path)
        channel = _resolve_channel(request=request, is_admin_origin=is_admin_origin)

        payload_summary = _extract_payload_summary(request)
        query_params = _extract_query_params_summary(request)
        query_string = _build_sanitized_query_string(query_params)

        actor_username = ""
        actor_is_staff = False
        actor_is_superuser = False
        actor = None
        if user and getattr(user, "is_authenticated", False):
            actor = user
            actor_username = str(getattr(user, "username", "") or "").strip()
            actor_is_staff = bool(getattr(user, "is_staff", False))
            actor_is_superuser = bool(getattr(user, "is_superuser", False))

        AdminActivityLog.objects.create(
            actor=actor,
            actor_username=actor_username,
            actor_is_staff=actor_is_staff,
            actor_is_superuser=actor_is_superuser,
            channel=channel,
            method=method,
            path=path[:255],
            query_string=query_string,
            action_group=action_group,
            resource=resource,
            http_status=status_code,
            is_success=200 <= status_code < 400,
            duration_ms=duration_ms,
            ip_address=_extract_client_ip(request),
            origin=str(request.headers.get("Origin", "") or "")[:255],
            referer=str(request.headers.get("Referer", "") or "")[:2000],
            user_agent=str(request.headers.get("User-Agent", "") or "")[:512],
            metadata={
                "query_params": query_params,
                "request_payload": payload_summary,
            },
        )


def _contains_sensitive_fragment(key: str) -> bool:
    normalized = str(key or "").strip().lower()
    if not normalized:
        return False
    if normalized in SENSITIVE_KEYS:
        return True
    return any(fragment in normalized for fragment in SENSITIVE_KEYS)


def _scrub_value(value: Any, depth: int = 0):
    if depth > 6:
        return "<truncated>"

    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, nested in value.items():
            normalized_key = str(key)
            if _contains_sensitive_fragment(normalized_key):
                cleaned[normalized_key] = "***"
            else:
                cleaned[normalized_key] = _scrub_value(nested, depth + 1)
        return cleaned

    if isinstance(value, list):
        return [_scrub_value(item, depth + 1) for item in value[:50]]

    if isinstance(value, tuple):
        return [_scrub_value(item, depth + 1) for item in list(value)[:50]]

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    return str(value)


def _extract_payload_summary(request) -> dict:
    method = str(getattr(request, "method", "")).upper()
    if method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return {}

    content_type = str(request.headers.get("Content-Type", "") or "").lower()

    max_body_size = 8192
    try:
        content_length = int(request.headers.get("Content-Length", "0") or "0")
    except (TypeError, ValueError):
        content_length = 0

    if content_length > max_body_size:
        return {"omitted": "payload_too_large"}

    if "application/json" in content_type:
        raw_body = getattr(request, "_admin_audit_body_snapshot", b"") or b""
        if not raw_body:
            try:
                raw_body = request.body or b""
            except Exception:
                raw_body = b""
        if len(raw_body) > max_body_size:
            return {"omitted": "payload_too_large"}
        if not raw_body:
            return {}
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {"omitted": "invalid_json"}
        return _scrub_value(payload)

    if "application/x-www-form-urlencoded" in content_type:
        try:
            data = {key: request.POST.getlist(key) for key in request.POST.keys()}
        except Exception:
            return {"omitted": "invalid_form_data"}
        return _scrub_value(data)

    if "multipart/form-data" in content_type:
        return {
            "form_keys": sorted(list(request.POST.keys())[:100]),
            "file_keys": sorted(list(request.FILES.keys())[:50]),
        }

    return {"omitted": "unsupported_content_type"}


def _store_request_body_snapshot(request) -> None:
    method = str(getattr(request, "method", "")).upper()
    if method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return
    try:
        raw_body = request.body or b""
    except Exception:
        raw_body = b""
    if not isinstance(raw_body, bytes):
        return
    request._admin_audit_body_snapshot = raw_body[:8192]


def _extract_query_params_summary(request) -> dict:
    query_params: dict[str, Any] = {}
    for key, values in request.GET.lists():
        clean_key = str(key or "").strip()[:128]
        if not clean_key:
            continue
        query_params[clean_key] = _scrub_value(values[:20])
    return query_params


def _build_sanitized_query_string(query_params: dict[str, Any]) -> str:
    if not query_params:
        return ""
    try:
        return json.dumps(query_params, ensure_ascii=False)[:2000]
    except Exception:
        return "<invalid_query_params>"


def _is_admin_actor(user) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if bool(getattr(user, "is_superuser", False)):
        return True

    if bool(getattr(user, "is_staff", False)):
        return True

    try:
        user_roles = getattr(user, "user_roles", None)
        if user_roles is None:
            return False
        return user_roles.filter(role__code="ADMIN", role__is_active=True).exists()
    except Exception:
        return False


def _is_admin_origin(request) -> bool:
    origin = str(request.headers.get("Origin", "") or "").strip()
    referer = str(request.headers.get("Referer", "") or "").strip()
    candidates = [origin, referer]

    for candidate in candidates:
        if not candidate:
            continue
        parsed = urlparse(candidate)
        host = str(parsed.netloc or "").lower()
        if not host:
            continue
        if host.endswith(":3002"):
            return True
        if host.startswith("admin."):
            return True
        if "admin-" in host and "trycloudflare.com" in host:
            return True

    return False


def _resolve_channel(*, request, is_admin_origin: bool) -> str:
    provided = str(request.headers.get("X-MRQ-CHANNEL", "") or "").strip().lower()
    if provided:
        return provided[:32]

    if is_admin_origin:
        return "web-admin"

    user = getattr(request, "user", None)
    if user and getattr(user, "is_authenticated", False):
        if bool(getattr(user, "is_staff", False)) or bool(
            getattr(user, "is_superuser", False)
        ):
            return "admin-authenticated"

    return "unknown"


def _resolve_action(path: str) -> tuple[str, str]:
    normalized = str(path or "").strip("/")
    parts = normalized.split("/")
    if len(parts) < 3:
        return "system", normalized[:128]

    action_group = parts[2]
    resource = "/".join(parts[3:6]) if len(parts) > 3 else parts[2]
    return action_group[:64], resource[:128]


def _extract_client_ip(request) -> str | None:
    forwarded_for = str(request.META.get("HTTP_X_FORWARDED_FOR", "") or "").strip()
    if forwarded_for:
        first = forwarded_for.split(",", maxsplit=1)[0].strip()
        if first:
            return first

    remote_addr = str(request.META.get("REMOTE_ADDR", "") or "").strip()
    if remote_addr:
        return remote_addr

    return None
