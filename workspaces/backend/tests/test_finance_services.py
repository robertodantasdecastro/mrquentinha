from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.finance.models import (
    Account,
    AccountType,
    APBill,
    APBillStatus,
    ARReceivable,
    ARReceivableStatus,
    BankStatement,
    CashDirection,
    CashMovement,
    LedgerEntry,
    LedgerEntryType,
    StatementLine,
)
from apps.finance.services import (
    create_ap_from_purchase,
    create_ar_from_order,
    reconcile_cash_movement,
    record_cash_in_from_ar,
    record_cash_out_from_ap,
    unreconcile_cash_movement,
)
from apps.orders.models import Order, OrderStatus
from apps.procurement.models import Purchase


@pytest.mark.django_db(transaction=True)
def test_account_impede_duplicidade_por_nome():
    Account.objects.create(name="Vendas", type=AccountType.REVENUE)

    with pytest.raises(IntegrityError):
        Account.objects.create(name="Vendas", type=AccountType.REVENUE)


@pytest.mark.django_db
def test_create_ap_from_purchase_idempotente_por_referencia():
    purchase = Purchase.objects.create(
        supplier_name="Fornecedor AP",
        purchase_date=date(2026, 3, 10),
        total_amount=Decimal("145.90"),
    )

    ap_first = create_ap_from_purchase(purchase.id)
    ap_second = create_ap_from_purchase(purchase.id)

    assert ap_first.id == ap_second.id
    assert APBill.objects.count() == 1
    assert ap_first.reference_type == "PURCHASE"
    assert ap_first.reference_id == purchase.id


@pytest.mark.django_db
def test_create_ar_from_order_idempotente_por_referencia():
    order = Order.objects.create(
        customer=None,
        delivery_date=date(2026, 3, 12),
        status=OrderStatus.CONFIRMED,
        total_amount=Decimal("89.70"),
    )

    ar_first = create_ar_from_order(order.id)
    ar_second = create_ar_from_order(order.id)

    assert ar_first.id == ar_second.id
    assert ARReceivable.objects.count() == 1
    assert ar_first.reference_type == "ORDER"
    assert ar_first.reference_id == order.id


@pytest.mark.django_db
def test_record_cash_in_e_out_cria_movimentos_e_atualiza_status():
    revenue_account = Account.objects.create(name="Receita", type=AccountType.REVENUE)
    expense_account = Account.objects.create(name="Despesa", type=AccountType.EXPENSE)

    receivable = ARReceivable.objects.create(
        customer=None,
        account=revenue_account,
        amount=Decimal("120.00"),
        due_date=date(2026, 3, 15),
        status=ARReceivableStatus.OPEN,
    )
    bill = APBill.objects.create(
        supplier_name="Fornecedor Caixa",
        account=expense_account,
        amount=Decimal("55.50"),
        due_date=date(2026, 3, 16),
        status=APBillStatus.OPEN,
    )

    cash_in_first = record_cash_in_from_ar(receivable.id)
    cash_in_second = record_cash_in_from_ar(receivable.id)
    cash_out_first = record_cash_out_from_ap(bill.id)
    cash_out_second = record_cash_out_from_ap(bill.id)

    assert cash_in_first.id == cash_in_second.id
    assert cash_in_first.direction == CashDirection.IN
    assert cash_in_first.amount == Decimal("120.00")

    assert cash_out_first.id == cash_out_second.id
    assert cash_out_first.direction == CashDirection.OUT
    assert cash_out_first.amount == Decimal("55.50")

    receivable.refresh_from_db()
    bill.refresh_from_db()

    assert receivable.status == ARReceivableStatus.RECEIVED
    assert receivable.received_at is not None
    assert bill.status == APBillStatus.PAID
    assert bill.paid_at is not None

    assert CashMovement.objects.count() == 2


@pytest.mark.django_db
def test_record_cash_in_from_ar_cria_ledger_e_nao_duplica():
    revenue_account = Account.objects.create(
        name="Conta Receita Ledger AR",
        type=AccountType.REVENUE,
    )
    cash_account = Account.objects.create(
        name="Conta Caixa Ledger AR",
        type=AccountType.ASSET,
    )
    receivable = ARReceivable.objects.create(
        customer=None,
        account=revenue_account,
        amount=Decimal("180.00"),
        due_date=date(2026, 3, 20),
        status=ARReceivableStatus.OPEN,
    )

    movement_first = record_cash_in_from_ar(receivable.id, account=cash_account)
    movement_second = record_cash_in_from_ar(receivable.id, account=cash_account)

    assert movement_first.id == movement_second.id

    entries = LedgerEntry.objects.filter(
        reference_type="AR",
        reference_id=receivable.id,
    )
    assert entries.count() == 2
    assert {entry.entry_type for entry in entries} == {
        LedgerEntryType.AR_RECEIVED,
        LedgerEntryType.CASH_IN,
    }

    ar_received = entries.get(entry_type=LedgerEntryType.AR_RECEIVED)
    cash_in = entries.get(entry_type=LedgerEntryType.CASH_IN)

    assert ar_received.amount == Decimal("180.00")
    assert ar_received.debit_account == cash_account
    assert ar_received.credit_account == revenue_account

    assert cash_in.amount == Decimal("180.00")
    assert cash_in.debit_account == cash_account
    assert cash_in.credit_account == revenue_account


@pytest.mark.django_db
def test_record_cash_out_from_ap_cria_ledger_e_nao_duplica():
    expense_account = Account.objects.create(
        name="Conta Despesa Ledger AP",
        type=AccountType.EXPENSE,
    )
    cash_account = Account.objects.create(
        name="Conta Caixa Ledger AP",
        type=AccountType.ASSET,
    )
    bill = APBill.objects.create(
        supplier_name="Fornecedor Ledger AP",
        account=expense_account,
        amount=Decimal("90.00"),
        due_date=date(2026, 3, 21),
        status=APBillStatus.OPEN,
    )

    movement_first = record_cash_out_from_ap(bill.id, account=cash_account)
    movement_second = record_cash_out_from_ap(bill.id, account=cash_account)

    assert movement_first.id == movement_second.id

    entries = LedgerEntry.objects.filter(
        reference_type="AP",
        reference_id=bill.id,
    )
    assert entries.count() == 2
    assert {entry.entry_type for entry in entries} == {
        LedgerEntryType.AP_PAID,
        LedgerEntryType.CASH_OUT,
    }

    ap_paid = entries.get(entry_type=LedgerEntryType.AP_PAID)
    cash_out = entries.get(entry_type=LedgerEntryType.CASH_OUT)

    assert ap_paid.amount == Decimal("90.00")
    assert ap_paid.debit_account == expense_account
    assert ap_paid.credit_account == cash_account

    assert cash_out.amount == Decimal("90.00")
    assert cash_out.debit_account == expense_account
    assert cash_out.credit_account == cash_account


@pytest.mark.django_db
def test_reconcile_cash_movement_marca_conciliado_e_vincula_linha():
    cash_account = Account.objects.create(
        name="Conta Caixa Conciliacao",
        type=AccountType.ASSET,
    )
    movement = CashMovement.objects.create(
        direction=CashDirection.IN,
        amount=Decimal("50.00"),
        account=cash_account,
        reference_type="AR",
        reference_id=300,
    )
    statement = BankStatement.objects.create(
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        source="Banco Teste",
    )
    line = StatementLine.objects.create(
        statement=statement,
        line_date=date(2026, 4, 10),
        description="Recebimento PIX",
        amount=Decimal("50.00"),
    )

    reconciled = reconcile_cash_movement(movement.id, line.id)

    assert reconciled.is_reconciled is True
    assert reconciled.statement_line_id == line.id


@pytest.mark.django_db
def test_reconcile_cash_movement_mesma_linha_e_idempotente():
    cash_account = Account.objects.create(
        name="Conta Caixa Conciliacao Idempotente",
        type=AccountType.ASSET,
    )
    movement = CashMovement.objects.create(
        direction=CashDirection.IN,
        amount=Decimal("70.00"),
        account=cash_account,
        reference_type="AR",
        reference_id=301,
    )
    statement = BankStatement.objects.create(
        period_start=date(2026, 5, 1),
        period_end=date(2026, 5, 31),
    )
    line = StatementLine.objects.create(
        statement=statement,
        line_date=date(2026, 5, 5),
        description="Credito",
        amount=Decimal("70.00"),
    )

    first = reconcile_cash_movement(movement.id, line.id)
    second = reconcile_cash_movement(movement.id, line.id)

    assert first.id == second.id
    assert second.is_reconciled is True
    assert second.statement_line_id == line.id


@pytest.mark.django_db
def test_reconcile_cash_movement_com_outra_linha_falha():
    cash_account = Account.objects.create(
        name="Conta Caixa Conciliacao Erro",
        type=AccountType.ASSET,
    )
    movement = CashMovement.objects.create(
        direction=CashDirection.OUT,
        amount=Decimal("45.00"),
        account=cash_account,
        reference_type="AP",
        reference_id=500,
    )
    statement = BankStatement.objects.create(
        period_start=date(2026, 6, 1),
        period_end=date(2026, 6, 30),
    )
    first_line = StatementLine.objects.create(
        statement=statement,
        line_date=date(2026, 6, 3),
        description="Debito fornecedor",
        amount=Decimal("-45.00"),
    )
    other_line = StatementLine.objects.create(
        statement=statement,
        line_date=date(2026, 6, 4),
        description="Outra linha",
        amount=Decimal("-45.00"),
    )

    reconcile_cash_movement(movement.id, first_line.id)

    with pytest.raises(ValidationError):
        reconcile_cash_movement(movement.id, other_line.id)


@pytest.mark.django_db
def test_unreconcile_cash_movement_remove_vinculo():
    cash_account = Account.objects.create(
        name="Conta Caixa Desconciliacao",
        type=AccountType.ASSET,
    )
    movement = CashMovement.objects.create(
        direction=CashDirection.IN,
        amount=Decimal("80.00"),
        account=cash_account,
        reference_type="AR",
        reference_id=701,
    )
    statement = BankStatement.objects.create(
        period_start=date(2026, 7, 1),
        period_end=date(2026, 7, 31),
    )
    line = StatementLine.objects.create(
        statement=statement,
        line_date=date(2026, 7, 10),
        description="Receita julho",
        amount=Decimal("80.00"),
    )

    reconcile_cash_movement(movement.id, line.id)
    unreconciled = unreconcile_cash_movement(movement.id)

    assert unreconciled.is_reconciled is False
    assert unreconciled.statement_line is None
