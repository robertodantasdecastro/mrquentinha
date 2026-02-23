from datetime import date, datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.orders.models import Order
from apps.procurement.models import Purchase

from .models import (
    Account,
    AccountType,
    APBill,
    APBillStatus,
    ARReceivable,
    ARReceivableStatus,
    CashDirection,
    CashMovement,
)
from .selectors import (
    get_ap_by_reference,
    get_ar_by_reference,
    get_cash_by_reference,
)

DEFAULT_FINANCE_ACCOUNTS = [
    {"name": "Vendas", "type": AccountType.REVENUE},
    {"name": "Insumos", "type": AccountType.EXPENSE},
    {"name": "Operacional", "type": AccountType.EXPENSE},
    {"name": "Caixa", "type": AccountType.ASSET},
    {"name": "Fornecedores", "type": AccountType.LIABILITY},
]


@transaction.atomic
def create_default_chart_of_accounts() -> list[Account]:
    created_or_updated: list[Account] = []

    for account_data in DEFAULT_FINANCE_ACCOUNTS:
        account, _ = Account.objects.get_or_create(
            name=account_data["name"],
            defaults={
                "type": account_data["type"],
                "is_active": True,
            },
        )

        updated_fields: list[str] = []
        if account.type != account_data["type"]:
            account.type = account_data["type"]
            updated_fields.append("type")
        if not account.is_active:
            account.is_active = True
            updated_fields.append("is_active")

        if updated_fields:
            updated_fields.append("updated_at")
            account.save(update_fields=updated_fields)

        created_or_updated.append(account)

    return created_or_updated


def _resolve_default_revenue_account() -> Account:
    account, _ = Account.objects.get_or_create(
        name="Vendas",
        defaults={"type": AccountType.REVENUE, "is_active": True},
    )
    return account


def _resolve_default_expense_account() -> Account:
    account, _ = Account.objects.get_or_create(
        name="Insumos",
        defaults={"type": AccountType.EXPENSE, "is_active": True},
    )
    return account


def _ensure_positive_amount(amount: Decimal) -> None:
    if amount <= 0:
        raise ValidationError("Valor deve ser maior que zero.")


def _resolve_datetime(value: datetime | None) -> datetime:
    return value or timezone.now()


@transaction.atomic
def create_ap_from_purchase(
    purchase_id: int,
    *,
    account: Account | None = None,
    amount: Decimal | None = None,
    due_date: date | None = None,
    supplier_name: str | None = None,
) -> APBill:
    try:
        purchase = Purchase.objects.select_for_update().get(pk=purchase_id)
    except Purchase.DoesNotExist as exc:
        raise ValidationError("Compra nao encontrada para gerar AP.") from exc

    existing = get_ap_by_reference("PURCHASE", purchase.id)
    if existing is not None:
        return existing

    account_obj = account or _resolve_default_expense_account()
    amount_value = amount if amount is not None else purchase.total_amount
    due_date_value = due_date if due_date is not None else purchase.purchase_date
    supplier_name_value = (
        supplier_name if supplier_name is not None else purchase.supplier_name
    )

    _ensure_positive_amount(amount_value)

    return APBill.objects.create(
        supplier_name=supplier_name_value,
        account=account_obj,
        amount=amount_value,
        due_date=due_date_value,
        status=APBillStatus.OPEN,
        reference_type="PURCHASE",
        reference_id=purchase.id,
    )


@transaction.atomic
def create_ar_from_order(
    order_id: int,
    *,
    account: Account | None = None,
    amount: Decimal | None = None,
    due_date: date | None = None,
) -> ARReceivable:
    try:
        order = Order.objects.select_for_update().get(pk=order_id)
    except Order.DoesNotExist as exc:
        raise ValidationError("Pedido nao encontrado para gerar AR.") from exc

    existing = get_ar_by_reference("ORDER", order.id)
    if existing is not None:
        return existing

    account_obj = account or _resolve_default_revenue_account()
    amount_value = amount if amount is not None else order.total_amount
    due_date_value = due_date if due_date is not None else order.delivery_date

    _ensure_positive_amount(amount_value)

    return ARReceivable.objects.create(
        customer=order.customer,
        account=account_obj,
        amount=amount_value,
        due_date=due_date_value,
        status=ARReceivableStatus.OPEN,
        reference_type="ORDER",
        reference_id=order.id,
    )


@transaction.atomic
def record_cash_in_from_ar(
    ar_id: int,
    *,
    account: Account | None = None,
    movement_date: datetime | None = None,
    note: str | None = None,
) -> CashMovement:
    try:
        receivable = (
            ARReceivable.objects.select_for_update()
            .select_related("account")
            .get(pk=ar_id)
        )
    except ARReceivable.DoesNotExist as exc:
        raise ValidationError(
            "AR nao encontrado para registrar entrada de caixa."
        ) from exc

    existing_movement = get_cash_by_reference(
        direction=CashDirection.IN,
        reference_type="AR",
        reference_id=receivable.id,
    )
    if existing_movement is not None:
        return existing_movement

    movement = CashMovement.objects.create(
        movement_date=_resolve_datetime(movement_date),
        direction=CashDirection.IN,
        amount=receivable.amount,
        account=account or receivable.account,
        note=note or f"Entrada de caixa referente ao AR {receivable.id}",
        reference_type="AR",
        reference_id=receivable.id,
    )

    if receivable.status != ARReceivableStatus.RECEIVED:
        receivable.status = ARReceivableStatus.RECEIVED
        receivable.received_at = movement.movement_date
        receivable.save(update_fields=["status", "received_at", "updated_at"])

    return movement


@transaction.atomic
def record_cash_out_from_ap(
    ap_id: int,
    *,
    account: Account | None = None,
    movement_date: datetime | None = None,
    note: str | None = None,
) -> CashMovement:
    try:
        bill = (
            APBill.objects.select_for_update().select_related("account").get(pk=ap_id)
        )
    except APBill.DoesNotExist as exc:
        raise ValidationError(
            "AP nao encontrado para registrar saida de caixa."
        ) from exc

    existing_movement = get_cash_by_reference(
        direction=CashDirection.OUT,
        reference_type="AP",
        reference_id=bill.id,
    )
    if existing_movement is not None:
        return existing_movement

    movement = CashMovement.objects.create(
        movement_date=_resolve_datetime(movement_date),
        direction=CashDirection.OUT,
        amount=bill.amount,
        account=account or bill.account,
        note=note or f"Saida de caixa referente ao AP {bill.id}",
        reference_type="AP",
        reference_id=bill.id,
    )

    if bill.status != APBillStatus.PAID:
        bill.status = APBillStatus.PAID
        bill.paid_at = movement.movement_date
        bill.save(update_fields=["status", "paid_at", "updated_at"])

    return movement
