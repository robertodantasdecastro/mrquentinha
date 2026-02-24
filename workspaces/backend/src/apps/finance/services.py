from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

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

MONEY_DECIMAL_PLACES = Decimal("0.01")
DEFAULT_REVENUE_ACCOUNT_NAME = "Vendas"
DEFAULT_EXPENSE_ACCOUNT_NAME = "Insumos"
DEFAULT_CASH_ACCOUNT_NAME = "Caixa/Banco"

DEFAULT_FINANCE_ACCOUNTS = [
    {"name": DEFAULT_REVENUE_ACCOUNT_NAME, "type": AccountType.REVENUE},
    {"name": DEFAULT_EXPENSE_ACCOUNT_NAME, "type": AccountType.EXPENSE},
    {"name": "Operacional", "type": AccountType.EXPENSE},
    {"name": DEFAULT_CASH_ACCOUNT_NAME, "type": AccountType.ASSET},
    {"name": "Fornecedores", "type": AccountType.LIABILITY},
]


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_DECIMAL_PLACES, rounding=ROUND_HALF_UP)


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


def ensure_default_accounts() -> list[Account]:
    return create_default_chart_of_accounts()


def _resolve_default_account(*, name: str, account_type: str) -> Account:
    ensure_default_accounts()
    account, _ = Account.objects.get_or_create(
        name=name,
        defaults={"type": account_type, "is_active": True},
    )

    updated_fields: list[str] = []
    if account.type != account_type:
        account.type = account_type
        updated_fields.append("type")
    if not account.is_active:
        account.is_active = True
        updated_fields.append("is_active")

    if updated_fields:
        updated_fields.append("updated_at")
        account.save(update_fields=updated_fields)

    return account


def _resolve_default_revenue_account() -> Account:
    return _resolve_default_account(
        name=DEFAULT_REVENUE_ACCOUNT_NAME,
        account_type=AccountType.REVENUE,
    )


def _resolve_default_expense_account() -> Account:
    return _resolve_default_account(
        name=DEFAULT_EXPENSE_ACCOUNT_NAME,
        account_type=AccountType.EXPENSE,
    )


def _resolve_default_cash_account() -> Account:
    return _resolve_default_account(
        name=DEFAULT_CASH_ACCOUNT_NAME,
        account_type=AccountType.ASSET,
    )


def _ensure_positive_amount(amount: Decimal) -> None:
    if amount <= 0:
        raise ValidationError("Valor deve ser maior que zero.")


def _resolve_datetime(value: datetime | None) -> datetime:
    return value or timezone.now()


def _calculate_purchase_total_from_items(purchase: Purchase) -> Decimal:
    total = Decimal("0")
    for item in purchase.items.all():
        tax_amount = item.tax_amount or Decimal("0")
        total += item.qty * item.unit_price + tax_amount
    return _quantize_money(total)


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
        purchase = (
            Purchase.objects.select_for_update()
            .prefetch_related("items")
            .get(pk=purchase_id)
        )
    except Purchase.DoesNotExist as exc:
        raise ValidationError("Compra nao encontrada para gerar AP.") from exc

    existing = get_ap_by_reference("PURCHASE", purchase.id)
    if existing is not None:
        return existing

    account_obj = account or _resolve_default_expense_account()

    if amount is not None:
        amount_value = _quantize_money(amount)
    elif purchase.total_amount and purchase.total_amount > 0:
        amount_value = _quantize_money(purchase.total_amount)
    else:
        amount_value = _calculate_purchase_total_from_items(purchase)

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
    amount_value = (
        _quantize_money(amount)
        if amount is not None
        else _quantize_money(order.total_amount)
    )
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
        if receivable.status != ARReceivableStatus.RECEIVED:
            receivable.status = ARReceivableStatus.RECEIVED
            if receivable.received_at is None:
                receivable.received_at = existing_movement.movement_date
            receivable.save(update_fields=["status", "received_at", "updated_at"])
        return existing_movement

    if receivable.status == ARReceivableStatus.RECEIVED:
        raise ValidationError(
            "AR ja esta RECEIVED. Nenhum novo movimento de caixa foi criado."
        )

    cash_account = account or _resolve_default_cash_account()
    if cash_account.type != AccountType.ASSET:
        raise ValidationError("Conta de caixa deve ser do tipo ASSET.")

    movement = CashMovement.objects.create(
        movement_date=_resolve_datetime(movement_date),
        direction=CashDirection.IN,
        amount=receivable.amount,
        account=cash_account,
        note=note or f"Entrada de caixa referente ao AR {receivable.id}",
        reference_type="AR",
        reference_id=receivable.id,
    )

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
