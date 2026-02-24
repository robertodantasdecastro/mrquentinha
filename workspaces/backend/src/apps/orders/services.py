from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.services import SystemRole, user_has_any_role
from apps.finance.services import create_ar_from_order, record_cash_in_from_ar

from .models import (
    Order,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from .selectors import get_menu_day_for_delivery

MONEY_DECIMAL_PLACES = Decimal("0.01")


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
def create_order(*, customer, delivery_date: date, items_payload: list[dict]) -> Order:
    _assert_items_payload(items_payload)
    _validate_menu_items_for_delivery_date(
        delivery_date=delivery_date,
        items_payload=items_payload,
    )

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
        method=PaymentMethod.PIX,
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
        OrderStatus.IN_PROGRESS: {OrderStatus.DELIVERED, OrderStatus.CANCELED},
        OrderStatus.DELIVERED: set(),
        OrderStatus.CANCELED: set(),
    }
    return new_status in allowed_transitions[current_status]


@transaction.atomic
def update_order_status(*, order_id: int, new_status: str, actor_user=None) -> Order:
    try:
        order = Order.objects.select_for_update().get(pk=order_id)
    except Order.DoesNotExist as exc:
        raise ValidationError("Pedido nao encontrado.") from exc

    if actor_user is not None and not has_global_order_access(actor_user):
        if order.customer_id != getattr(actor_user, "id", None):
            raise ValidationError("Pedido nao encontrado.")

    status_choices = {choice for choice, _ in OrderStatus.choices}
    if new_status not in status_choices:
        raise ValidationError("Status de pedido invalido.")

    if not _is_valid_order_transition(order.status, new_status):
        raise ValidationError(f"Transicao invalida: {order.status} -> {new_status}.")

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
        _sync_paid_payment_cash_flow(payment=payment)

    return payment
