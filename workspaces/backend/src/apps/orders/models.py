from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.catalog.models import MenuItem


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OrderStatus(models.TextChoices):
    CREATED = "CREATED", "CREATED"
    CONFIRMED = "CONFIRMED", "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS", "IN_PROGRESS"
    DELIVERED = "DELIVERED", "DELIVERED"
    CANCELED = "CANCELED", "CANCELED"


class PaymentMethod(models.TextChoices):
    PIX = "PIX", "PIX"
    CARD = "CARD", "CARD"
    VR = "VR", "VR"
    CASH = "CASH", "CASH"


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "PENDING"
    PAID = "PAID", "PAID"
    FAILED = "FAILED", "FAILED"
    REFUNDED = "REFUNDED", "REFUNDED"


class PaymentIntentStatus(models.TextChoices):
    REQUIRES_ACTION = "REQUIRES_ACTION", "REQUIRES_ACTION"
    PROCESSING = "PROCESSING", "PROCESSING"
    SUCCEEDED = "SUCCEEDED", "SUCCEEDED"
    FAILED = "FAILED", "FAILED"
    CANCELED = "CANCELED", "CANCELED"
    EXPIRED = "EXPIRED", "EXPIRED"


class Order(TimeStampedModel):
    AR_REFERENCE_TYPE = "ORDER"

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateField(db_index=True)
    status = models.CharField(
        max_length=16,
        choices=OrderStatus.choices,
        default=OrderStatus.CREATED,
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        ordering = ["-order_date", "-id"]

    def __str__(self) -> str:
        return f"Pedido-{self.id} ({self.delivery_date})"

    def get_ar_reference(self) -> dict[str, str | int]:
        return {
            "reference_type": self.AR_REFERENCE_TYPE,
            "reference_id": self.id,
        }


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    qty = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order", "menu_item"],
                name="orders_orderitem_order_menu_item_unique",
            )
        ]

    def __str__(self) -> str:
        return f"Pedido-{self.order_id} item-{self.menu_item_id}"


class Payment(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    method = models.CharField(
        max_length=16,
        choices=PaymentMethod.choices,
        default=PaymentMethod.PIX,
    )
    status = models.CharField(
        max_length=16,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    provider_ref = models.CharField(max_length=180, null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"Pagamento-{self.id} ({self.status})"


class PaymentIntent(TimeStampedModel):
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="intents",
    )
    provider = models.CharField(max_length=40)
    status = models.CharField(
        max_length=24,
        choices=PaymentIntentStatus.choices,
        default=PaymentIntentStatus.REQUIRES_ACTION,
    )
    idempotency_key = models.CharField(max_length=128)
    provider_intent_ref = models.CharField(max_length=180, null=True, blank=True)
    client_payload = models.JSONField(default=dict, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["payment", "idempotency_key"],
                name="orders_paymentintent_payment_idempotency_unique",
            )
        ]

    def __str__(self) -> str:
        return f"Intent-{self.id} pagamento-{self.payment_id} ({self.status})"
