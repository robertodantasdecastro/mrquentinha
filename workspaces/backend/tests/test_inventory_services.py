from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.catalog.models import Ingredient, IngredientUnit
from apps.inventory.models import StockMovement, StockMovementType, StockReferenceType
from apps.inventory.selectors import get_stock_by_ingredient
from apps.inventory.services import apply_stock_movement


@pytest.mark.django_db
def test_movement_out_nao_pode_deixar_saldo_negativo():
    ingredient = Ingredient.objects.create(
        name="arroz cru", unit=IngredientUnit.KILOGRAM
    )

    with pytest.raises(ValidationError):
        apply_stock_movement(
            ingredient=ingredient,
            movement_type=StockMovementType.OUT,
            qty=Decimal("1.000"),
            unit=IngredientUnit.KILOGRAM,
            reference_type=StockReferenceType.CONSUMPTION,
        )

    stock_item = get_stock_by_ingredient(ingredient)
    assert stock_item is None
    assert not StockMovement.objects.filter(ingredient=ingredient).exists()


@pytest.mark.django_db
def test_movement_in_aumenta_saldo():
    ingredient = Ingredient.objects.create(name="feijao", unit=IngredientUnit.KILOGRAM)

    apply_stock_movement(
        ingredient=ingredient,
        movement_type=StockMovementType.IN,
        qty=Decimal("2.500"),
        unit=IngredientUnit.KILOGRAM,
        reference_type=StockReferenceType.ADJUSTMENT,
    )
    apply_stock_movement(
        ingredient=ingredient,
        movement_type=StockMovementType.IN,
        qty=Decimal("0.500"),
        unit=IngredientUnit.KILOGRAM,
        reference_type=StockReferenceType.ADJUSTMENT,
    )

    stock_item = get_stock_by_ingredient(ingredient)
    assert stock_item is not None
    assert stock_item.balance_qty == Decimal("3.000")
