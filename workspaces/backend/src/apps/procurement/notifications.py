from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

from apps.accounts.services import SystemRole

from .models import PurchaseRequest


def _build_alert_message(purchase_request: PurchaseRequest) -> str:
    lines = [
        "Nova requisicao de compra gerada automaticamente.",
        f"Requisicao: PR #{purchase_request.id}",
        f"Status: {purchase_request.status}",
    ]
    if purchase_request.note:
        lines.append(f"Observacao: {purchase_request.note}")

    lines.append("Itens:")
    for item in purchase_request.items.select_related("ingredient").all():
        lines.append(f"- {item.ingredient.name}: {item.required_qty} {item.unit}")

    return "\n".join(lines)


def _collect_procurement_recipients() -> list[str]:
    User = get_user_model()
    queryset = (
        User.objects.filter(is_active=True, email__isnull=False)
        .exclude(email="")
        .filter(
            user_roles__role__code__in=[SystemRole.ADMIN, SystemRole.COMPRAS],
            user_roles__role__is_active=True,
        )
        .distinct()
    )
    return [user.email.strip() for user in queryset if user.email.strip()]


def _send_whatsapp_alert(*, message: str) -> dict:
    webhook_url = getattr(settings, "PROCUREMENT_WHATSAPP_WEBHOOK_URL", "").strip()
    if not webhook_url:
        return {
            "configured": False,
            "sent": False,
            "error": None,
        }

    token = getattr(settings, "PROCUREMENT_WHATSAPP_WEBHOOK_TOKEN", "").strip()
    headers = {
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(
        webhook_url,
        method="POST",
        headers=headers,
        data=json.dumps({"message": message}).encode("utf-8"),
    )

    try:
        with urlopen(request, timeout=10):
            return {"configured": True, "sent": True, "error": None}
    except (TimeoutError, URLError) as exc:
        return {"configured": True, "sent": False, "error": str(exc)}


def notify_purchase_request_created(purchase_request: PurchaseRequest) -> dict:
    message = _build_alert_message(purchase_request)
    recipients = _collect_procurement_recipients()
    from_email = (
        getattr(settings, "PROCUREMENT_ALERT_FROM_EMAIL", "").strip()
        or getattr(settings, "DEFAULT_FROM_EMAIL", "").strip()
        or "noreply@mrquentinha.local"
    )

    sent_email_count = 0
    if recipients:
        sent_email_count = send_mail(
            subject=f"[Mr Quentinha] Nova requisicao PR #{purchase_request.id}",
            message=message,
            from_email=from_email,
            recipient_list=recipients,
            fail_silently=True,
        )

    whatsapp_status = _send_whatsapp_alert(message=message)

    return {
        "email": {
            "configured": bool(recipients),
            "sent_count": sent_email_count,
            "recipients": recipients,
        },
        "whatsapp": whatsapp_status,
    }
