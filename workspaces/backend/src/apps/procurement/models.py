from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.catalog.models import Ingredient, IngredientUnit


class PurchaseRequestStatus(models.TextChoices):
    OPEN = "OPEN", "OPEN"
    APPROVED = "APPROVED", "APPROVED"
    BOUGHT = "BOUGHT", "BOUGHT"
    CANCELED = "CANCELED", "CANCELED"


class PurchaseRequest(models.Model):
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="procurement_requests",
    )
    status = models.CharField(
        max_length=16,
        choices=PurchaseRequestStatus.choices,
        default=PurchaseRequestStatus.OPEN,
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-requested_at", "-id"]

    def __str__(self) -> str:
        return f"PR-{self.id} ({self.status})"


class PurchaseRequestItem(models.Model):
    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name="items",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="purchase_request_items",
    )
    required_qty = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    unit = models.CharField(max_length=16, choices=IngredientUnit.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["purchase_request", "ingredient"],
                name="proc_request_item_request_ingredient_unique",
            )
        ]

    def __str__(self) -> str:
        return f"{self.purchase_request_id} - {self.ingredient.name}"


class Purchase(models.Model):
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchases_made",
    )
    supplier_name = models.CharField(max_length=180)
    invoice_number = models.CharField(max_length=120, null=True, blank=True)
    purchase_date = models.DateField()
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    receipt_image = models.ImageField(
        upload_to="procurement/receipts/%Y/%m/%d",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-purchase_date", "-id"]

    def __str__(self) -> str:
        return f"Compra-{self.id} ({self.supplier_name})"


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name="items",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="purchase_items",
    )
    qty = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    unit = models.CharField(max_length=16, choices=IngredientUnit.choices)
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    expiry_date = models.DateField(null=True, blank=True)
    label_front_image = models.ImageField(
        upload_to="procurement/labels/front/%Y/%m/%d",
        null=True,
        blank=True,
    )
    label_back_image = models.ImageField(
        upload_to="procurement/labels/back/%Y/%m/%d",
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"{self.purchase_id} - {self.ingredient.name}"
