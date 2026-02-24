from datetime import date

from django.db.models import QuerySet

from apps.catalog.models import MenuDay
from apps.inventory.models import StockMovement, StockMovementType, StockReferenceType

from .models import ProductionBatch


def list_batches() -> QuerySet[ProductionBatch]:
    return (
        ProductionBatch.objects.select_related("created_by")
        .prefetch_related("items__menu_item__dish")
        .order_by("-production_date", "-id")
    )


def get_batch_detail(batch_id: int) -> ProductionBatch | None:
    return list_batches().filter(pk=batch_id).first()


def get_batch_for_completion(batch_id: int) -> ProductionBatch | None:
    return (
        ProductionBatch.objects.select_for_update()
        .prefetch_related("items__menu_item__dish__dish_ingredients__ingredient")
        .filter(pk=batch_id)
        .first()
    )


def get_menu_day_for_production(production_date: date) -> MenuDay | None:
    return (
        MenuDay.objects.filter(menu_date=production_date)
        .prefetch_related("items__dish__dish_ingredients__ingredient")
        .first()
    )


def has_out_movements_for_batch(batch_id: int) -> bool:
    return StockMovement.objects.filter(
        movement_type=StockMovementType.OUT,
        reference_type=StockReferenceType.PRODUCTION,
        reference_id=batch_id,
    ).exists()
