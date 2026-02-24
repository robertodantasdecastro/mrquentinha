from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AccountType(models.TextChoices):
    REVENUE = "REVENUE", "REVENUE"
    EXPENSE = "EXPENSE", "EXPENSE"
    ASSET = "ASSET", "ASSET"
    LIABILITY = "LIABILITY", "LIABILITY"


class APBillStatus(models.TextChoices):
    OPEN = "OPEN", "OPEN"
    PAID = "PAID", "PAID"
    CANCELED = "CANCELED", "CANCELED"


class ARReceivableStatus(models.TextChoices):
    OPEN = "OPEN", "OPEN"
    RECEIVED = "RECEIVED", "RECEIVED"
    CANCELED = "CANCELED", "CANCELED"


class CashDirection(models.TextChoices):
    IN = "IN", "IN"
    OUT = "OUT", "OUT"


class LedgerEntryType(models.TextChoices):
    AP_PAID = "AP_PAID", "AP_PAID"
    AR_RECEIVED = "AR_RECEIVED", "AR_RECEIVED"
    CASH_IN = "CASH_IN", "CASH_IN"
    CASH_OUT = "CASH_OUT", "CASH_OUT"
    ADJUSTMENT = "ADJUSTMENT", "ADJUSTMENT"


class Account(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    type = models.CharField(max_length=16, choices=AccountType.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class APBill(TimeStampedModel):
    supplier_name = models.CharField(max_length=180)
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="ap_bills",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    due_date = models.DateField()
    status = models.CharField(
        max_length=16,
        choices=APBillStatus.choices,
        default=APBillStatus.OPEN,
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    reference_type = models.CharField(max_length=32, null=True, blank=True)
    reference_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["due_date", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["reference_type", "reference_id"],
                condition=(
                    Q(reference_type__isnull=False)
                    & ~Q(reference_type="")
                    & Q(reference_id__isnull=False)
                ),
                name="finance_apbill_reference_unique",
            )
        ]

    def __str__(self) -> str:
        return f"AP-{self.id} ({self.status})"


class ARReceivable(TimeStampedModel):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="finance_receivables",
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="ar_receivables",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    due_date = models.DateField()
    status = models.CharField(
        max_length=16,
        choices=ARReceivableStatus.choices,
        default=ARReceivableStatus.OPEN,
    )
    received_at = models.DateTimeField(null=True, blank=True)
    reference_type = models.CharField(max_length=32, null=True, blank=True)
    reference_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["due_date", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["reference_type", "reference_id"],
                condition=(
                    Q(reference_type__isnull=False)
                    & ~Q(reference_type="")
                    & Q(reference_id__isnull=False)
                ),
                name="finance_arreceivable_reference_unique",
            )
        ]

    def __str__(self) -> str:
        return f"AR-{self.id} ({self.status})"


class CashMovement(models.Model):
    movement_date = models.DateTimeField(default=timezone.now)
    direction = models.CharField(max_length=8, choices=CashDirection.choices)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="cash_movements",
    )
    note = models.TextField(null=True, blank=True)
    reference_type = models.CharField(max_length=32, null=True, blank=True)
    reference_id = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-movement_date", "-id"]

    def __str__(self) -> str:
        return f"Cash-{self.id} ({self.direction})"


class LedgerEntry(models.Model):
    entry_date = models.DateTimeField(default=timezone.now)
    entry_type = models.CharField(max_length=16, choices=LedgerEntryType.choices)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    debit_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ledger_debits",
    )
    credit_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ledger_credits",
    )
    reference_type = models.CharField(max_length=32)
    reference_id = models.PositiveIntegerField()
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-entry_date", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["reference_type", "reference_id", "entry_type"],
                name="finance_ledger_reference_entry_type_unique",
            )
        ]

    def __str__(self) -> str:
        return f"Ledger-{self.id} ({self.entry_type})"
