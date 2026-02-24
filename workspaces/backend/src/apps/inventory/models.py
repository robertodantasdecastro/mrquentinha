from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.catalog.models import Ingredient, IngredientUnit


class StockItem(models.Model):
    ingredient = models.OneToOneField(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="stock_item",
    )
    balance_qty = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    unit = models.CharField(max_length=16, choices=IngredientUnit.choices)
    min_qty = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ingredient__name"]

    def __str__(self) -> str:
        return f"{self.ingredient.name} ({self.balance_qty} {self.unit})"


class StockMovementType(models.TextChoices):
    IN = "IN", "IN"
    OUT = "OUT", "OUT"
    ADJUST = "ADJUST", "ADJUST"


class StockReferenceType(models.TextChoices):
    PURCHASE = "PURCHASE", "PURCHASE"
    CONSUMPTION = "CONSUMPTION", "CONSUMPTION"
    ADJUSTMENT = "ADJUSTMENT", "ADJUSTMENT"
    PRODUCTION = "PRODUCTION", "PRODUCTION"


class StockMovement(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    movement_type = models.CharField(max_length=16, choices=StockMovementType.choices)
    qty = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    unit = models.CharField(max_length=16, choices=IngredientUnit.choices)
    reference_type = models.CharField(max_length=16, choices=StockReferenceType.choices)
    reference_id = models.PositiveIntegerField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_movements_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.movement_type} {self.ingredient.name} ({self.qty} {self.unit})"
