from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from urllib import error as urllib_error
from urllib import request as urllib_request
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Payment, PaymentIntentStatus, PaymentMethod
from .provider_config import (
    build_provider_webhook_url,
    get_provider_settings,
    resolve_provider_for_method,
)


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

    @staticmethod
    def _to_brl_float(amount: Decimal) -> float:
        return float(amount.quantize(Decimal("0.01")))

    @staticmethod
    def _resolve_customer_email(payment: Payment) -> str:
        customer = getattr(payment.order, "customer", None)
        if customer and getattr(customer, "email", ""):
            return str(customer.email).strip()
        return f"cliente+pedido{payment.order_id}@mrquentinha.local"

    @staticmethod
    def _resolve_customer_name(payment: Payment) -> str:
        customer = getattr(payment.order, "customer", None)
        if customer:
            full_name = (
                f"{getattr(customer, 'first_name', '').strip()} "
                f"{getattr(customer, 'last_name', '').strip()}"
            ).strip()
            if full_name:
                return full_name
            if getattr(customer, "username", "").strip():
                return str(customer.username).strip()
        return f"Cliente Pedido {payment.order_id}"

    @staticmethod
    def _request_json(
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        payload: dict | None = None,
        timeout_seconds: int = 20,
    ) -> dict:
        body: bytes | None = None
        request_headers = headers.copy()
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            request_headers["Content-Type"] = "application/json"

        req = urllib_request.Request(
            url=url,
            data=body,
            headers=request_headers,
            method=method.upper(),
        )

        try:
            with urllib_request.urlopen(req, timeout=timeout_seconds) as response:
                raw_body = response.read().decode("utf-8").strip()
                if not raw_body:
                    return {}
                return json.loads(raw_body)
        except urllib_error.HTTPError as exc:
            detail = exc.read().decode("utf-8").strip() if exc.fp is not None else ""
            message = (
                f"Falha HTTP {exc.code} em integracao de pagamento: "
                f"{detail or exc.reason}"
            )
            raise ValidationError(message) from exc
        except urllib_error.URLError as exc:
            raise ValidationError(
                "Falha de conexao com provider de pagamento."
            ) from exc
        except json.JSONDecodeError as exc:
            raise ValidationError(
                "Resposta invalida do provider de pagamento."
            ) from exc


class MockPaymentProvider(BasePaymentProvider):
    provider_name = "mock"

    def create_intent(
        self,
        *,
        payment: Payment,
        idempotency_key: str,
    ) -> ProviderIntentResult:
        provider_ref = f"mock-intent-{uuid4().hex[:20]}"
        expires_at = timezone.now() + timedelta(minutes=15)

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


class MercadoPagoPaymentProvider(BasePaymentProvider):
    provider_name = "mercadopago"

    def create_intent(
        self,
        *,
        payment: Payment,
        idempotency_key: str,
    ) -> ProviderIntentResult:
        settings = get_provider_settings(self.provider_name)
        access_token = str(settings.get("access_token", "")).strip()
        api_base_url = (
            str(settings.get("api_base_url", "")).strip()
            or "https://api.mercadopago.com"
        ).rstrip("/")
        if not access_token:
            raise ValidationError("Mercado Pago nao configurado (access_token).")

        webhook_url = build_provider_webhook_url(self.provider_name)
        external_reference = f"order-{payment.order_id}-payment-{payment.id}"

        if payment.method == PaymentMethod.PIX:
            payload = {
                "transaction_amount": self._to_brl_float(payment.amount),
                "description": f"Pedido #{payment.order_id}",
                "payment_method_id": "pix",
                "external_reference": external_reference,
                "notification_url": webhook_url,
                "payer": {
                    "email": self._resolve_customer_email(payment),
                },
            }

            response_payload = self._request_json(
                method="POST",
                url=f"{api_base_url}/v1/payments",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "X-Idempotency-Key": idempotency_key,
                },
                payload=payload,
            )
            provider_ref = str(response_payload.get("id", "")).strip()
            if not provider_ref:
                raise ValidationError(
                    "Mercado Pago nao retornou referencia de pagamento."
                )

            transaction_data = response_payload.get("point_of_interaction", {}).get(
                "transaction_data", {}
            )

            return ProviderIntentResult(
                provider=self.provider_name,
                status=map_mercadopago_status_to_intent(
                    str(response_payload.get("status", "pending"))
                ),
                provider_intent_ref=provider_ref,
                client_payload={
                    "provider": self.provider_name,
                    "method": payment.method,
                    "checkout_url": "",
                    "pix": {
                        "copy_paste_code": str(
                            transaction_data.get("qr_code", "")
                        ).strip(),
                        "qr_code_base64": str(
                            transaction_data.get("qr_code_base64", "")
                        ).strip(),
                    },
                },
                expires_at=timezone.now() + timedelta(minutes=15),
            )

        if payment.method == PaymentMethod.CARD:
            preference_payload = {
                "items": [
                    {
                        "id": str(payment.id),
                        "title": f"Pedido #{payment.order_id}",
                        "quantity": 1,
                        "currency_id": "BRL",
                        "unit_price": self._to_brl_float(payment.amount),
                    }
                ],
                "external_reference": external_reference,
                "notification_url": webhook_url,
            }

            response_payload = self._request_json(
                method="POST",
                url=f"{api_base_url}/checkout/preferences",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "X-Idempotency-Key": idempotency_key,
                },
                payload=preference_payload,
            )
            provider_ref = str(response_payload.get("id", "")).strip()
            if not provider_ref:
                raise ValidationError(
                    "Mercado Pago nao retornou referencia de checkout."
                )
            checkout_url = (
                str(response_payload.get("init_point", "")).strip()
                or str(response_payload.get("sandbox_init_point", "")).strip()
            )

            return ProviderIntentResult(
                provider=self.provider_name,
                status=PaymentIntentStatus.REQUIRES_ACTION,
                provider_intent_ref=provider_ref,
                client_payload={
                    "provider": self.provider_name,
                    "method": payment.method,
                    "checkout_url": checkout_url,
                },
                expires_at=timezone.now() + timedelta(minutes=30),
            )

        raise ValidationError("Mercado Pago suporta apenas PIX e CARD nesta versao.")


class AsaasPaymentProvider(BasePaymentProvider):
    provider_name = "asaas"

    def create_intent(
        self,
        *,
        payment: Payment,
        idempotency_key: str,
    ) -> ProviderIntentResult:
        settings = get_provider_settings(self.provider_name)
        api_key = str(settings.get("api_key", "")).strip()
        api_base_url = (
            str(settings.get("api_base_url", "")).strip()
            or "https://sandbox.asaas.com/api/v3"
        ).rstrip("/")
        if not api_key:
            raise ValidationError("Asaas nao configurado (api_key).")

        asaas_customer_id = self._ensure_customer(
            api_base_url=api_base_url,
            api_key=api_key,
            payment=payment,
        )
        billing_type = "PIX" if payment.method == PaymentMethod.PIX else "UNDEFINED"

        create_payload = {
            "customer": asaas_customer_id,
            "billingType": billing_type,
            "value": self._to_brl_float(payment.amount),
            "dueDate": timezone.localdate().isoformat(),
            "description": f"Pedido #{payment.order_id}",
            "externalReference": f"order-{payment.order_id}-payment-{payment.id}",
        }

        payment_payload = self._request_json(
            method="POST",
            url=f"{api_base_url}/payments",
            headers={
                "access_token": api_key,
                "User-Agent": "MrQuentinha/Backend",
                "X-Idempotency-Key": idempotency_key,
            },
            payload=create_payload,
        )

        provider_ref = str(payment_payload.get("id", "")).strip()
        if not provider_ref:
            raise ValidationError("Asaas nao retornou id de pagamento.")

        client_payload: dict = {
            "provider": self.provider_name,
            "method": payment.method,
            "checkout_url": str(payment_payload.get("invoiceUrl", "")).strip(),
        }

        if payment.method == PaymentMethod.PIX:
            pix_payload = self._request_json(
                method="GET",
                url=f"{api_base_url}/payments/{provider_ref}/pixQrCode",
                headers={
                    "access_token": api_key,
                    "User-Agent": "MrQuentinha/Backend",
                },
            )
            client_payload["pix"] = {
                "copy_paste_code": str(pix_payload.get("payload", "")).strip(),
                "qr_code_base64": str(pix_payload.get("encodedImage", "")).strip(),
                "expiration_date": str(pix_payload.get("expirationDate", "")).strip(),
            }

        return ProviderIntentResult(
            provider=self.provider_name,
            status=map_asaas_status_to_intent(str(payment_payload.get("status", ""))),
            provider_intent_ref=provider_ref,
            client_payload=client_payload,
            expires_at=timezone.now() + timedelta(minutes=30),
        )

    def _ensure_customer(
        self,
        *,
        api_base_url: str,
        api_key: str,
        payment: Payment,
    ) -> str:
        email = self._resolve_customer_email(payment)
        list_payload = self._request_json(
            method="GET",
            url=f"{api_base_url}/customers?email={email}",
            headers={
                "access_token": api_key,
                "User-Agent": "MrQuentinha/Backend",
            },
        )
        if isinstance(list_payload.get("data"), list) and list_payload["data"]:
            first_customer = list_payload["data"][0]
            customer_id = str(first_customer.get("id", "")).strip()
            if customer_id:
                return customer_id

        create_payload = {
            "name": self._resolve_customer_name(payment),
            "email": email,
        }
        create_result = self._request_json(
            method="POST",
            url=f"{api_base_url}/customers",
            headers={
                "access_token": api_key,
                "User-Agent": "MrQuentinha/Backend",
            },
            payload=create_payload,
        )
        customer_id = str(create_result.get("id", "")).strip()
        if not customer_id:
            raise ValidationError("Asaas nao retornou id de cliente.")
        return customer_id


class EfiPaymentProvider(BasePaymentProvider):
    provider_name = "efi"

    def create_intent(
        self,
        *,
        payment: Payment,
        idempotency_key: str,
    ) -> ProviderIntentResult:
        settings = get_provider_settings(self.provider_name)
        client_id = str(settings.get("client_id", "")).strip()
        client_secret = str(settings.get("client_secret", "")).strip()
        api_base_url = (
            str(settings.get("api_base_url", "")).strip()
            or "https://cobrancas-h.api.efipay.com.br"
        ).rstrip("/")
        if not client_id or not client_secret:
            raise ValidationError("Efi nao configurado (client_id/client_secret).")

        token = self._fetch_access_token(
            api_base_url=api_base_url,
            client_id=client_id,
            client_secret=client_secret,
        )
        cents_value = int((payment.amount * Decimal("100")).quantize(Decimal("1")))
        payload = {
            "items": [
                {
                    "name": f"Pedido {payment.order_id}",
                    "amount": 1,
                    "value": cents_value,
                }
            ],
            "metadata": {
                "custom_id": f"order-{payment.order_id}-payment-{payment.id}",
                "notification_url": build_provider_webhook_url(self.provider_name),
            },
            "settings": {
                "payment_method": "all",
                "expire_time": 1800,
            },
        }
        response_payload = self._request_json(
            method="POST",
            url=f"{api_base_url}/v1/charge/one-step/link",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Idempotency-Key": idempotency_key,
            },
            payload=payload,
        )

        data = response_payload.get("data", {})
        if not isinstance(data, dict):
            data = {}
        charge_id = (
            str(data.get("charge_id", "")).strip()
            or str(response_payload.get("id", "")).strip()
        )
        if not charge_id:
            charge_id = f"efi-{uuid4().hex[:20]}"

        checkout_url = (
            str(data.get("payment_url", "")).strip()
            or str(data.get("link", "")).strip()
        )

        return ProviderIntentResult(
            provider=self.provider_name,
            status=PaymentIntentStatus.REQUIRES_ACTION,
            provider_intent_ref=charge_id,
            client_payload={
                "provider": self.provider_name,
                "method": payment.method,
                "checkout_url": checkout_url,
            },
            expires_at=timezone.now() + timedelta(minutes=30),
        )

    def _fetch_access_token(
        self,
        *,
        api_base_url: str,
        client_id: str,
        client_secret: str,
    ) -> str:
        basic_token = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode(
            "utf-8"
        )
        token_payload = self._request_json(
            method="POST",
            url=f"{api_base_url}/v1/authorize",
            headers={
                "Authorization": f"Basic {basic_token}",
                "Content-Type": "application/json",
            },
            payload={"grant_type": "client_credentials"},
        )

        token = str(token_payload.get("access_token", "")).strip()
        if not token:
            raise ValidationError("Efi nao retornou access_token.")
        return token


def map_mercadopago_status_to_intent(raw_status: str) -> str:
    normalized = (raw_status or "").strip().lower()
    if normalized in {"approved"}:
        return PaymentIntentStatus.SUCCEEDED
    if normalized in {"rejected", "cancelled", "refunded", "charged_back"}:
        return PaymentIntentStatus.FAILED
    if normalized in {"in_process", "pending", "in_mediation"}:
        return PaymentIntentStatus.PROCESSING
    return PaymentIntentStatus.REQUIRES_ACTION


def map_asaas_status_to_intent(raw_status: str) -> str:
    normalized = (raw_status or "").strip().upper()
    if normalized in {"RECEIVED", "CONFIRMED", "RECEIVED_IN_CASH"}:
        return PaymentIntentStatus.SUCCEEDED
    if normalized in {"OVERDUE", "REFUNDED", "REFUND_REQUESTED", "CHARGEBACK"}:
        return PaymentIntentStatus.FAILED
    if normalized in {"PENDING", "AWAITING_RISK_ANALYSIS"}:
        return PaymentIntentStatus.PROCESSING
    return PaymentIntentStatus.REQUIRES_ACTION


def get_payment_provider(
    *,
    provider_name: str | None = None,
    payment_method: str | None = None,
    channel: str | None = None,
) -> BasePaymentProvider:
    normalized_name = provider_name or resolve_provider_for_method(
        payment_method or PaymentMethod.PIX,
        channel=channel,
    )
    normalized_name = normalized_name.strip().lower()

    provider_map = {
        MockPaymentProvider.provider_name: MockPaymentProvider,
        MercadoPagoPaymentProvider.provider_name: MercadoPagoPaymentProvider,
        EfiPaymentProvider.provider_name: EfiPaymentProvider,
        AsaasPaymentProvider.provider_name: AsaasPaymentProvider,
    }
    provider_cls = provider_map.get(normalized_name)
    if provider_cls is None:
        raise ValidationError(f"Provider de pagamento invalido: {normalized_name}.")

    return provider_cls()


def test_payment_provider_connection(provider_name: str) -> dict:
    normalized_name = (provider_name or "").strip().lower()
    if not normalized_name:
        raise ValidationError("Provider obrigatorio para teste de conexao.")

    if normalized_name == "mock":
        return {
            "provider": "mock",
            "ok": True,
            "detail": "Provider mock sempre disponivel para desenvolvimento.",
        }

    settings = get_provider_settings(normalized_name)
    if normalized_name == MercadoPagoPaymentProvider.provider_name:
        token = str(settings.get("access_token", "")).strip()
        api_base_url = (
            str(settings.get("api_base_url", "")).strip()
            or "https://api.mercadopago.com"
        ).rstrip("/")
        if not token:
            raise ValidationError("Mercado Pago nao configurado (access_token).")
        BasePaymentProvider._request_json(
            method="GET",
            url=f"{api_base_url}/v1/payment_methods",
            headers={"Authorization": f"Bearer {token}"},
        )
        return {
            "provider": normalized_name,
            "ok": True,
            "detail": "Conexao Mercado Pago validada com sucesso.",
        }

    if normalized_name == AsaasPaymentProvider.provider_name:
        api_key = str(settings.get("api_key", "")).strip()
        api_base_url = (
            str(settings.get("api_base_url", "")).strip()
            or "https://sandbox.asaas.com/api/v3"
        ).rstrip("/")
        if not api_key:
            raise ValidationError("Asaas nao configurado (api_key).")
        BasePaymentProvider._request_json(
            method="GET",
            url=f"{api_base_url}/myAccount",
            headers={
                "access_token": api_key,
                "User-Agent": "MrQuentinha/Backend",
            },
        )
        return {
            "provider": normalized_name,
            "ok": True,
            "detail": "Conexao Asaas validada com sucesso.",
        }

    if normalized_name == EfiPaymentProvider.provider_name:
        client_id = str(settings.get("client_id", "")).strip()
        client_secret = str(settings.get("client_secret", "")).strip()
        api_base_url = (
            str(settings.get("api_base_url", "")).strip()
            or "https://cobrancas-h.api.efipay.com.br"
        ).rstrip("/")
        if not client_id or not client_secret:
            raise ValidationError("Efi nao configurado (client_id/client_secret).")
        EfiPaymentProvider()._fetch_access_token(
            api_base_url=api_base_url,
            client_id=client_id,
            client_secret=client_secret,
        )
        return {
            "provider": normalized_name,
            "ok": True,
            "detail": "Conexao Efi validada com sucesso.",
        }

    raise ValidationError(f"Provider de pagamento invalido: {normalized_name}.")


def fetch_mercadopago_payment_details(payment_id: str) -> dict:
    settings = get_provider_settings(MercadoPagoPaymentProvider.provider_name)
    access_token = str(settings.get("access_token", "")).strip()
    api_base_url = (
        str(settings.get("api_base_url", "")).strip() or "https://api.mercadopago.com"
    ).rstrip("/")
    if not access_token:
        raise ValidationError("Mercado Pago nao configurado (access_token).")

    normalized_payment_id = str(payment_id).strip()
    if not normalized_payment_id:
        raise ValidationError("payment_id do Mercado Pago obrigatorio.")

    return BasePaymentProvider._request_json(
        method="GET",
        url=f"{api_base_url}/v1/payments/{normalized_payment_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
