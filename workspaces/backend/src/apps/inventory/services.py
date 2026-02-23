from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.catalog.models import Ingredient

from .models import StockItem, StockMovement, StockMovementType


def ensure_stock_item(
    ingredient: Ingredient,
    *,
    unit: str | None = None,
    min_qty: Decimal | None = None,
) -> StockItem:
    stock_item, _ = StockItem.objects.get_or_create(
        ingredient=ingredient,
        defaults={"unit": unit or ingredient.unit, "min_qty": min_qty},
    )

    if unit is not None and stock_item.unit != unit:
        raise ValidationError("Unidade do estoque difere da unidade informada.")

    if min_qty is not None and stock_item.min_qty != min_qty:
        stock_item.min_qty = min_qty
        stock_item.save(update_fields=["min_qty", "updated_at"])

    return stock_item


def _compute_new_balance(
    current_balance: Decimal, movement_type: str, qty: Decimal
) -> Decimal:
    if movement_type == StockMovementType.IN:
        return current_balance + qty

    if movement_type == StockMovementType.OUT:
        new_balance = current_balance - qty
        if new_balance < 0:
            raise ValidationError("Movimento OUT nao pode gerar saldo negativo.")
        return new_balance

    if movement_type == StockMovementType.ADJUST:
        return qty

    raise ValidationError("Tipo de movimento de estoque invalido.")


@transaction.atomic
def apply_stock_movement(
    *,
    ingredient: Ingredient,
    movement_type: str,
    qty: Decimal,
    unit: str,
    reference_type: str,
    reference_id: int | None = None,
    note: str | None = None,
    created_by=None,
) -> StockMovement:
    if qty <= 0:
        raise ValidationError("Quantidade do movimento deve ser maior que zero.")

    stock_item = (
        StockItem.objects.select_for_update().filter(ingredient=ingredient).first()
    )
    if stock_item is None:
        created_stock = ensure_stock_item(ingredient, unit=unit)
        stock_item = StockItem.objects.select_for_update().get(pk=created_stock.pk)

    if stock_item.unit != unit:
        raise ValidationError("Unidade do movimento difere da unidade do estoque.")

    stock_item.balance_qty = _compute_new_balance(
        stock_item.balance_qty, movement_type, qty
    )
    stock_item.save(update_fields=["balance_qty", "updated_at"])

    return StockMovement.objects.create(
        ingredient=ingredient,
        movement_type=movement_type,
        qty=qty,
        unit=unit,
        reference_type=reference_type,
        reference_id=reference_id,
        note=note,
        created_by=created_by,
    )
