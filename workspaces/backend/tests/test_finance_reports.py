from datetime import date, datetime
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.catalog.models import (
    Dish,
    DishIngredient,
    Ingredient,
    IngredientUnit,
    MenuDay,
    MenuItem,
)
from apps.finance.models import (
    Account,
    AccountType,
    APBill,
    APBillStatus,
    CashDirection,
    CashMovement,
)
from apps.finance.reports import (
    get_cashflow,
    get_dish_cost,
    get_dre,
    get_ingredient_weighted_cost,
    get_kpis,
    get_menu_item_cost,
)
from apps.orders.models import Order, OrderItem, OrderStatus
from apps.procurement.models import Purchase, PurchaseItem


def _create_purchase_with_item(
    *,
    ingredient: Ingredient,
    purchase_date: date,
    qty: Decimal,
    unit_price: Decimal,
    tax_amount: Decimal = Decimal("0.00"),
    supplier_name: str = "Fornecedor Rel",
) -> PurchaseItem:
    purchase = Purchase.objects.create(
        supplier_name=supplier_name,
        purchase_date=purchase_date,
        total_amount=qty * unit_price + tax_amount,
    )
    return PurchaseItem.objects.create(
        purchase=purchase,
        ingredient=ingredient,
        qty=qty,
        unit=ingredient.unit,
        unit_price=unit_price,
        tax_amount=tax_amount,
    )


def _setup_dre_scenario() -> tuple[date, date]:
    period_from = date(2026, 4, 1)
    period_to = date(2026, 4, 30)
    delivery_date = date(2026, 4, 20)

    ingredient = Ingredient.objects.create(
        name="Ingrediente DRE",
        unit=IngredientUnit.KILOGRAM,
    )
    dish = Dish.objects.create(name="Prato DRE", yield_portions=2)
    DishIngredient.objects.create(
        dish=dish,
        ingredient=ingredient,
        quantity=Decimal("2.000"),
        unit=IngredientUnit.KILOGRAM,
    )

    menu_day = MenuDay.objects.create(menu_date=delivery_date, title="Cardapio DRE")
    menu_item = MenuItem.objects.create(
        menu_day=menu_day,
        dish=dish,
        sale_price=Decimal("10.00"),
        is_active=True,
    )

    _create_purchase_with_item(
        ingredient=ingredient,
        purchase_date=date(2026, 4, 10),
        qty=Decimal("10.000"),
        unit_price=Decimal("6.00"),
    )

    order = Order.objects.create(
        customer=None,
        delivery_date=delivery_date,
        status=OrderStatus.DELIVERED,
        total_amount=Decimal("30.00"),
    )
    OrderItem.objects.create(
        order=order,
        menu_item=menu_item,
        qty=3,
        unit_price=Decimal("10.00"),
    )

    expense_account = Account.objects.create(
        name="Conta Despesa DRE",
        type=AccountType.EXPENSE,
    )
    APBill.objects.create(
        supplier_name="Fornecedor DRE",
        account=expense_account,
        amount=Decimal("5.00"),
        due_date=date(2026, 4, 22),
        status=APBillStatus.PAID,
        paid_at=timezone.make_aware(datetime(2026, 4, 22, 10, 0)),
    )

    return period_from, period_to


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


@pytest.mark.django_db
def test_get_ingredient_weighted_cost_com_duas_compras():
    ingredient = Ingredient.objects.create(
        name="Ingrediente Custo Medio",
        unit=IngredientUnit.KILOGRAM,
    )

    _create_purchase_with_item(
        ingredient=ingredient,
        purchase_date=date(2026, 4, 1),
        qty=Decimal("2.000"),
        unit_price=Decimal("10.00"),
        tax_amount=Decimal("2.00"),
    )
    _create_purchase_with_item(
        ingredient=ingredient,
        purchase_date=date(2026, 4, 2),
        qty=Decimal("3.000"),
        unit_price=Decimal("8.00"),
        tax_amount=Decimal("1.00"),
    )

    weighted_cost = get_ingredient_weighted_cost(ingredient.id)

    assert weighted_cost == Decimal("9.40")


@pytest.mark.django_db
def test_get_dish_cost_com_receita_simples():
    ingredient = Ingredient.objects.create(
        name="Ingrediente Prato Custo",
        unit=IngredientUnit.KILOGRAM,
    )
    dish = Dish.objects.create(name="Prato Custo", yield_portions=2)
    DishIngredient.objects.create(
        dish=dish,
        ingredient=ingredient,
        quantity=Decimal("1.500"),
        unit=IngredientUnit.KILOGRAM,
    )
    menu_day = MenuDay.objects.create(
        menu_date=date(2026, 4, 5), title="Cardapio Custo"
    )
    menu_item = MenuItem.objects.create(
        menu_day=menu_day,
        dish=dish,
        sale_price=Decimal("20.00"),
        is_active=True,
    )

    _create_purchase_with_item(
        ingredient=ingredient,
        purchase_date=date(2026, 4, 4),
        qty=Decimal("5.000"),
        unit_price=Decimal("8.00"),
    )

    dish_cost = get_dish_cost(dish.id, on_date=date(2026, 4, 5))
    menu_item_cost = get_menu_item_cost(menu_item.id)

    assert dish_cost == Decimal("12.00")
    assert menu_item_cost == Decimal("6.00")


@pytest.mark.django_db
def test_get_dre_retorna_valores_consistentes_em_cenario_controlado():
    period_from, period_to = _setup_dre_scenario()

    dre = get_dre(from_date=period_from, to_date=period_to)

    assert dre["receita_total"] == Decimal("30.00")
    assert dre["despesas_total"] == Decimal("5.00")
    assert dre["cmv_estimado"] == Decimal("18.00")
    assert dre["lucro_bruto"] == Decimal("12.00")
    assert dre["resultado"] == Decimal("7.00")


@pytest.mark.django_db
def test_get_kpis_retorna_pedidos_ticket_e_margem_media():
    period_from, period_to = _setup_dre_scenario()

    kpis = get_kpis(from_date=period_from, to_date=period_to)

    assert kpis["pedidos"] == 1
    assert kpis["receita_total"] == Decimal("30.00")
    assert kpis["despesas_total"] == Decimal("5.00")
    assert kpis["cmv_estimado"] == Decimal("18.00")
    assert kpis["lucro_bruto"] == Decimal("12.00")
    assert kpis["ticket_medio"] == Decimal("30.00")
    assert kpis["margem_media"] == Decimal("40.00")
