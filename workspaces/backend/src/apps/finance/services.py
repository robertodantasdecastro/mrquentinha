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
    FinancialClose,
    LedgerEntry,
    LedgerEntryType,
    StatementLine,
)
from .reports import get_cashflow, get_dre
from .selectors import (
    get_ap_by_reference,
    get_ar_by_reference,
    get_cash_by_reference,
    get_financial_close_for_date,
)

MONEY_DECIMAL_PLACES = Decimal("0.01")
ZERO_MONEY = Decimal("0.00")
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


def _resolve_datetime(value: datetime | None) -> datetime:
    return value or timezone.now()


def _resolve_date(value: date | datetime | None) -> date | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    return value


def is_date_closed(target_date: date) -> bool:
    return get_financial_close_for_date(target_date) is not None


def _ensure_open_period_for_date(
    *,
    target_date: date | datetime | None,
    entity_label: str,
):
    resolved_date = _resolve_date(target_date)
    if resolved_date is None:
        return

    financial_close = get_financial_close_for_date(resolved_date)
    if financial_close is None:
        return

    raise ValidationError(
        f"Nao e permitido alterar {entity_label} na data "
        f"{resolved_date.isoformat()} porque o periodo "
        f"{financial_close.period_start.isoformat()} a "
        f"{financial_close.period_end.isoformat()} esta fechado."
    )


def ensure_cash_movement_open_for_write(*, movement_date: date | datetime) -> None:
    _ensure_open_period_for_date(
        target_date=movement_date,
        entity_label="movimento de caixa",
    )


def ensure_ap_bill_open_for_write(
    *,
    due_date: date | None,
    status: str,
    paid_at: datetime | None = None,
) -> None:
    _ensure_open_period_for_date(
        target_date=due_date,
        entity_label="conta a pagar",
    )

    if status == APBillStatus.PAID:
        effective_paid_at = paid_at or timezone.now()
        _ensure_open_period_for_date(
            target_date=effective_paid_at,
            entity_label="pagamento de conta a pagar",
        )


def ensure_ar_receivable_open_for_write(
    *,
    due_date: date | None,
    status: str,
    received_at: datetime | None = None,
) -> None:
    _ensure_open_period_for_date(
        target_date=due_date,
        entity_label="conta a receber",
    )

    if status == ARReceivableStatus.RECEIVED:
        effective_received_at = received_at or timezone.now()
        _ensure_open_period_for_date(
            target_date=effective_received_at,
            entity_label="recebimento de conta a receber",
        )


def ensure_ledger_entry_open_for_write(*, entry_date: date | datetime) -> None:
    _ensure_open_period_for_date(
        target_date=entry_date,
        entity_label="lancamento de auditoria",
    )


@transaction.atomic
def close_period(
    *,
    period_start: date,
    period_end: date,
    closed_by=None,
) -> FinancialClose:
    if period_start > period_end:
        raise ValidationError("period_start deve ser menor ou igual a period_end.")

    existing_close = FinancialClose.objects.filter(
        period_start=period_start,
        period_end=period_end,
    ).first()
    if existing_close is not None:
        raise ValidationError("Periodo informado ja foi fechado.")

    dre = get_dre(from_date=period_start, to_date=period_end)
    cashflow_items = get_cashflow(from_date=period_start, to_date=period_end)

    cashflow_net_total = ZERO_MONEY
    cashflow_running_balance = ZERO_MONEY

    for item in cashflow_items:
        cashflow_net_total += item["net"]
        cashflow_running_balance = item["running_balance"]

    cashflow_net_total = _quantize_money(cashflow_net_total)
    cashflow_running_balance = _quantize_money(cashflow_running_balance)

    totals_json = {
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "receita_total": f"{dre['receita_total']:.2f}",
        "despesas_total": f"{dre['despesas_total']:.2f}",
        "cmv_estimado": f"{dre['cmv_estimado']:.2f}",
        "lucro_bruto": f"{dre['lucro_bruto']:.2f}",
        "resultado": f"{dre['resultado']:.2f}",
        "saldo_caixa_periodo": f"{cashflow_net_total:.2f}",
        "saldo_caixa_final": f"{cashflow_running_balance:.2f}",
    }

    return FinancialClose.objects.create(
        period_start=period_start,
        period_end=period_end,
        closed_by=closed_by,
        totals_json=totals_json,
    )


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


@transaction.atomic
def create_cash_movement(
    *,
    direction: str,
    amount: Decimal,
    account: Account,
    movement_date: datetime | None = None,
    note: str | None = None,
    reference_type: str | None = None,
    reference_id: int | None = None,
) -> CashMovement:
    _ensure_positive_amount(amount)

    movement_datetime = _resolve_datetime(movement_date)
    ensure_cash_movement_open_for_write(movement_date=movement_datetime)

    return CashMovement.objects.create(
        movement_date=movement_datetime,
        direction=direction,
        amount=_quantize_money(amount),
        account=account,
        note=note,
        reference_type=reference_type,
        reference_id=reference_id,
    )


def _record_ledger_entry(
    *,
    entry_type: str,
    amount: Decimal,
    debit_account: Account | None,
    credit_account: Account | None,
    reference_type: str,
    reference_id: int,
    note: str | None,
    entry_date: datetime | None = None,
) -> LedgerEntry:
    _ensure_positive_amount(amount)
    resolved_entry_date = _resolve_datetime(entry_date)
    ensure_ledger_entry_open_for_write(entry_date=resolved_entry_date)

    ledger_entry, _ = LedgerEntry.objects.get_or_create(
        reference_type=reference_type,
        reference_id=reference_id,
        entry_type=entry_type,
        defaults={
            "entry_date": resolved_entry_date,
            "amount": _quantize_money(amount),
            "debit_account": debit_account,
            "credit_account": credit_account,
            "note": note,
        },
    )

    return ledger_entry


def _record_cash_in_ledger_entries(
    *,
    receivable: ARReceivable,
    cash_account: Account,
    entry_date: datetime,
) -> None:
    _record_ledger_entry(
        entry_type=LedgerEntryType.AR_RECEIVED,
        amount=receivable.amount,
        debit_account=cash_account,
        credit_account=receivable.account,
        reference_type="AR",
        reference_id=receivable.id,
        note=f"Recebimento do AR {receivable.id}",
        entry_date=entry_date,
    )

    _record_ledger_entry(
        entry_type=LedgerEntryType.CASH_IN,
        amount=receivable.amount,
        debit_account=cash_account,
        credit_account=receivable.account,
        reference_type="AR",
        reference_id=receivable.id,
        note=f"Entrada de caixa do AR {receivable.id}",
        entry_date=entry_date,
    )


def _record_cash_out_ledger_entries(
    *,
    bill: APBill,
    cash_account: Account,
    entry_date: datetime,
) -> None:
    _record_ledger_entry(
        entry_type=LedgerEntryType.AP_PAID,
        amount=bill.amount,
        debit_account=bill.account,
        credit_account=cash_account,
        reference_type="AP",
        reference_id=bill.id,
        note=f"Liquidacao do AP {bill.id}",
        entry_date=entry_date,
    )

    _record_ledger_entry(
        entry_type=LedgerEntryType.CASH_OUT,
        amount=bill.amount,
        debit_account=bill.account,
        credit_account=cash_account,
        reference_type="AP",
        reference_id=bill.id,
        note=f"Saida de caixa do AP {bill.id}",
        entry_date=entry_date,
    )


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
    ensure_ap_bill_open_for_write(
        due_date=due_date_value,
        status=APBillStatus.OPEN,
    )

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
    ensure_ar_receivable_open_for_write(
        due_date=due_date_value,
        status=ARReceivableStatus.OPEN,
    )

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
            ensure_ar_receivable_open_for_write(
                due_date=receivable.due_date,
                status=ARReceivableStatus.RECEIVED,
                received_at=existing_movement.movement_date,
            )
            receivable.status = ARReceivableStatus.RECEIVED
            if receivable.received_at is None:
                receivable.received_at = existing_movement.movement_date
            receivable.save(update_fields=["status", "received_at", "updated_at"])

        _record_cash_in_ledger_entries(
            receivable=receivable,
            cash_account=existing_movement.account,
            entry_date=existing_movement.movement_date,
        )

        return existing_movement

    if receivable.status == ARReceivableStatus.RECEIVED:
        raise ValidationError(
            "AR ja esta RECEIVED. Nenhum novo movimento de caixa foi criado."
        )

    cash_account = account or _resolve_default_cash_account()
    if cash_account.type != AccountType.ASSET:
        raise ValidationError("Conta de caixa deve ser do tipo ASSET.")

    movement_datetime = _resolve_datetime(movement_date)
    ensure_ar_receivable_open_for_write(
        due_date=receivable.due_date,
        status=ARReceivableStatus.RECEIVED,
        received_at=movement_datetime,
    )

    movement = create_cash_movement(
        movement_date=movement_datetime,
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

    _record_cash_in_ledger_entries(
        receivable=receivable,
        cash_account=movement.account,
        entry_date=movement.movement_date,
    )

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
        if bill.status != APBillStatus.PAID:
            ensure_ap_bill_open_for_write(
                due_date=bill.due_date,
                status=APBillStatus.PAID,
                paid_at=existing_movement.movement_date,
            )
            bill.status = APBillStatus.PAID
            if bill.paid_at is None:
                bill.paid_at = existing_movement.movement_date
            bill.save(update_fields=["status", "paid_at", "updated_at"])

        _record_cash_out_ledger_entries(
            bill=bill,
            cash_account=existing_movement.account,
            entry_date=existing_movement.movement_date,
        )

        return existing_movement

    movement_datetime = _resolve_datetime(movement_date)
    ensure_ap_bill_open_for_write(
        due_date=bill.due_date,
        status=APBillStatus.PAID,
        paid_at=movement_datetime,
    )

    movement = create_cash_movement(
        movement_date=movement_datetime,
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

    _record_cash_out_ledger_entries(
        bill=bill,
        cash_account=movement.account,
        entry_date=movement.movement_date,
    )

    return movement


@transaction.atomic
def reconcile_cash_movement(
    cash_movement_id: int,
    statement_line_id: int,
) -> CashMovement:
    try:
        movement = CashMovement.objects.select_for_update().get(pk=cash_movement_id)
    except CashMovement.DoesNotExist as exc:
        raise ValidationError("Movimento de caixa nao encontrado.") from exc

    ensure_cash_movement_open_for_write(movement_date=movement.movement_date)

    try:
        statement_line = StatementLine.objects.get(pk=statement_line_id)
    except StatementLine.DoesNotExist as exc:
        raise ValidationError("Linha de extrato nao encontrada.") from exc

    if movement.is_reconciled:
        if movement.statement_line_id == statement_line.id:
            return movement

        raise ValidationError(
            "Movimento ja conciliado com outra linha de extrato. "
            "Desconcilie antes de reconciliar novamente."
        )

    if (
        movement.statement_line_id is not None
        and movement.statement_line_id != statement_line.id
    ):
        raise ValidationError(
            "Movimento ja possui vinculo com outra linha de extrato. "
            "Desconcilie antes de reconciliar novamente."
        )

    movement.statement_line = statement_line
    movement.is_reconciled = True
    movement.save(update_fields=["statement_line", "is_reconciled"])

    return movement


@transaction.atomic
def unreconcile_cash_movement(cash_movement_id: int) -> CashMovement:
    try:
        movement = CashMovement.objects.select_for_update().get(pk=cash_movement_id)
    except CashMovement.DoesNotExist as exc:
        raise ValidationError("Movimento de caixa nao encontrado.") from exc

    ensure_cash_movement_open_for_write(movement_date=movement.movement_date)

    if not movement.is_reconciled and movement.statement_line_id is None:
        return movement

    movement.statement_line = None
    movement.is_reconciled = False
    movement.save(update_fields=["statement_line", "is_reconciled"])

    return movement
