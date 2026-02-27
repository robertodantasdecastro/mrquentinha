from __future__ import annotations

import secrets
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import CustomerGovernanceProfile, CustomerLgpdRequest


def ensure_customer_governance_profile(*, user) -> CustomerGovernanceProfile:
    governance, _created = CustomerGovernanceProfile.objects.get_or_create(user=user)
    return governance


def _generate_lgpd_protocol_code() -> str:
    now = timezone.now()
    return f"LGPD-{now.strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(2).upper()}"


@transaction.atomic
def create_lgpd_request(
    *,
    customer,
    request_type: str,
    channel: str,
    requested_by_name: str = "",
    requested_by_email: str = "",
    notes: str = "",
    request_payload: dict | None = None,
) -> CustomerLgpdRequest:
    requested_at = timezone.now()
    due_at = (requested_at + timedelta(days=15)).date()

    return CustomerLgpdRequest.objects.create(
        customer=customer,
        protocol_code=_generate_lgpd_protocol_code(),
        request_type=request_type,
        status=CustomerLgpdRequest.RequestStatus.OPEN,
        channel=channel,
        requested_by_name=str(requested_by_name or "").strip(),
        requested_by_email=str(requested_by_email or "").strip(),
        requested_at=requested_at,
        due_at=due_at,
        notes=str(notes or "").strip(),
        request_payload=request_payload or {},
    )


@transaction.atomic
def apply_customer_account_status(
    *,
    customer,
    account_status: str,
    reason: str,
    actor,
) -> CustomerGovernanceProfile:
    governance = ensure_customer_governance_profile(user=customer)
    governance.account_status = account_status
    governance.account_status_reason = str(reason or "").strip()

    if account_status == CustomerGovernanceProfile.AccountStatus.ACTIVE:
        customer.is_active = True
        governance.checkout_blocked = False
        governance.checkout_block_reason = ""
    elif account_status in {
        CustomerGovernanceProfile.AccountStatus.SUSPENDED,
        CustomerGovernanceProfile.AccountStatus.BLOCKED,
    }:
        customer.is_active = False
        governance.checkout_blocked = True
        governance.checkout_block_reason = (
            str(reason or "").strip() or "Conta com restricao administrativa."
        )

    governance.reviewed_by = (
        actor if getattr(actor, "is_authenticated", False) else None
    )
    governance.reviewed_at = timezone.now()

    customer.save(update_fields=["is_active"])
    governance.save(
        update_fields=[
            "account_status",
            "account_status_reason",
            "checkout_blocked",
            "checkout_block_reason",
            "reviewed_by",
            "reviewed_at",
            "updated_at",
        ]
    )
    return governance


@transaction.atomic
def apply_customer_consents(
    *,
    customer,
    accepted_terms: bool | None,
    accepted_privacy_policy: bool | None,
    marketing_opt_in: bool | None,
) -> CustomerGovernanceProfile:
    governance = ensure_customer_governance_profile(user=customer)
    now = timezone.now()
    update_fields: list[str] = ["updated_at"]

    if accepted_terms is True and governance.terms_accepted_at is None:
        governance.terms_accepted_at = now
        update_fields.append("terms_accepted_at")

    if (
        accepted_privacy_policy is True
        and governance.privacy_policy_accepted_at is None
    ):
        governance.privacy_policy_accepted_at = now
        update_fields.append("privacy_policy_accepted_at")

    if marketing_opt_in is True:
        governance.marketing_opt_in_at = now
        update_fields.append("marketing_opt_in_at")
    elif marketing_opt_in is False:
        governance.marketing_opt_out_at = now
        update_fields.append("marketing_opt_out_at")

    governance.save(update_fields=list(set(update_fields)))
    return governance


def assert_customer_checkout_eligible(*, customer) -> None:
    if customer is None:
        raise ValidationError("Pedido sem cliente autenticado nao e permitido.")

    governance = ensure_customer_governance_profile(user=customer)

    if governance.account_status in {
        CustomerGovernanceProfile.AccountStatus.SUSPENDED,
        CustomerGovernanceProfile.AccountStatus.BLOCKED,
    }:
        reason = governance.account_status_reason or "Conta suspensa para pedidos."
        raise ValidationError(f"Conta sem permissao para checkout: {reason}")

    if governance.checkout_blocked:
        reason = governance.checkout_block_reason or "Checkout bloqueado pela operacao."
        raise ValidationError(f"Checkout bloqueado para este cliente: {reason}")
