from datetime import date
from decimal import Decimal

import pytest

from apps.catalog.models import (
    Dish,
    DishIngredient,
    Ingredient,
    IngredientUnit,
    MenuDay,
    MenuItem,
)
from apps.finance.models import APBill
from apps.finance.services import create_ap_from_purchase
from apps.inventory.models import (
    StockItem,
    StockMovement,
    StockMovementType,
    StockReferenceType,
)
from apps.inventory.selectors import get_stock_by_ingredient
from apps.procurement.models import Purchase, PurchaseItem, PurchaseRequest
from apps.procurement.services import (
    create_purchase_and_apply_stock,
    generate_purchase_request_from_menu,
)


def _create_menu_for_procurement() -> tuple[MenuDay, Ingredient, Ingredient]:
    arroz = Ingredient.objects.create(name="Arroz", unit=IngredientUnit.KILOGRAM)
    feijao = Ingredient.objects.create(name="Feijao", unit=IngredientUnit.KILOGRAM)

    prato_arroz = Dish.objects.create(name="Arroz Branco", yield_portions=10)
    DishIngredient.objects.create(
        dish=prato_arroz,
        ingredient=arroz,
        quantity=Decimal("2.000"),
        unit=IngredientUnit.KILOGRAM,
    )

    prato_feijao = Dish.objects.create(name="Feijao Caseiro", yield_portions=10)
    DishIngredient.objects.create(
        dish=prato_feijao,
        ingredient=feijao,
        quantity=Decimal("1.000"),
        unit=IngredientUnit.KILOGRAM,
    )
    DishIngredient.objects.create(
        dish=prato_feijao,
        ingredient=arroz,
        quantity=Decimal("0.500"),
        unit=IngredientUnit.KILOGRAM,
    )

    menu_day = MenuDay.objects.create(menu_date=date(2026, 3, 2), title="Cardapio")
    MenuItem.objects.create(
        menu_day=menu_day,
        dish=prato_arroz,
        sale_price=Decimal("20.00"),
        is_active=True,
    )
    MenuItem.objects.create(
        menu_day=menu_day,
        dish=prato_feijao,
        sale_price=Decimal("22.00"),
        available_qty=2,
        is_active=True,
    )

    return menu_day, arroz, feijao


@pytest.mark.django_db
def test_create_purchase_and_apply_stock_cria_movimentos_in_e_ap_idempotente():
    ingredient = Ingredient.objects.create(name="azeite", unit=IngredientUnit.LITER)

    purchase = create_purchase_and_apply_stock(
        purchase_data={
            "supplier_name": "Fornecedor Centro",
            "invoice_number": "NF-0001",
            "purchase_date": date(2026, 2, 24),
        },
        items_payload=[
            {
                "ingredient": ingredient,
                "qty": Decimal("3.000"),
                "unit": IngredientUnit.LITER,
                "unit_price": Decimal("10.00"),
                "tax_amount": Decimal("2.50"),
            }
        ],
    )

    assert purchase.total_amount == Decimal("32.50")

    movement = StockMovement.objects.get(
        ingredient=ingredient,
        reference_id=purchase.id,
    )
    assert movement.movement_type == StockMovementType.IN
    assert movement.reference_type == StockReferenceType.PURCHASE

    stock_item = get_stock_by_ingredient(ingredient)
    assert stock_item is not None
    assert stock_item.balance_qty == Decimal("3.000")

    ap_bill = APBill.objects.get(
        reference_type="PURCHASE",
        reference_id=purchase.id,
    )
    assert ap_bill.supplier_name == "Fornecedor Centro"
    assert ap_bill.amount == Decimal("32.50")
    assert ap_bill.due_date == date(2026, 2, 24)

    ap_bill_second = create_ap_from_purchase(purchase.id)
    assert ap_bill_second.id == ap_bill.id
    assert (
        APBill.objects.filter(
            reference_type="PURCHASE",
            reference_id=purchase.id,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_create_ap_from_purchase_calcula_amount_quando_total_amount_zerado():
    ingredient = Ingredient.objects.create(
        name="farinha",
        unit=IngredientUnit.KILOGRAM,
    )
    purchase = Purchase.objects.create(
        supplier_name="Fornecedor Sem Total",
        purchase_date=date(2026, 3, 1),
        total_amount=Decimal("0"),
    )

    PurchaseItem.objects.create(
        purchase=purchase,
        ingredient=ingredient,
        qty=Decimal("2.000"),
        unit=IngredientUnit.KILOGRAM,
        unit_price=Decimal("8.50"),
        tax_amount=Decimal("1.00"),
    )

    ap_bill = create_ap_from_purchase(purchase.id)

    assert ap_bill.amount == Decimal("18.00")
    assert ap_bill.reference_type == "PURCHASE"
    assert ap_bill.reference_id == purchase.id


@pytest.mark.django_db
def test_generate_purchase_request_from_menu_sem_estoque_cria_itens_corretos():
    menu_day, arroz, feijao = _create_menu_for_procurement()

    result = generate_purchase_request_from_menu(menu_day.id)

    assert result["created"] is True
    assert result["purchase_request_id"] is not None
    assert len(result["items"]) == 2

    items_by_ingredient = {item["ingredient_id"]: item for item in result["items"]}
    assert items_by_ingredient[arroz.id]["required_qty"] == Decimal("3.000")
    assert items_by_ingredient[arroz.id]["unit"] == IngredientUnit.KILOGRAM
    assert items_by_ingredient[feijao.id]["required_qty"] == Decimal("2.000")
    assert items_by_ingredient[feijao.id]["unit"] == IngredientUnit.KILOGRAM

    purchase_request = PurchaseRequest.objects.get(pk=result["purchase_request_id"])
    assert purchase_request.items.count() == 2


@pytest.mark.django_db
def test_generate_purchase_request_from_menu_com_estoque_suficiente_nao_cria():
    menu_day, arroz, feijao = _create_menu_for_procurement()

    StockItem.objects.create(
        ingredient=arroz,
        balance_qty=Decimal("3.000"),
        unit=IngredientUnit.KILOGRAM,
    )
    StockItem.objects.create(
        ingredient=feijao,
        balance_qty=Decimal("2.500"),
        unit=IngredientUnit.KILOGRAM,
    )

    result = generate_purchase_request_from_menu(menu_day.id)

    assert result == {
        "created": False,
        "purchase_request_id": None,
        "message": "sem compra necessaria",
        "items": [],
    }
    assert PurchaseRequest.objects.count() == 0


@pytest.mark.django_db
def test_generate_purchase_request_from_menu_com_estoque_parcial_cria_somente_faltas():
    menu_day, arroz, feijao = _create_menu_for_procurement()

    StockItem.objects.create(
        ingredient=arroz,
        balance_qty=Decimal("1.200"),
        unit=IngredientUnit.KILOGRAM,
    )
    StockItem.objects.create(
        ingredient=feijao,
        balance_qty=Decimal("2.000"),
        unit=IngredientUnit.KILOGRAM,
    )

    result = generate_purchase_request_from_menu(menu_day.id)

    assert result["created"] is True
    assert len(result["items"]) == 1
    assert result["items"][0]["ingredient_id"] == arroz.id
    assert result["items"][0]["required_qty"] == Decimal("1.800")
    assert result["items"][0]["unit"] == IngredientUnit.KILOGRAM

    purchase_request = PurchaseRequest.objects.get(pk=result["purchase_request_id"])
    assert purchase_request.items.count() == 1
    assert purchase_request.items.first().ingredient_id == arroz.id
