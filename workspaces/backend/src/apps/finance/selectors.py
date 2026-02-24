from datetime import date

from django.db.models import QuerySet

from .models import (
    Account,
    APBill,
    ARReceivable,
    BankStatement,
    CashMovement,
    LedgerEntry,
    StatementLine,
)


def list_accounts() -> QuerySet[Account]:
    return Account.objects.order_by("name")


def list_ap_bills() -> QuerySet[APBill]:
    return APBill.objects.select_related("account").order_by("due_date", "id")


def list_ar_receivables() -> QuerySet[ARReceivable]:
    return ARReceivable.objects.select_related("account", "customer").order_by(
        "due_date", "id"
    )


def list_bank_statements() -> QuerySet[BankStatement]:
    return BankStatement.objects.order_by("-period_start", "-id")


def list_statement_lines(statement_id: int) -> QuerySet[StatementLine]:
    return StatementLine.objects.filter(statement_id=statement_id).order_by(
        "line_date", "id"
    )


def list_all_statement_lines() -> QuerySet[StatementLine]:
    return StatementLine.objects.select_related("statement").order_by("line_date", "id")


def list_cash_movements() -> QuerySet[CashMovement]:
    return CashMovement.objects.select_related("account", "statement_line").order_by(
        "-movement_date", "-id"
    )


def list_unreconciled_movements(
    from_date: date, to_date: date
) -> QuerySet[CashMovement]:
    return (
        CashMovement.objects.select_related("account", "statement_line")
        .filter(
            movement_date__date__gte=from_date,
            movement_date__date__lte=to_date,
            is_reconciled=False,
        )
        .order_by("movement_date", "id")
    )


def list_ledger_entries() -> QuerySet[LedgerEntry]:
    return LedgerEntry.objects.select_related(
        "debit_account",
        "credit_account",
    ).order_by("-entry_date", "-id")


def get_ap_by_reference(reference_type: str, reference_id: int) -> APBill | None:
    return APBill.objects.filter(
        reference_type=reference_type,
        reference_id=reference_id,
    ).first()


def get_ar_by_reference(reference_type: str, reference_id: int) -> ARReceivable | None:
    return ARReceivable.objects.filter(
        reference_type=reference_type,
        reference_id=reference_id,
    ).first()


def get_cash_by_reference(
    *,
    direction: str,
    reference_type: str,
    reference_id: int,
) -> CashMovement | None:
    return CashMovement.objects.filter(
        direction=direction,
        reference_type=reference_type,
        reference_id=reference_id,
    ).first()
