from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PersonalDirection(models.TextChoices):
    IN = "IN", "Entrada"
    OUT = "OUT", "Saida"


class PersonalRecurringFrequency(models.TextChoices):
    WEEKLY = "WEEKLY", "Semanal"
    MONTHLY = "MONTHLY", "Mensal"


class PersonalImportStatus(models.TextChoices):
    PREVIEWED = "PREVIEWED", "Preview concluido"
    CONFIRMED = "CONFIRMED", "Importacao confirmada"
    FAILED = "FAILED", "Falha no processamento"


class PersonalAccountType(models.TextChoices):
    CHECKING = "CHECKING", "Conta corrente"
    CASH = "CASH", "Dinheiro"
    CARD = "CARD", "Cartao"
    SAVINGS = "SAVINGS", "Poupanca"


class PersonalAuditEvent(models.TextChoices):
    LIST = "LIST", "Consulta"
    RETRIEVE = "RETRIEVE", "Detalhe"
    CREATE = "CREATE", "Criacao"
    UPDATE = "UPDATE", "Atualizacao"
    DELETE = "DELETE", "Exclusao"
    EXPORT = "EXPORT", "Exportacao"


class PersonalAccount(TimeStampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="personal_finance_accounts",
    )
    name = models.CharField(max_length=120)
    type = models.CharField(
        max_length=16,
        choices=PersonalAccountType.choices,
        default=PersonalAccountType.CHECKING,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"],
                name="personal_account_owner_name_unique",
            )
        ]

    def __str__(self) -> str:
        return f"{self.owner_id}:{self.name}"


class PersonalCategory(TimeStampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="personal_finance_categories",
    )
    name = models.CharField(max_length=120)
    direction = models.CharField(
        max_length=8,
        choices=PersonalDirection.choices,
        default=PersonalDirection.OUT,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name", "direction"],
                name="personal_category_owner_name_direction_unique",
            )
        ]

    def __str__(self) -> str:
        return f"{self.owner_id}:{self.name}:{self.direction}"


class PersonalRecurringRule(TimeStampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="personal_finance_recurring_rules",
    )
    account = models.ForeignKey(
        PersonalAccount,
        on_delete=models.PROTECT,
        related_name="recurring_rules",
    )
    category = models.ForeignKey(
        PersonalCategory,
        on_delete=models.PROTECT,
        related_name="recurring_rules",
    )
    direction = models.CharField(max_length=8, choices=PersonalDirection.choices)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    description = models.CharField(max_length=255, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    frequency = models.CharField(
        max_length=16,
        choices=PersonalRecurringFrequency.choices,
        default=PersonalRecurringFrequency.MONTHLY,
    )
    interval = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(null=True, blank=True)
    next_run_date = models.DateField(default=date.today)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["next_run_date", "id"]
        indexes = [
            models.Index(
                fields=["owner", "next_run_date"],
                name="pf_rule_owner_next_run_idx",
            )
        ]

    def __str__(self) -> str:
        return f"RecurringRule<{self.owner_id}:{self.id}>"


class PersonalImportJob(TimeStampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="personal_finance_import_jobs",
    )
    status = models.CharField(
        max_length=16,
        choices=PersonalImportStatus.choices,
        default=PersonalImportStatus.PREVIEWED,
    )
    source_filename = models.CharField(max_length=255)
    delimiter = models.CharField(max_length=1, default=",")
    preview_rows = models.JSONField(default=list, blank=True)
    error_rows = models.JSONField(default=list, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    rows_total = models.PositiveIntegerField(default=0)
    rows_valid = models.PositiveIntegerField(default=0)
    rows_invalid = models.PositiveIntegerField(default=0)
    imported_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["owner", "status"],
                name="pf_import_owner_status_idx",
            )
        ]

    def __str__(self) -> str:
        return f"ImportJob<{self.owner_id}:{self.id}:{self.status}>"


class PersonalEntry(TimeStampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="personal_finance_entries",
    )
    account = models.ForeignKey(
        PersonalAccount,
        on_delete=models.PROTECT,
        related_name="entries",
    )
    category = models.ForeignKey(
        PersonalCategory,
        on_delete=models.PROTECT,
        related_name="entries",
    )
    recurring_rule = models.ForeignKey(
        PersonalRecurringRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="materialized_entries",
    )
    import_job = models.ForeignKey(
        PersonalImportJob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="imported_entries",
    )
    direction = models.CharField(max_length=8, choices=PersonalDirection.choices)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    entry_date = models.DateField(default=date.today)
    description = models.CharField(max_length=255, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    recurring_event_key = models.CharField(max_length=80, null=True, blank=True)
    import_hash = models.CharField(max_length=64, null=True, blank=True)

    class Meta:
        ordering = ["-entry_date", "-id"]
        indexes = [
            models.Index(
                fields=["owner", "entry_date"], name="personal_entry_owner_date_idx"
            ),
            models.Index(
                fields=["owner", "import_hash"],
                name="pf_entry_owner_import_hash_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "recurring_event_key"],
                name="personal_entry_owner_recur_event_key_unique",
            ),
            models.UniqueConstraint(
                fields=["owner", "import_hash"],
                name="personal_entry_owner_import_hash_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"Entry<{self.owner_id}:{self.id}>"


class PersonalBudget(TimeStampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="personal_finance_budgets",
    )
    category = models.ForeignKey(
        PersonalCategory,
        on_delete=models.PROTECT,
        related_name="budgets",
    )
    month_ref = models.DateField()
    limit_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    class Meta:
        ordering = ["-month_ref", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "category", "month_ref"],
                name="personal_budget_owner_category_month_unique",
            )
        ]

    def __str__(self) -> str:
        return f"Budget<{self.owner_id}:{self.month_ref.isoformat()}>"


class PersonalAuditLog(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="personal_finance_audit_logs",
    )
    event_type = models.CharField(
        max_length=16,
        choices=PersonalAuditEvent.choices,
    )
    resource_type = models.CharField(max_length=40)
    resource_id = models.PositiveIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["owner", "created_at"],
                name="personal_audit_owner_date_idx",
            )
        ]

    def __str__(self) -> str:
        return (
            f"Audit<{self.owner_id}:{self.event_type}:"
            f"{self.resource_type}:{self.resource_id or '-'}>"
        )
