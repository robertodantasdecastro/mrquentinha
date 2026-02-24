from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.inventory.models import StockMovementType, StockReferenceType
from apps.inventory.services import apply_stock_movement

from .models import ProductionBatch, ProductionBatchStatus, ProductionItem
from .selectors import (
    get_batch_detail,
    get_batch_for_completion,
    get_menu_day_for_production,
    has_out_movements_for_batch,
)

QTY_DECIMAL_PLACES = Decimal("0.001")


def _quantize_qty(value: Decimal) -> Decimal:
    return value.quantize(QTY_DECIMAL_PLACES, rounding=ROUND_HALF_UP)


def _assert_items_payload(items_payload: list[dict]) -> None:
    if not items_payload:
        raise ValidationError("Lote de producao deve possuir ao menos um item.")

    menu_item_ids = [item["menu_item"].id for item in items_payload]
    if len(menu_item_ids) != len(set(menu_item_ids)):
        raise ValidationError("Item de cardapio duplicado no lote de producao.")

    for item in items_payload:
        if item["qty_planned"] <= 0:
            raise ValidationError("Quantidade planejada deve ser maior que zero.")


def _resolve_recipe_unit(*, ingredient, recipe_unit: str | None) -> str:
    unit = recipe_unit or ingredient.unit
    if unit != ingredient.unit:
        raise ValidationError(
            f"Unidade incompativel para ingrediente '{ingredient.name}': "
            f"receita usa '{unit}' e ingrediente usa '{ingredient.unit}'. "
            "TODO: implementar conversao de unidades."
        )
    return unit


@transaction.atomic
def create_batch_for_date(
    *,
    production_date: date,
    items_payload: list[dict],
    note: str | None = None,
    created_by=None,
) -> ProductionBatch:
    _assert_items_payload(items_payload)

    menu_day = get_menu_day_for_production(production_date)
    if menu_day is None:
        raise ValidationError("Nao existe cardapio para a data de producao informada.")

    if ProductionBatch.objects.filter(production_date=production_date).exists():
        raise ValidationError("Ja existe lote de producao para a data informada.")

    for item in items_payload:
        menu_item = item["menu_item"]
        if menu_item.menu_day_id != menu_day.id:
            raise ValidationError(
                "Menu item informado nao pertence ao cardapio da data de producao."
            )

    batch = ProductionBatch.objects.create(
        production_date=production_date,
        status=ProductionBatchStatus.PLANNED,
        note=note,
        created_by=created_by,
    )

    ProductionItem.objects.bulk_create(
        [
            ProductionItem(
                batch=batch,
                menu_item=item["menu_item"],
                qty_planned=item["qty_planned"],
                qty_produced=item.get("qty_produced", 0),
                qty_waste=item.get("qty_waste", 0),
                note=item.get("note"),
            )
            for item in items_payload
        ]
    )

    return get_batch_detail(batch.id)


@transaction.atomic
def complete_batch(*, batch_id: int) -> ProductionBatch:
    batch = get_batch_for_completion(batch_id)
    if batch is None:
        raise ValidationError("Lote de producao nao encontrado.")

    if batch.status == ProductionBatchStatus.DONE:
        return batch

    if batch.status == ProductionBatchStatus.CANCELED:
        raise ValidationError("Lote cancelado nao pode ser concluido.")

    if has_out_movements_for_batch(batch.id):
        batch.status = ProductionBatchStatus.DONE
        batch.save(update_fields=["status", "updated_at"])
        return get_batch_detail(batch.id)

    for batch_item in batch.items.all():
        if batch_item.qty_produced <= 0:
            continue

        dish = batch_item.menu_item.dish
        multiplier = Decimal(batch_item.qty_produced)

        for dish_ingredient in dish.dish_ingredients.all():
            ingredient = dish_ingredient.ingredient
            unit = _resolve_recipe_unit(
                ingredient=ingredient,
                recipe_unit=dish_ingredient.unit,
            )
            consume_qty = _quantize_qty(dish_ingredient.quantity * multiplier)

            if consume_qty <= 0:
                continue

            apply_stock_movement(
                ingredient=ingredient,
                movement_type=StockMovementType.OUT,
                qty=consume_qty,
                unit=unit,
                reference_type=StockReferenceType.PRODUCTION,
                reference_id=batch.id,
                note=f"Consumo por producao do lote {batch.id}",
                created_by=batch.created_by,
            )

    batch.status = ProductionBatchStatus.DONE
    batch.save(update_fields=["status", "updated_at"])

    return get_batch_detail(batch.id)
