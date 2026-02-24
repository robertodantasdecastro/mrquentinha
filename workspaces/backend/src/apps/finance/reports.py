from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from .models import CashDirection, CashMovement

MONEY_DECIMAL_PLACES = Decimal("0.01")


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_DECIMAL_PLACES, rounding=ROUND_HALF_UP)


def get_cashflow(from_date: date, to_date: date) -> list[dict]:
    movements = CashMovement.objects.filter(
        movement_date__date__gte=from_date,
        movement_date__date__lte=to_date,
    ).order_by("movement_date", "id")

    daily_totals: dict[date, dict[str, Decimal]] = {}

    for movement in movements:
        movement_day = movement.movement_date.date()
        totals = daily_totals.setdefault(
            movement_day,
            {
                "total_in": Decimal("0.00"),
                "total_out": Decimal("0.00"),
            },
        )

        if movement.direction == CashDirection.IN:
            totals["total_in"] += movement.amount
        elif movement.direction == CashDirection.OUT:
            totals["total_out"] += movement.amount

    running_balance = Decimal("0.00")
    items: list[dict] = []

    for movement_day in sorted(daily_totals):
        totals = daily_totals[movement_day]
        total_in = _quantize_money(totals["total_in"])
        total_out = _quantize_money(totals["total_out"])
        net = _quantize_money(total_in - total_out)
        running_balance = _quantize_money(running_balance + net)

        items.append(
            {
                "date": movement_day,
                "total_in": total_in,
                "total_out": total_out,
                "net": net,
                "running_balance": running_balance,
            }
        )

    return items
