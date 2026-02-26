import csv
import hashlib
import io
import json
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import (
    PersonalAccount,
    PersonalAuditEvent,
    PersonalAuditLog,
    PersonalBudget,
    PersonalCategory,
    PersonalDirection,
    PersonalEntry,
    PersonalImportJob,
    PersonalImportStatus,
    PersonalRecurringFrequency,
    PersonalRecurringRule,
)
from .selectors import list_personal_audit_logs_older_than

PERSONAL_AUDIT_RETENTION_DAYS = 730
MONEY_QUANTIZER = Decimal("0.01")
CSV_REQUIRED_HEADERS = {"entry_date", "direction", "amount", "account", "category"}


def _ensure_owner(*, resource_name: str, resource_owner_id: int, user_id: int) -> None:
    if resource_owner_id != user_id:
        raise ValidationError(f"{resource_name} nao pertence ao usuario autenticado.")


def normalize_month_ref(month_ref: date) -> date:
    return month_ref.replace(day=1)


def _end_of_month(month_ref: date) -> date:
    month_start = normalize_month_ref(month_ref)
    last_day = monthrange(month_start.year, month_start.month)[1]
    return month_start.replace(day=last_day)


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTIZER)


def _add_months(base_date: date, months: int) -> date:
    shifted_month = base_date.month - 1 + months
    year = base_date.year + shifted_month // 12
    month = shifted_month % 12 + 1
    day = min(base_date.day, monthrange(year, month)[1])
    return date(year, month, day)


def _advance_recurrence_date(
    *,
    current_date: date,
    frequency: str,
    interval: int,
) -> date:
    if frequency == PersonalRecurringFrequency.WEEKLY:
        return current_date + timedelta(weeks=interval)

    if frequency == PersonalRecurringFrequency.MONTHLY:
        return _add_months(current_date, interval)

    raise ValidationError("Frequencia de recorrencia invalida.")


def _build_recurring_event_key(*, rule_id: int, occurrence_date: date) -> str:
    return f"rule:{rule_id}:{occurrence_date.isoformat()}"


def _build_import_hash(
    *,
    owner_id: int,
    account_id: int,
    category_id: int,
    direction: str,
    amount: Decimal,
    entry_date: date,
    description: str,
    metadata: dict,
) -> str:
    canonical_payload = {
        "owner_id": owner_id,
        "account_id": account_id,
        "category_id": category_id,
        "direction": direction,
        "amount": f"{_quantize_money(amount):.2f}",
        "entry_date": entry_date.isoformat(),
        "description": description.strip(),
        "metadata": metadata,
    }
    digest_source = json.dumps(canonical_payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(digest_source.encode("utf-8")).hexdigest()


def _validate_entry_relations(*, owner, account, category, direction: str) -> None:
    _ensure_owner(
        resource_name="Conta pessoal",
        resource_owner_id=account.owner_id,
        user_id=owner.id,
    )
    _ensure_owner(
        resource_name="Categoria pessoal",
        resource_owner_id=category.owner_id,
        user_id=owner.id,
    )

    if direction != category.direction:
        raise ValidationError(
            "direction precisa ser igual ao direction da categoria selecionada."
        )


@transaction.atomic
def create_personal_entry(*, owner, payload: dict) -> PersonalEntry:
    account = payload["account"]
    category = payload["category"]
    direction = payload.get("direction", category.direction)

    _validate_entry_relations(
        owner=owner,
        account=account,
        category=category,
        direction=direction,
    )

    return PersonalEntry.objects.create(
        owner=owner,
        account=account,
        category=category,
        recurring_rule=payload.get("recurring_rule"),
        import_job=payload.get("import_job"),
        direction=direction,
        amount=payload["amount"],
        entry_date=payload["entry_date"],
        description=payload.get("description", ""),
        metadata=payload.get("metadata", {}),
        recurring_event_key=payload.get("recurring_event_key"),
        import_hash=payload.get("import_hash"),
    )


@transaction.atomic
def update_personal_entry(
    *, entry: PersonalEntry, owner, payload: dict
) -> PersonalEntry:
    _ensure_owner(
        resource_name="Lancamento pessoal",
        resource_owner_id=entry.owner_id,
        user_id=owner.id,
    )

    account = payload.get("account", entry.account)
    category = payload.get("category", entry.category)
    direction = payload.get("direction", entry.direction)

    _validate_entry_relations(
        owner=owner,
        account=account,
        category=category,
        direction=direction,
    )

    update_fields: list[str] = []
    for field_name, value in {
        "account": account,
        "category": category,
        "direction": direction,
        "amount": payload.get("amount", entry.amount),
        "entry_date": payload.get("entry_date", entry.entry_date),
        "description": payload.get("description", entry.description),
        "metadata": payload.get("metadata", entry.metadata),
    }.items():
        if getattr(entry, field_name) != value:
            setattr(entry, field_name, value)
            update_fields.append(field_name)

    if update_fields:
        update_fields.append("updated_at")
        entry.save(update_fields=update_fields)

    return entry


@transaction.atomic
def create_personal_budget(*, owner, payload: dict) -> PersonalBudget:
    category = payload["category"]
    _ensure_owner(
        resource_name="Categoria pessoal",
        resource_owner_id=category.owner_id,
        user_id=owner.id,
    )

    month_ref = normalize_month_ref(payload["month_ref"])

    return PersonalBudget.objects.create(
        owner=owner,
        category=category,
        month_ref=month_ref,
        limit_amount=payload["limit_amount"],
    )


@transaction.atomic
def update_personal_budget(
    *, budget: PersonalBudget, owner, payload: dict
) -> PersonalBudget:
    _ensure_owner(
        resource_name="Orcamento pessoal",
        resource_owner_id=budget.owner_id,
        user_id=owner.id,
    )

    category = payload.get("category", budget.category)
    _ensure_owner(
        resource_name="Categoria pessoal",
        resource_owner_id=category.owner_id,
        user_id=owner.id,
    )

    month_ref = normalize_month_ref(payload.get("month_ref", budget.month_ref))
    limit_amount = payload.get("limit_amount", budget.limit_amount)

    update_fields: list[str] = []
    for field_name, value in {
        "category": category,
        "month_ref": month_ref,
        "limit_amount": limit_amount,
    }.items():
        if getattr(budget, field_name) != value:
            setattr(budget, field_name, value)
            update_fields.append(field_name)

    if update_fields:
        update_fields.append("updated_at")
        budget.save(update_fields=update_fields)

    return budget


def _validate_recurring_rule_dates(
    *,
    start_date: date,
    end_date: date | None,
    next_run_date: date,
) -> None:
    if end_date is not None and start_date > end_date:
        raise ValidationError("start_date deve ser menor ou igual a end_date.")

    if next_run_date < start_date:
        raise ValidationError("next_run_date deve ser maior ou igual a start_date.")

    if end_date is not None and next_run_date > end_date:
        raise ValidationError("next_run_date nao pode ser maior que end_date.")


@transaction.atomic
def create_personal_recurring_rule(*, owner, payload: dict) -> PersonalRecurringRule:
    account = payload["account"]
    category = payload["category"]
    direction = payload.get("direction", category.direction)

    _validate_entry_relations(
        owner=owner,
        account=account,
        category=category,
        direction=direction,
    )

    start_date = payload.get("start_date", date.today())
    next_run_date = payload.get("next_run_date", start_date)
    end_date = payload.get("end_date")
    interval = payload.get("interval", 1)

    if interval <= 0:
        raise ValidationError("interval deve ser maior que zero.")

    _validate_recurring_rule_dates(
        start_date=start_date,
        end_date=end_date,
        next_run_date=next_run_date,
    )

    return PersonalRecurringRule.objects.create(
        owner=owner,
        account=account,
        category=category,
        direction=direction,
        amount=payload["amount"],
        description=payload.get("description", ""),
        metadata=payload.get("metadata", {}),
        frequency=payload.get("frequency", PersonalRecurringFrequency.MONTHLY),
        interval=interval,
        start_date=start_date,
        end_date=end_date,
        next_run_date=next_run_date,
        is_active=payload.get("is_active", True),
    )


@transaction.atomic
def update_personal_recurring_rule(
    *,
    recurring_rule: PersonalRecurringRule,
    owner,
    payload: dict,
) -> PersonalRecurringRule:
    _ensure_owner(
        resource_name="Regra recorrente pessoal",
        resource_owner_id=recurring_rule.owner_id,
        user_id=owner.id,
    )

    account = payload.get("account", recurring_rule.account)
    category = payload.get("category", recurring_rule.category)
    direction = payload.get("direction", recurring_rule.direction)

    _validate_entry_relations(
        owner=owner,
        account=account,
        category=category,
        direction=direction,
    )

    frequency = payload.get("frequency", recurring_rule.frequency)
    interval = payload.get("interval", recurring_rule.interval)
    if interval <= 0:
        raise ValidationError("interval deve ser maior que zero.")

    start_date = payload.get("start_date", recurring_rule.start_date)
    end_date = payload.get("end_date", recurring_rule.end_date)
    next_run_date = payload.get("next_run_date", recurring_rule.next_run_date)

    _validate_recurring_rule_dates(
        start_date=start_date,
        end_date=end_date,
        next_run_date=next_run_date,
    )

    update_fields: list[str] = []
    for field_name, value in {
        "account": account,
        "category": category,
        "direction": direction,
        "amount": payload.get("amount", recurring_rule.amount),
        "description": payload.get("description", recurring_rule.description),
        "metadata": payload.get("metadata", recurring_rule.metadata),
        "frequency": frequency,
        "interval": interval,
        "start_date": start_date,
        "end_date": end_date,
        "next_run_date": next_run_date,
        "is_active": payload.get("is_active", recurring_rule.is_active),
    }.items():
        if getattr(recurring_rule, field_name) != value:
            setattr(recurring_rule, field_name, value)
            update_fields.append(field_name)

    if update_fields:
        update_fields.append("updated_at")
        recurring_rule.save(update_fields=update_fields)

    return recurring_rule


@transaction.atomic
def materialize_personal_recurring_rules(
    *,
    owner,
    from_date: date,
    to_date: date,
    recurring_rule_id: int | None = None,
) -> dict:
    if from_date > to_date:
        raise ValidationError("from_date deve ser menor ou igual a to_date.")

    queryset = PersonalRecurringRule.objects.select_related(
        "account", "category"
    ).filter(
        owner=owner,
        is_active=True,
    )

    if recurring_rule_id is not None:
        queryset = queryset.filter(pk=recurring_rule_id)

    rules = list(queryset.order_by("id"))
    if recurring_rule_id is not None and not rules:
        raise ValidationError(
            "Regra recorrente informada nao encontrada para o usuario."
        )

    total_created = 0
    total_skipped = 0
    processed_rules: list[dict] = []

    for rule in rules:
        if rule.direction != rule.category.direction:
            processed_rules.append(
                {
                    "rule_id": rule.id,
                    "created": 0,
                    "skipped": 0,
                    "detail": "Regra ignorada: direction difere da categoria.",
                }
            )
            continue

        cursor = max(rule.next_run_date, rule.start_date)
        created = 0
        skipped = 0

        while cursor <= to_date:
            if rule.end_date is not None and cursor > rule.end_date:
                break

            if cursor >= from_date:
                recurring_event_key = _build_recurring_event_key(
                    rule_id=rule.id,
                    occurrence_date=cursor,
                )
                _, was_created = PersonalEntry.objects.get_or_create(
                    owner=owner,
                    recurring_event_key=recurring_event_key,
                    defaults={
                        "account": rule.account,
                        "category": rule.category,
                        "recurring_rule": rule,
                        "direction": rule.direction,
                        "amount": rule.amount,
                        "entry_date": cursor,
                        "description": rule.description,
                        "metadata": {
                            **rule.metadata,
                            "source": "recurring_rule",
                            "rule_id": rule.id,
                        },
                    },
                )
                if was_created:
                    created += 1
                else:
                    skipped += 1

            cursor = _advance_recurrence_date(
                current_date=cursor,
                frequency=rule.frequency,
                interval=rule.interval,
            )

        if cursor != rule.next_run_date:
            rule.next_run_date = cursor
            rule.save(update_fields=["next_run_date", "updated_at"])

        total_created += created
        total_skipped += skipped
        processed_rules.append(
            {
                "rule_id": rule.id,
                "created": created,
                "skipped": skipped,
                "next_run_date": rule.next_run_date.isoformat(),
            }
        )

    return {
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat(),
        "rules_processed": len(rules),
        "entries_created": total_created,
        "entries_skipped": total_skipped,
        "rules": processed_rules,
    }


def build_personal_monthly_summary(*, owner, month_ref: date) -> dict:
    month_start = normalize_month_ref(month_ref)
    month_end = _end_of_month(month_start)

    entries_queryset = PersonalEntry.objects.filter(
        owner=owner,
        entry_date__gte=month_start,
        entry_date__lte=month_end,
    )

    totals = entries_queryset.aggregate(
        total_in=Coalesce(
            Sum("amount", filter=Q(direction=PersonalDirection.IN)),
            Decimal("0.00"),
        ),
        total_out=Coalesce(
            Sum("amount", filter=Q(direction=PersonalDirection.OUT)),
            Decimal("0.00"),
        ),
    )

    total_in = _quantize_money(totals["total_in"])
    total_out = _quantize_money(totals["total_out"])
    balance = _quantize_money(total_in - total_out)

    category_rows = list(
        entries_queryset.values("category_id", "category__name", "direction")
        .annotate(
            total=Coalesce(Sum("amount"), Decimal("0.00")),
            entries_count=Count("id"),
        )
        .order_by("-total", "category__name")[:10]
    )

    top_categories = [
        {
            "category_id": row["category_id"],
            "category_name": row["category__name"],
            "direction": row["direction"],
            "total": f"{_quantize_money(row['total']):.2f}",
            "entries_count": int(row["entries_count"]),
        }
        for row in category_rows
    ]

    spent_rows = PersonalEntry.objects.filter(
        owner=owner,
        entry_date__gte=month_start,
        entry_date__lte=month_end,
        direction=PersonalDirection.OUT,
    ).values("category_id")
    spent_rows = spent_rows.annotate(total=Coalesce(Sum("amount"), Decimal("0.00")))
    spent_by_category = {
        row["category_id"]: _quantize_money(row["total"]) for row in spent_rows
    }

    budgets = PersonalBudget.objects.select_related("category").filter(
        owner=owner,
        month_ref=month_start,
    )

    budgets_status: list[dict] = []
    for budget in budgets:
        spent = spent_by_category.get(budget.category_id, Decimal("0.00"))
        remaining = _quantize_money(budget.limit_amount - spent)
        consumption_percent = Decimal("0.00")
        if budget.limit_amount > 0:
            consumption_percent = _quantize_money(
                (spent / budget.limit_amount) * Decimal("100")
            )

        if spent > budget.limit_amount:
            status_value = "ESTOURADO"
        elif consumption_percent >= Decimal("80.00"):
            status_value = "ALERTA"
        else:
            status_value = "OK"

        budgets_status.append(
            {
                "budget_id": budget.id,
                "category_id": budget.category_id,
                "category_name": budget.category.name,
                "limit_amount": f"{_quantize_money(budget.limit_amount):.2f}",
                "spent_amount": f"{spent:.2f}",
                "remaining_amount": f"{remaining:.2f}",
                "consumption_percent": f"{consumption_percent:.2f}",
                "status": status_value,
            }
        )

    return {
        "month_ref": month_start.isoformat(),
        "period": {
            "from": month_start.isoformat(),
            "to": month_end.isoformat(),
        },
        "totals": {
            "total_in": f"{total_in:.2f}",
            "total_out": f"{total_out:.2f}",
            "balance": f"{balance:.2f}",
        },
        "entries_count": entries_queryset.count(),
        "top_categories": top_categories,
        "budgets": budgets_status,
    }


def _build_account_name_map(*, owner) -> dict[str, PersonalAccount]:
    queryset = PersonalAccount.objects.filter(owner=owner)
    return {account.name.strip().lower(): account for account in queryset}


def _build_category_name_map(*, owner) -> dict[tuple[str, str], PersonalCategory]:
    queryset = PersonalCategory.objects.filter(owner=owner)
    return {
        (category.name.strip().lower(), category.direction): category
        for category in queryset
    }


def _extract_row_value(*, row: dict, key: str) -> str:
    value = row.get(key)
    if value is None:
        return ""
    return str(value).strip()


def _parse_csv_row(
    *,
    owner,
    row: dict,
    line_number: int,
    account_by_name: dict[str, PersonalAccount],
    category_by_name_direction: dict[tuple[str, str], PersonalCategory],
) -> dict:
    entry_date_raw = _extract_row_value(row=row, key="entry_date")
    direction = _extract_row_value(row=row, key="direction").upper()
    amount_raw = _extract_row_value(row=row, key="amount")
    account_name = _extract_row_value(row=row, key="account").lower()
    category_name = _extract_row_value(row=row, key="category").lower()
    description = _extract_row_value(row=row, key="description")
    metadata_raw = _extract_row_value(row=row, key="metadata")

    try:
        entry_date = date.fromisoformat(entry_date_raw)
    except ValueError as exc:
        raise ValidationError(
            f"Linha {line_number}: entry_date deve estar em YYYY-MM-DD."
        ) from exc

    if direction not in PersonalDirection.values:
        raise ValidationError(f"Linha {line_number}: direction deve ser IN ou OUT.")

    try:
        amount = _quantize_money(Decimal(amount_raw))
    except Exception as exc:  # noqa: BLE001
        raise ValidationError(f"Linha {line_number}: amount invalido.") from exc

    if amount <= 0:
        raise ValidationError(f"Linha {line_number}: amount deve ser maior que zero.")

    account = account_by_name.get(account_name)
    if account is None:
        raise ValidationError(
            f"Linha {line_number}: conta '{row.get('account')}' nao encontrada."
        )

    category = category_by_name_direction.get((category_name, direction))
    if category is None:
        raise ValidationError(
            f"Linha {line_number}: categoria '{row.get('category')}' "
            f"com direction '{direction}' nao encontrada."
        )

    metadata: dict = {}
    if metadata_raw:
        try:
            loaded_metadata = json.loads(metadata_raw)
        except json.JSONDecodeError as exc:
            raise ValidationError(
                f"Linha {line_number}: metadata deve ser JSON valido."
            ) from exc

        if not isinstance(loaded_metadata, dict):
            raise ValidationError(
                f"Linha {line_number}: metadata deve ser objeto JSON."
            )
        metadata = loaded_metadata

    import_hash = _build_import_hash(
        owner_id=owner.id,
        account_id=account.id,
        category_id=category.id,
        direction=direction,
        amount=amount,
        entry_date=entry_date,
        description=description,
        metadata=metadata,
    )

    return {
        "entry_date": entry_date.isoformat(),
        "direction": direction,
        "amount": f"{amount:.2f}",
        "account_id": account.id,
        "category_id": category.id,
        "description": description,
        "metadata": metadata,
        "import_hash": import_hash,
    }


@transaction.atomic
def preview_personal_import_csv(
    *,
    owner,
    csv_content: str,
    source_filename: str,
    delimiter: str = ",",
) -> PersonalImportJob:
    if not csv_content.strip():
        raise ValidationError("Arquivo CSV vazio.")

    if len(delimiter) != 1:
        raise ValidationError("delimiter deve ter exatamente um caractere.")

    csv_file = io.StringIO(csv_content)
    reader = csv.DictReader(csv_file, delimiter=delimiter)

    if not reader.fieldnames:
        raise ValidationError("CSV sem cabecalho.")

    normalized_headers = {field.strip() for field in reader.fieldnames if field}
    missing_headers = sorted(CSV_REQUIRED_HEADERS - normalized_headers)
    if missing_headers:
        raise ValidationError(
            "CSV sem colunas obrigatorias: " + ", ".join(missing_headers)
        )

    account_by_name = _build_account_name_map(owner=owner)
    category_by_name_direction = _build_category_name_map(owner=owner)

    preview_rows: list[dict] = []
    error_rows: list[dict] = []
    rows_total = 0

    for line_number, row in enumerate(reader, start=2):
        if row is None:
            continue
        is_empty_row = all(not _extract_row_value(row=row, key=key) for key in row)
        if is_empty_row:
            continue

        rows_total += 1

        try:
            parsed_row = _parse_csv_row(
                owner=owner,
                row=row,
                line_number=line_number,
                account_by_name=account_by_name,
                category_by_name_direction=category_by_name_direction,
            )
            preview_rows.append(parsed_row)
        except ValidationError as exc:
            error_rows.append(
                {
                    "line_number": line_number,
                    "detail": exc.messages[0] if exc.messages else str(exc),
                    "raw_row": {key: (value or "") for key, value in row.items()},
                }
            )

    rows_valid = len(preview_rows)
    rows_invalid = len(error_rows)

    summary = {
        "rows_total": rows_total,
        "rows_valid": rows_valid,
        "rows_invalid": rows_invalid,
        "ready_to_confirm": rows_valid > 0,
    }

    return PersonalImportJob.objects.create(
        owner=owner,
        status=PersonalImportStatus.PREVIEWED,
        source_filename=source_filename,
        delimiter=delimiter,
        preview_rows=preview_rows,
        error_rows=error_rows,
        summary=summary,
        rows_total=rows_total,
        rows_valid=rows_valid,
        rows_invalid=rows_invalid,
    )


@transaction.atomic
def confirm_personal_import_job(*, owner, import_job: PersonalImportJob) -> dict:
    _ensure_owner(
        resource_name="Importacao CSV pessoal",
        resource_owner_id=import_job.owner_id,
        user_id=owner.id,
    )

    if import_job.status == PersonalImportStatus.CONFIRMED:
        return {
            "job_id": import_job.id,
            "status": import_job.status,
            "imported_count": import_job.imported_count,
            "skipped_count": import_job.skipped_count,
        }

    preview_rows = list(import_job.preview_rows)
    if not preview_rows:
        raise ValidationError("Nenhuma linha valida para confirmar importacao.")

    account_ids = {int(row["account_id"]) for row in preview_rows}
    category_ids = {int(row["category_id"]) for row in preview_rows}

    account_by_id = {
        account.id: account
        for account in PersonalAccount.objects.filter(owner=owner, id__in=account_ids)
    }
    category_by_id = {
        category.id: category
        for category in PersonalCategory.objects.filter(
            owner=owner,
            id__in=category_ids,
        )
    }

    imported_count = 0
    skipped_count = 0
    runtime_errors: list[dict] = []

    for row in preview_rows:
        account = account_by_id.get(int(row["account_id"]))
        category = category_by_id.get(int(row["category_id"]))

        if account is None or category is None:
            skipped_count += 1
            runtime_errors.append(
                {
                    "import_hash": row.get("import_hash"),
                    "detail": (
                        "Conta ou categoria nao encontrada no momento da confirmacao."
                    ),
                }
            )
            continue

        entry_date = date.fromisoformat(row["entry_date"])
        amount = _quantize_money(Decimal(row["amount"]))
        import_hash = row["import_hash"]

        _, created = PersonalEntry.objects.get_or_create(
            owner=owner,
            import_hash=import_hash,
            defaults={
                "account": account,
                "category": category,
                "direction": row["direction"],
                "amount": amount,
                "entry_date": entry_date,
                "description": row.get("description", ""),
                "metadata": {
                    **row.get("metadata", {}),
                    "source": "csv_import",
                    "import_job_id": import_job.id,
                },
                "import_job": import_job,
            },
        )

        if created:
            imported_count += 1
        else:
            skipped_count += 1

    import_job.status = PersonalImportStatus.CONFIRMED
    import_job.imported_count = imported_count
    import_job.skipped_count = skipped_count
    import_job.confirmed_at = timezone.now()
    import_job.summary = {
        **(import_job.summary or {}),
        "imported_count": imported_count,
        "skipped_count": skipped_count,
        "runtime_errors": runtime_errors,
    }
    import_job.save(
        update_fields=[
            "status",
            "imported_count",
            "skipped_count",
            "confirmed_at",
            "summary",
            "updated_at",
        ]
    )

    return {
        "job_id": import_job.id,
        "status": import_job.status,
        "imported_count": imported_count,
        "skipped_count": skipped_count,
    }


def validate_category_direction(direction: str) -> None:
    if direction not in PersonalDirection.values:
        raise ValidationError("direction invalido.")


@transaction.atomic
def record_personal_audit_log(
    *,
    owner,
    event_type: str,
    resource_type: str,
    resource_id: int | None = None,
    metadata: dict | None = None,
) -> PersonalAuditLog:
    if event_type not in PersonalAuditEvent.values:
        raise ValidationError("event_type invalido para auditoria pessoal.")

    return PersonalAuditLog.objects.create(
        owner=owner,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata=metadata or {},
    )


def build_personal_data_export(*, owner) -> dict:
    accounts = list(
        PersonalAccount.objects.filter(owner=owner)
        .order_by("name", "id")
        .values("id", "name", "type", "is_active", "created_at", "updated_at")
    )
    categories = list(
        PersonalCategory.objects.filter(owner=owner)
        .order_by("name", "id")
        .values("id", "name", "direction", "is_active", "created_at", "updated_at")
    )
    recurring_rules = list(
        PersonalRecurringRule.objects.filter(owner=owner)
        .order_by("next_run_date", "id")
        .values(
            "id",
            "account_id",
            "category_id",
            "direction",
            "amount",
            "description",
            "metadata",
            "frequency",
            "interval",
            "start_date",
            "end_date",
            "next_run_date",
            "is_active",
            "created_at",
            "updated_at",
        )
    )
    entries = list(
        PersonalEntry.objects.filter(owner=owner)
        .order_by("-entry_date", "-id")
        .values(
            "id",
            "account_id",
            "category_id",
            "recurring_rule_id",
            "import_job_id",
            "direction",
            "amount",
            "entry_date",
            "description",
            "metadata",
            "recurring_event_key",
            "import_hash",
            "created_at",
            "updated_at",
        )
    )
    budgets = list(
        PersonalBudget.objects.filter(owner=owner)
        .order_by("-month_ref", "-id")
        .values(
            "id",
            "category_id",
            "month_ref",
            "limit_amount",
            "created_at",
            "updated_at",
        )
    )
    import_jobs = list(
        PersonalImportJob.objects.filter(owner=owner)
        .order_by("-created_at", "-id")
        .values(
            "id",
            "status",
            "source_filename",
            "delimiter",
            "preview_rows",
            "error_rows",
            "summary",
            "rows_total",
            "rows_valid",
            "rows_invalid",
            "imported_count",
            "skipped_count",
            "confirmed_at",
            "created_at",
            "updated_at",
        )
    )
    audit_logs = list(
        PersonalAuditLog.objects.filter(owner=owner)
        .order_by("-created_at", "-id")
        .values(
            "id",
            "event_type",
            "resource_type",
            "resource_id",
            "metadata",
            "created_at",
        )
    )

    return {
        "owner": {
            "id": owner.id,
            "username": owner.username,
            "email": owner.email,
        },
        "generated_at": timezone.now().isoformat(),
        "retention_policy": {
            "audit_log_retention_days": PERSONAL_AUDIT_RETENTION_DAYS,
        },
        "data": {
            "accounts": accounts,
            "categories": categories,
            "recurring_rules": recurring_rules,
            "entries": entries,
            "budgets": budgets,
            "import_jobs": import_jobs,
            "audit_logs": audit_logs,
        },
    }


@transaction.atomic
def purge_personal_audit_logs(
    *,
    older_than_days: int = PERSONAL_AUDIT_RETENTION_DAYS,
) -> int:
    if older_than_days <= 0:
        raise ValidationError("older_than_days deve ser maior que zero.")

    cutoff = timezone.now() - timedelta(days=older_than_days)
    queryset = list_personal_audit_logs_older_than(cutoff=cutoff)
    deleted_count, _ = queryset.delete()
    return deleted_count
