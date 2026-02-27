import string
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.customer_services import assert_customer_checkout_eligible
from apps.accounts.services import SystemRole, user_has_any_role
from apps.finance.services import create_ar_from_order, record_cash_in_from_ar

from .models import (
    Order,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentIntent,
    PaymentIntentStatus,
    PaymentMethod,
    PaymentStatus,
    PaymentWebhookEvent,
)
from .payment_providers import get_payment_provider
from .selectors import get_menu_day_for_delivery

MONEY_DECIMAL_PLACES = Decimal("0.01")
IDEMPOTENCY_ALLOWED_CHARS = set(string.ascii_letters + string.digits + "-_.:")
IDEMPOTENCY_KEY_MAX_LENGTH = 128
ONLINE_INTENT_METHODS = {PaymentMethod.PIX, PaymentMethod.CARD, PaymentMethod.VR}
WEBHOOK_EVENT_ALLOWED_CHARS = IDEMPOTENCY_ALLOWED_CHARS
WEBHOOK_EVENT_ID_MAX_LENGTH = 120
INTENT_ACTIVE_STATUSES = {
    PaymentIntentStatus.REQUIRES_ACTION,
    PaymentIntentStatus.PROCESSING,
}
INTENT_FAILURE_STATUSES = {
    PaymentIntentStatus.FAILED,
    PaymentIntentStatus.CANCELED,
    PaymentIntentStatus.EXPIRED,
}


class PaymentIntentConflictError(Exception):
    pass


def normalize_idempotency_key(idempotency_key: str) -> str:
    normalized_key = (idempotency_key or "").strip()

    if not normalized_key:
        raise ValidationError("Header Idempotency-Key obrigatorio.")

    if len(normalized_key) > IDEMPOTENCY_KEY_MAX_LENGTH:
        raise ValidationError(
            "Idempotency-Key deve ter no maximo "
            f"{IDEMPOTENCY_KEY_MAX_LENGTH} caracteres."
        )

    if any(char not in IDEMPOTENCY_ALLOWED_CHARS for char in normalized_key):
        raise ValidationError(
            "Idempotency-Key contem caracteres invalidos. Use apenas letras, "
            "numeros e -_.:."
        )

    return normalized_key


def normalize_webhook_event_id(event_id: str) -> str:
    normalized_event_id = (event_id or "").strip()

    if not normalized_event_id:
        raise ValidationError("Campo event_id obrigatorio.")

    if len(normalized_event_id) > WEBHOOK_EVENT_ID_MAX_LENGTH:
        raise ValidationError(
            "event_id deve ter no maximo " f"{WEBHOOK_EVENT_ID_MAX_LENGTH} caracteres."
        )

    if any(char not in WEBHOOK_EVENT_ALLOWED_CHARS for char in normalized_event_id):
        raise ValidationError(
            "event_id contem caracteres invalidos. Use apenas letras, "
            "numeros e -_.:."
        )

    return normalized_event_id


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_DECIMAL_PLACES, rounding=ROUND_HALF_UP)


def _assert_unique_items_payload(items_payload: list[dict]) -> None:
    menu_item_ids = [item["menu_item"].id for item in items_payload]
    if len(menu_item_ids) != len(set(menu_item_ids)):
        raise ValidationError("Item de cardapio duplicado no pedido.")


def _assert_items_payload(items_payload: list[dict]) -> None:
    if not items_payload:
        raise ValidationError("Pedido deve possuir ao menos um item.")

    _assert_unique_items_payload(items_payload)

    for item in items_payload:
        if item["qty"] <= 0:
            raise ValidationError("Quantidade do item deve ser maior que zero.")


def _validate_menu_items_for_delivery_date(
    *,
    delivery_date: date,
    items_payload: list[dict],
) -> None:
    menu_day = get_menu_day_for_delivery(delivery_date)
    if menu_day is None:
        raise ValidationError("Nao existe cardapio para a data de entrega informada.")

    for item in items_payload:
        menu_item = item["menu_item"]
        if menu_item.menu_day_id != menu_day.id:
            raise ValidationError(
                "Menu item informado nao pertence ao cardapio da data de entrega."
            )
        if not menu_item.is_active:
            raise ValidationError("Menu item inativo nao pode ser usado no pedido.")


def _calculate_total_amount(items_payload: list[dict]) -> Decimal:
    total_amount = Decimal("0")
    for item in items_payload:
        total_amount += Decimal(item["qty"]) * item["menu_item"].sale_price
    return _quantize_money(total_amount)


def _sync_order_receivable(*, order_id: int) -> None:
    create_ar_from_order(order_id)


def _sync_paid_payment_cash_flow(*, payment: Payment) -> None:
    ar_receivable = create_ar_from_order(payment.order_id)
    record_cash_in_from_ar(ar_receivable.id)


def has_global_order_access(user) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return True

    return user_has_any_role(
        user,
        [
            SystemRole.ADMIN,
            SystemRole.FINANCEIRO,
            SystemRole.COZINHA,
            SystemRole.COMPRAS,
            SystemRole.ESTOQUE,
        ],
    )


@transaction.atomic
def create_order(
    *,
    customer,
    delivery_date: date,
    items_payload: list[dict],
    payment_method: str = PaymentMethod.PIX,
) -> Order:
    assert_customer_checkout_eligible(customer=customer)
    _assert_items_payload(items_payload)
    _validate_menu_items_for_delivery_date(
        delivery_date=delivery_date,
        items_payload=items_payload,
    )

    method_choices = {choice for choice, _ in PaymentMethod.choices}
    if payment_method not in method_choices:
        raise ValidationError("Metodo de pagamento invalido.")

    total_amount = _calculate_total_amount(items_payload)

    order = Order.objects.create(
        customer=customer,
        delivery_date=delivery_date,
        status=OrderStatus.CREATED,
        total_amount=total_amount,
    )

    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                menu_item=item["menu_item"],
                qty=item["qty"],
                unit_price=item["menu_item"].sale_price,
            )
            for item in items_payload
        ]
    )

    Payment.objects.create(
        order=order,
        method=payment_method,
        status=PaymentStatus.PENDING,
        amount=total_amount,
    )

    _sync_order_receivable(order_id=order.id)

    return (
        Order.objects.select_related("customer")
        .prefetch_related("items__menu_item__dish", "payments")
        .get(pk=order.pk)
    )


def _is_valid_order_transition(current_status: str, new_status: str) -> bool:
    if current_status == new_status:
        return True

    allowed_transitions = {
        OrderStatus.CREATED: {OrderStatus.CONFIRMED, OrderStatus.CANCELED},
        OrderStatus.CONFIRMED: {OrderStatus.IN_PROGRESS, OrderStatus.CANCELED},
        OrderStatus.IN_PROGRESS: {
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.CANCELED,
        },
        OrderStatus.OUT_FOR_DELIVERY: {
            OrderStatus.DELIVERED,
            OrderStatus.CANCELED,
        },
        OrderStatus.DELIVERED: {OrderStatus.RECEIVED},
        OrderStatus.RECEIVED: set(),
        OrderStatus.CANCELED: set(),
    }
    return new_status in allowed_transitions[current_status]


@transaction.atomic
def update_order_status(*, order_id: int, new_status: str, actor_user=None) -> Order:
    try:
        order = Order.objects.select_for_update().get(pk=order_id)
    except Order.DoesNotExist as exc:
        raise ValidationError("Pedido nao encontrado.") from exc

    actor_is_global = actor_user is not None and has_global_order_access(actor_user)
    actor_is_owner = actor_user is not None and order.customer_id == getattr(
        actor_user, "id", None
    )
    if actor_user is not None and not actor_is_global and not actor_is_owner:
        raise ValidationError("Pedido nao encontrado.")

    status_choices = {choice for choice, _ in OrderStatus.choices}
    if new_status not in status_choices:
        raise ValidationError("Status de pedido invalido.")

    if not _is_valid_order_transition(order.status, new_status):
        raise ValidationError(f"Transicao invalida: {order.status} -> {new_status}.")

    if actor_user is not None and not actor_is_global:
        if not actor_is_owner:
            raise ValidationError("Pedido nao encontrado.")

        is_customer_receipt_confirmation = (
            order.status == OrderStatus.DELIVERED and new_status == OrderStatus.RECEIVED
        )
        is_customer_cancel = new_status == OrderStatus.CANCELED and order.status in {
            OrderStatus.CREATED,
            OrderStatus.CONFIRMED,
        }
        if not (is_customer_receipt_confirmation or is_customer_cancel):
            raise ValidationError(
                "Cliente so pode cancelar pedido no inicio ou confirmar recebimento."
            )

    if order.status != new_status:
        order.status = new_status
        order.save(update_fields=["status", "updated_at"])

    return order


@transaction.atomic
def update_payment_status(
    *, payment_id: int, update_data: dict, actor_user=None
) -> Payment:
    try:
        payment = (
            Payment.objects.select_for_update()
            .select_related("order")
            .get(pk=payment_id)
        )
    except Payment.DoesNotExist as exc:
        raise ValidationError("Pagamento nao encontrado.") from exc

    if actor_user is not None and not has_global_order_access(actor_user):
        if payment.order.customer_id != getattr(actor_user, "id", None):
            raise ValidationError("Pagamento nao encontrado.")

    status_choices = {choice for choice, _ in PaymentStatus.choices}
    if "status" in update_data:
        new_status = update_data["status"]
        if new_status not in status_choices:
            raise ValidationError("Status de pagamento invalido.")
        payment.status = new_status

        if (
            new_status == PaymentStatus.PAID
            and "paid_at" not in update_data
            and payment.paid_at is None
        ):
            payment.paid_at = timezone.now()

    if "provider_ref" in update_data:
        payment.provider_ref = update_data["provider_ref"]

    if "paid_at" in update_data:
        payment.paid_at = update_data["paid_at"]

    payment.save()

    if payment.status == PaymentStatus.PAID:
        PaymentIntent.objects.filter(
            payment=payment,
            status__in=INTENT_ACTIVE_STATUSES,
        ).update(
            status=PaymentIntentStatus.SUCCEEDED,
            updated_at=timezone.now(),
        )
        _sync_paid_payment_cash_flow(payment=payment)

    return payment


@transaction.atomic
def create_or_get_payment_intent(
    *,
    payment_id: int,
    idempotency_key: str,
    source_channel: str | None = None,
    actor_user=None,
) -> tuple[PaymentIntent, bool]:
    normalized_key = normalize_idempotency_key(idempotency_key)

    try:
        payment = (
            Payment.objects.select_for_update()
            .select_related("order")
            .get(pk=payment_id)
        )
    except Payment.DoesNotExist as exc:
        raise ValidationError("Pagamento nao encontrado.") from exc

    if actor_user is not None and not has_global_order_access(actor_user):
        if payment.order.customer_id != getattr(actor_user, "id", None):
            raise ValidationError("Pagamento nao encontrado.")

    if payment.method not in ONLINE_INTENT_METHODS:
        raise ValidationError("Metodo de pagamento nao suporta intent online.")

    if payment.status == PaymentStatus.PAID:
        raise PaymentIntentConflictError(
            "Pagamento ja confirmado. Nao e permitido abrir novo intent."
        )

    existing = PaymentIntent.objects.filter(
        payment=payment,
        idempotency_key=normalized_key,
    ).first()
    if existing is not None:
        return existing, False

    conflicting_intent = (
        PaymentIntent.objects.filter(payment=payment, status__in=INTENT_ACTIVE_STATUSES)
        .exclude(idempotency_key=normalized_key)
        .first()
    )
    if conflicting_intent is not None:
        raise PaymentIntentConflictError(
            "Ja existe um intent ativo para este pagamento."
        )

    provider = get_payment_provider(
        payment_method=payment.method,
        channel=source_channel,
    )
    provider_result = provider.create_intent(
        payment=payment,
        idempotency_key=normalized_key,
    )

    intent = PaymentIntent.objects.create(
        payment=payment,
        provider=provider_result.provider,
        status=provider_result.status,
        idempotency_key=normalized_key,
        provider_intent_ref=provider_result.provider_intent_ref,
        client_payload=provider_result.client_payload,
        expires_at=provider_result.expires_at,
    )

    return intent, True


def get_latest_payment_intent(
    *,
    payment_id: int,
    actor_user=None,
) -> PaymentIntent | None:
    try:
        payment = Payment.objects.select_related("order").get(pk=payment_id)
    except Payment.DoesNotExist as exc:
        raise ValidationError("Pagamento nao encontrado.") from exc

    if actor_user is not None and not has_global_order_access(actor_user):
        if payment.order.customer_id != getattr(actor_user, "id", None):
            raise ValidationError("Pagamento nao encontrado.")

    return payment.intents.order_by("-created_at", "-id").first()


def _resolve_webhook_payment_status(intent_status: str) -> str | None:
    if intent_status == PaymentIntentStatus.SUCCEEDED:
        return PaymentStatus.PAID

    if intent_status in INTENT_FAILURE_STATUSES:
        return PaymentStatus.FAILED

    return None


@transaction.atomic
def process_payment_webhook(
    *,
    provider: str | None,
    event_id: str,
    provider_intent_ref: str,
    intent_status: str,
    provider_ref: str | None = None,
    paid_at=None,
    raw_payload: dict | None = None,
) -> tuple[PaymentWebhookEvent, bool]:
    normalized_provider = (
        (provider or get_payment_provider().provider_name).strip().lower()
    )
    normalized_event_id = normalize_webhook_event_id(event_id)
    normalized_intent_ref = (provider_intent_ref or "").strip()
    normalized_intent_status = (intent_status or "").strip().upper()

    if not normalized_provider:
        raise ValidationError("Campo provider obrigatorio.")

    if not normalized_intent_ref:
        raise ValidationError("Campo provider_intent_ref obrigatorio.")

    intent_choices = {choice for choice, _ in PaymentIntentStatus.choices}
    if normalized_intent_status not in intent_choices:
        raise ValidationError("Status de intent invalido.")

    (
        webhook_event,
        created,
    ) = PaymentWebhookEvent.objects.select_for_update().get_or_create(
        provider=normalized_provider,
        event_id=normalized_event_id,
        defaults={"payload": raw_payload or {}},
    )
    if not created:
        return webhook_event, False

    intent = (
        PaymentIntent.objects.select_for_update()
        .select_related("payment")
        .filter(
            provider=normalized_provider,
            provider_intent_ref=normalized_intent_ref,
        )
        .order_by("-created_at", "-id")
        .first()
    )
    if intent is None:
        raise ValidationError("Intent de pagamento nao encontrado.")

    if intent.status != normalized_intent_status:
        intent.status = normalized_intent_status
        intent.save(update_fields=["status", "updated_at"])

    payment = intent.payment
    payment_update_data: dict = {}
    resolved_payment_status = _resolve_webhook_payment_status(normalized_intent_status)

    if resolved_payment_status is not None:
        payment_update_data["status"] = resolved_payment_status

    if provider_ref is not None:
        payment_update_data["provider_ref"] = provider_ref

    if resolved_payment_status == PaymentStatus.PAID and paid_at is not None:
        payment_update_data["paid_at"] = paid_at

    if payment_update_data:
        payment = update_payment_status(
            payment_id=payment.id,
            update_data=payment_update_data,
        )

    webhook_event.payment = payment
    webhook_event.intent = intent
    webhook_event.intent_status = intent.status
    webhook_event.payment_status = payment.status
    webhook_event.payload = raw_payload or {}
    webhook_event.processed_at = timezone.now()
    webhook_event.save(
        update_fields=[
            "payment",
            "intent",
            "intent_status",
            "payment_status",
            "payload",
            "processed_at",
            "updated_at",
        ]
    )

    return webhook_event, True
