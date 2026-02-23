from datetime import date
from decimal import Decimal

import pytest
from django.db import IntegrityError

from apps.finance.models import (
    Account,
    AccountType,
    APBill,
    APBillStatus,
    ARReceivable,
    ARReceivableStatus,
    CashDirection,
    CashMovement,
)
from apps.finance.services import (
    create_ap_from_purchase,
    create_ar_from_order,
    record_cash_in_from_ar,
    record_cash_out_from_ap,
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
