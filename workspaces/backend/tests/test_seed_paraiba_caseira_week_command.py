from __future__ import annotations

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

import pytest
from django.core.management import call_command

from apps.catalog.models import (
    Dish,
    DishIngredient,
    Ingredient,
    IngredientUnit,
    MenuDay,
    MenuItem,
)
from apps.orders.models import Order, OrderItem
from apps.procurement.models import Purchase, PurchaseRequest
from apps.production.models import ProductionBatch


def _week_invoice_number(start_date: date) -> str:
    return f"PB-CASEIRA-{start_date.strftime('%Y%m%d')}"


def _build_expected_sale_price(base_cost: Decimal) -> Decimal:
    operational = (base_cost * Decimal("1.18")) + Decimal("1.80")
    sale_price = operational * Decimal("1.75")
    if sale_price < Decimal("18.00"):
        sale_price = Decimal("18.00")
    return sale_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@pytest.mark.django_db(transaction=True)
def test_seed_paraiba_caseira_week_command_e_idempotente(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    start_date = date(2026, 3, 9)

    call_command("seed_paraiba_caseira_week", start_date=start_date.isoformat())

    first_counts = {
        "ingredients": Ingredient.objects.count(),
        "dishes": Dish.objects.count(),
        "menu_days": MenuDay.objects.count(),
        "purchase_requests": PurchaseRequest.objects.count(),
        "purchases": Purchase.objects.count(),
        "production_batches": ProductionBatch.objects.count(),
    }

    call_command("seed_paraiba_caseira_week", start_date=start_date.isoformat())

    second_counts = {
        "ingredients": Ingredient.objects.count(),
        "dishes": Dish.objects.count(),
        "menu_days": MenuDay.objects.count(),
        "purchase_requests": PurchaseRequest.objects.count(),
        "purchases": Purchase.objects.count(),
        "production_batches": ProductionBatch.objects.count(),
    }

    assert second_counts == first_counts
    assert (
        MenuDay.objects.filter(
            menu_date__range=(start_date, start_date + timedelta(days=6))
        ).count()
        >= 7
    )
    assert (
        Purchase.objects.filter(invoice_number=_week_invoice_number(start_date)).count()
        == 1
    )


@pytest.mark.django_db(transaction=True)
def test_seed_paraiba_caseira_week_command_preserva_menu_com_pedido_existente(
    settings,
    tmp_path,
):
    settings.MEDIA_ROOT = tmp_path / "media"
    start_date = date(2026, 3, 9)

    ingredient = Ingredient.objects.create(
        name="insumo legado",
        unit=IngredientUnit.KILOGRAM,
    )
    dish = Dish.objects.create(name="prato legado", yield_portions=1)
    DishIngredient.objects.create(
        dish=dish,
        ingredient=ingredient,
        quantity=Decimal("0.200"),
        unit=IngredientUnit.KILOGRAM,
    )

    menu_day = MenuDay.objects.create(
        menu_date=start_date,
        title="Menu legado com pedido",
    )
    menu_item = MenuItem.objects.create(
        menu_day=menu_day,
        dish=dish,
        sale_price=Decimal("22.00"),
        available_qty=20,
        is_active=True,
    )
    order = Order.objects.create(
        delivery_date=start_date,
        total_amount=Decimal("22.00"),
    )
    order_item = OrderItem.objects.create(
        order=order,
        menu_item=menu_item,
        qty=1,
        unit_price=Decimal("22.00"),
    )

    call_command("seed_paraiba_caseira_week", start_date=start_date.isoformat())

    menu_day.refresh_from_db()
    menu_item.refresh_from_db()
    order_item.refresh_from_db()

    assert menu_day.title == "Menu legado com pedido"
    assert menu_day.items.count() == 1
    assert menu_day.items.first().id == menu_item.id
    assert order_item.menu_item_id == menu_item.id


@pytest.mark.django_db(transaction=True)
def test_seed_paraiba_caseira_week_command_aplica_formula_de_preco(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    start_date = date(2026, 3, 9)

    call_command("seed_paraiba_caseira_week", start_date=start_date.isoformat())

    purchase = Purchase.objects.prefetch_related("items__ingredient").get(
        invoice_number=_week_invoice_number(start_date)
    )
    menu_day = MenuDay.objects.get(menu_date=start_date)
    menu_item = menu_day.items.select_related("dish").get()

    ingredient_cost_map = {
        item.ingredient_id: Decimal(item.unit_price) for item in purchase.items.all()
    }

    dish_cost = Decimal("0")
    for composition in menu_item.dish.dish_ingredients.select_related(
        "ingredient"
    ).all():
        ingredient_cost = ingredient_cost_map.get(
            composition.ingredient_id,
            Decimal("0"),
        )
        dish_cost += Decimal(composition.quantity) * ingredient_cost

    dish_cost = dish_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    expected_sale_price = _build_expected_sale_price(dish_cost)

    assert menu_item.sale_price == expected_sale_price
