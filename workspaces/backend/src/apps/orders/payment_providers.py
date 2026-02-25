from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Payment, PaymentIntentStatus, PaymentMethod


@dataclass(slots=True)
class ProviderIntentResult:
    provider: str
    status: str
    provider_intent_ref: str
    client_payload: dict
    expires_at: datetime | None


class BasePaymentProvider:
    provider_name = "base"

    def create_intent(
        self,
        *,
        payment: Payment,
        idempotency_key: str,
    ) -> ProviderIntentResult:
        raise NotImplementedError


class MockPaymentProvider(BasePaymentProvider):
    provider_name = "mock"

    def create_intent(
        self,
        *,
        payment: Payment,
        idempotency_key: str,
    ) -> ProviderIntentResult:
        provider_ref = f"mock-intent-{uuid4().hex[:20]}"
        expires_at = timezone.now() + timedelta(
            minutes=getattr(settings, "PAYMENTS_INTENT_TTL_MINUTES", 15)
        )

        payload = {
            "method": payment.method,
            "amount": str(payment.amount),
            "currency": "BRL",
            "provider": self.provider_name,
            "idempotency_key": idempotency_key,
        }

        if payment.method == PaymentMethod.PIX:
            payload.update(
                {
                    "pix": {
                        "copy_paste_code": f"{provider_ref}-pix-copy-paste",
                        "qr_code": f"{provider_ref}-pix-qr",
                    }
                }
            )
        elif payment.method == PaymentMethod.CARD:
            payload.update(
                {
                    "card": {
                        "checkout_token": f"{provider_ref}-card-token",
                        "requires_redirect": False,
                    }
                }
            )
        elif payment.method == PaymentMethod.VR:
            payload.update(
                {
                    "vr": {
                        "authorization_token": f"{provider_ref}-vr-token",
                        "network": "mock-vr",
                    }
                }
            )

        return ProviderIntentResult(
            provider=self.provider_name,
            status=PaymentIntentStatus.REQUIRES_ACTION,
            provider_intent_ref=provider_ref,
            client_payload=payload,
            expires_at=expires_at,
        )


def get_payment_provider(provider_name: str | None = None) -> BasePaymentProvider:
    normalized_name = provider_name or getattr(
        settings,
        "PAYMENTS_PROVIDER_DEFAULT",
        MockPaymentProvider.provider_name,
    )
    normalized_name = normalized_name.strip().lower()

    if normalized_name == MockPaymentProvider.provider_name:
        return MockPaymentProvider()

    raise ValidationError(f"Provider de pagamento invalido: {normalized_name}.")
