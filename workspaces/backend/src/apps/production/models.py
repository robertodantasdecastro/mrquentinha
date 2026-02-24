from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.catalog.models import MenuItem


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ProductionBatchStatus(models.TextChoices):
    PLANNED = "PLANNED", "PLANNED"
    IN_PROGRESS = "IN_PROGRESS", "IN_PROGRESS"
    DONE = "DONE", "DONE"
    CANCELED = "CANCELED", "CANCELED"


class ProductionBatch(TimeStampedModel):
    production_date = models.DateField(unique=True)
    status = models.CharField(
        max_length=16,
        choices=ProductionBatchStatus.choices,
        default=ProductionBatchStatus.PLANNED,
    )
    note = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="production_batches_created",
    )

    class Meta:
        ordering = ["-production_date", "-id"]

    def __str__(self) -> str:
        return f"Lote {self.id} - {self.production_date}"


class ProductionItem(models.Model):
    batch = models.ForeignKey(
        ProductionBatch,
        on_delete=models.CASCADE,
        related_name="items",
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT,
        related_name="production_items",
    )
    qty_planned = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    qty_produced = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )
    qty_waste = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )
    note = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["batch", "menu_item"],
                name="production_item_batch_menu_item_unique",
            )
        ]

    def __str__(self) -> str:
        return f"Lote {self.batch_id} - item {self.menu_item_id}"
