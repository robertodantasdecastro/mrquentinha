from datetime import date
from decimal import Decimal

import pytest

from apps.catalog.models import Ingredient, IngredientUnit
from apps.inventory.models import StockMovement, StockMovementType, StockReferenceType
from apps.inventory.selectors import get_stock_by_ingredient
from apps.procurement.services import create_purchase_and_apply_stock


@pytest.mark.django_db
def test_create_purchase_and_apply_stock_cria_movimentos_in_e_atualiza_saldo():
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
        ingredient=ingredient, reference_id=purchase.id
    )
    assert movement.movement_type == StockMovementType.IN
    assert movement.reference_type == StockReferenceType.PURCHASE

    stock_item = get_stock_by_ingredient(ingredient)
    assert stock_item is not None
    assert stock_item.balance_qty == Decimal("3.000")
