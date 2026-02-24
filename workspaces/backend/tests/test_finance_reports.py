from datetime import date, datetime
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.finance.models import Account, AccountType, CashDirection, CashMovement
from apps.finance.reports import get_cashflow


@pytest.mark.django_db
def test_get_cashflow_agrega_por_dia_e_calcula_running_balance():
    cash_account = Account.objects.create(
        name="Conta Caixa Rel", type=AccountType.ASSET
    )

    CashMovement.objects.create(
        movement_date=timezone.make_aware(datetime(2026, 3, 1, 9, 0)),
        direction=CashDirection.IN,
        amount=Decimal("100.00"),
        account=cash_account,
        reference_type="AR",
        reference_id=1,
    )
    CashMovement.objects.create(
        movement_date=timezone.make_aware(datetime(2026, 3, 1, 18, 0)),
        direction=CashDirection.OUT,
        amount=Decimal("40.00"),
        account=cash_account,
        reference_type="AP",
        reference_id=1,
    )
    CashMovement.objects.create(
        movement_date=timezone.make_aware(datetime(2026, 3, 2, 10, 0)),
        direction=CashDirection.IN,
        amount=Decimal("60.00"),
        account=cash_account,
        reference_type="AR",
        reference_id=2,
    )
    CashMovement.objects.create(
        movement_date=timezone.make_aware(datetime(2026, 3, 2, 14, 0)),
        direction=CashDirection.OUT,
        amount=Decimal("10.00"),
        account=cash_account,
        reference_type="AP",
        reference_id=2,
    )

    items = get_cashflow(from_date=date(2026, 3, 1), to_date=date(2026, 3, 3))

    assert len(items) == 2

    assert items[0]["date"] == date(2026, 3, 1)
    assert items[0]["total_in"] == Decimal("100.00")
    assert items[0]["total_out"] == Decimal("40.00")
    assert items[0]["net"] == Decimal("60.00")
    assert items[0]["running_balance"] == Decimal("60.00")

    assert items[1]["date"] == date(2026, 3, 2)
    assert items[1]["total_in"] == Decimal("60.00")
    assert items[1]["total_out"] == Decimal("10.00")
    assert items[1]["net"] == Decimal("50.00")
    assert items[1]["running_balance"] == Decimal("110.00")
