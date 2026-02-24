from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db.models import Sum

from apps.catalog.models import Dish, MenuItem
from apps.orders.models import Order, OrderItem, OrderStatus
from apps.procurement.models import PurchaseItem

from .models import APBill, APBillStatus, CashDirection, CashMovement

MONEY_DECIMAL_PLACES = Decimal("0.01")
ZERO_MONEY = Decimal("0.00")


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_DECIMAL_PLACES, rounding=ROUND_HALF_UP)


def _ensure_unit_compatible(
    *,
    context: str,
    expected_unit: str,
    received_unit: str,
) -> None:
    if expected_unit != received_unit:
        raise ValidationError(
            f"Unidade incompativel em {context}: esperado "
            f"'{expected_unit}', recebido '{received_unit}'. "
            "TODO: implementar conversao de unidades."
        )


def _sum_or_zero(value: Decimal | None) -> Decimal:
    if value is None:
        return ZERO_MONEY
    return _quantize_money(value)


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


def get_ingredient_weighted_cost(
    ingredient_id: int,
    until_date: date | None = None,
) -> Decimal:
    purchase_items_qs = PurchaseItem.objects.filter(
        ingredient_id=ingredient_id,
    ).select_related("ingredient", "purchase")

    if until_date is not None:
        purchase_items_qs = purchase_items_qs.filter(
            purchase__purchase_date__lte=until_date
        )

    purchase_items = list(purchase_items_qs)
    if not purchase_items:
        return ZERO_MONEY

    total_cost = Decimal("0")
    total_qty = Decimal("0")

    for item in purchase_items:
        _ensure_unit_compatible(
            context=f"compra do ingrediente '{item.ingredient.name}'",
            expected_unit=item.ingredient.unit,
            received_unit=item.unit,
        )

        tax_amount = item.tax_amount or Decimal("0")
        total_cost += item.qty * item.unit_price + tax_amount
        total_qty += item.qty

    if total_qty <= 0:
        return ZERO_MONEY

    return _quantize_money(total_cost / total_qty)


def get_dish_cost(dish_id: int, on_date: date | None = None) -> Decimal:
    dish = (
        Dish.objects.prefetch_related("dish_ingredients__ingredient")
        .filter(pk=dish_id)
        .first()
    )
    if dish is None:
        raise ValidationError("Prato nao encontrado para calculo de custo.")

    total_cost = Decimal("0")

    for dish_ingredient in dish.dish_ingredients.all():
        recipe_unit = dish_ingredient.unit or dish_ingredient.ingredient.unit
        _ensure_unit_compatible(
            context=(
                f"receita do prato '{dish.name}' com "
                f"ingrediente '{dish_ingredient.ingredient.name}'"
            ),
            expected_unit=dish_ingredient.ingredient.unit,
            received_unit=recipe_unit,
        )

        ingredient_cost = get_ingredient_weighted_cost(
            dish_ingredient.ingredient_id,
            until_date=on_date,
        )
        total_cost += dish_ingredient.quantity * ingredient_cost

    return _quantize_money(total_cost)


def get_menu_item_cost(menu_item_id: int) -> Decimal:
    menu_item = (
        MenuItem.objects.select_related("dish", "menu_day")
        .filter(pk=menu_item_id)
        .first()
    )
    if menu_item is None:
        raise ValidationError("Menu item nao encontrado para calculo de custo.")

    if menu_item.dish.yield_portions <= 0:
        raise ValidationError(
            "yield_portions do prato deve ser maior que zero para calcular custo."
        )

    dish_cost = get_dish_cost(
        menu_item.dish_id,
        on_date=menu_item.menu_day.menu_date,
    )

    return _quantize_money(dish_cost / Decimal(menu_item.dish.yield_portions))


def _get_revenue_total(from_date: date, to_date: date) -> Decimal:
    # MVP: receita por pedidos entregues no periodo.
    value = Order.objects.filter(
        status=OrderStatus.DELIVERED,
        delivery_date__gte=from_date,
        delivery_date__lte=to_date,
    ).aggregate(total=Sum("total_amount"))["total"]
    return _sum_or_zero(value)


def _get_paid_expenses_total(from_date: date, to_date: date) -> Decimal:
    value = APBill.objects.filter(
        status=APBillStatus.PAID,
        paid_at__date__gte=from_date,
        paid_at__date__lte=to_date,
    ).aggregate(total=Sum("amount"))["total"]
    return _sum_or_zero(value)


def _get_estimated_cmv(from_date: date, to_date: date) -> Decimal:
    order_items = OrderItem.objects.filter(
        order__status=OrderStatus.DELIVERED,
        order__delivery_date__gte=from_date,
        order__delivery_date__lte=to_date,
    )

    total_cmv = Decimal("0")
    menu_item_cost_cache: dict[int, Decimal] = {}

    for order_item in order_items:
        if order_item.menu_item_id not in menu_item_cost_cache:
            menu_item_cost_cache[order_item.menu_item_id] = get_menu_item_cost(
                order_item.menu_item_id
            )

        total_cmv += (
            Decimal(order_item.qty) * menu_item_cost_cache[order_item.menu_item_id]
        )

    return _quantize_money(total_cmv)


def get_dre(from_date: date, to_date: date) -> dict[str, Decimal]:
    receita_total = _get_revenue_total(from_date, to_date)
    despesas_total = _get_paid_expenses_total(from_date, to_date)
    cmv_estimado = _get_estimated_cmv(from_date, to_date)
    lucro_bruto = _quantize_money(receita_total - cmv_estimado)
    resultado = _quantize_money(lucro_bruto - despesas_total)

    return {
        "receita_total": receita_total,
        "despesas_total": despesas_total,
        "cmv_estimado": cmv_estimado,
        "lucro_bruto": lucro_bruto,
        "resultado": resultado,
    }


def get_kpis(from_date: date, to_date: date) -> dict[str, int | Decimal]:
    pedidos = Order.objects.filter(
        status=OrderStatus.DELIVERED,
        delivery_date__gte=from_date,
        delivery_date__lte=to_date,
    ).count()

    receita_total = _get_revenue_total(from_date, to_date)
    despesas_total = _get_paid_expenses_total(from_date, to_date)
    cmv_estimado = _get_estimated_cmv(from_date, to_date)
    lucro_bruto = _quantize_money(receita_total - cmv_estimado)

    if pedidos > 0:
        ticket_medio = _quantize_money(receita_total / Decimal(pedidos))
    else:
        ticket_medio = ZERO_MONEY

    if receita_total > 0:
        margem_media = _quantize_money((lucro_bruto / receita_total) * Decimal("100"))
    else:
        margem_media = ZERO_MONEY

    return {
        "pedidos": pedidos,
        "receita_total": receita_total,
        "despesas_total": despesas_total,
        "cmv_estimado": cmv_estimado,
        "lucro_bruto": lucro_bruto,
        "ticket_medio": ticket_medio,
        "margem_media": margem_media,
    }
