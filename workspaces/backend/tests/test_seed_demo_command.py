from __future__ import annotations

import pytest
from django.core.management import call_command

from apps.catalog.models import Dish, Ingredient, MenuDay
from apps.finance.models import APBill, ARReceivable, CashMovement, LedgerEntry
from apps.ocr_ai.models import OCRJob
from apps.orders.models import Order, Payment
from apps.procurement.models import Purchase
from apps.production.models import ProductionBatch


@pytest.mark.django_db(transaction=True)
def test_seed_demo_command_e_idempotente(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"

    call_command("seed_demo")

    first_counts = {
        "ingredients": Ingredient.objects.count(),
        "dishes": Dish.objects.count(),
        "menu_days": MenuDay.objects.count(),
        "purchases": Purchase.objects.count(),
        "batches": ProductionBatch.objects.count(),
        "ocr_jobs": OCRJob.objects.count(),
        "orders": Order.objects.count(),
        "payments": Payment.objects.count(),
        "ap_bills": APBill.objects.count(),
        "ar_receivables": ARReceivable.objects.count(),
        "cash_movements": CashMovement.objects.count(),
        "ledger_entries": LedgerEntry.objects.count(),
    }

    assert first_counts["ingredients"] >= 10
    assert first_counts["dishes"] >= 6
    assert first_counts["menu_days"] >= 10
    assert first_counts["purchases"] >= 3
    assert first_counts["orders"] >= 5
    assert first_counts["ocr_jobs"] >= 3

    call_command("seed_demo")

    second_counts = {
        "ingredients": Ingredient.objects.count(),
        "dishes": Dish.objects.count(),
        "menu_days": MenuDay.objects.count(),
        "purchases": Purchase.objects.count(),
        "batches": ProductionBatch.objects.count(),
        "ocr_jobs": OCRJob.objects.count(),
        "orders": Order.objects.count(),
        "payments": Payment.objects.count(),
        "ap_bills": APBill.objects.count(),
        "ar_receivables": ARReceivable.objects.count(),
        "cash_movements": CashMovement.objects.count(),
        "ledger_entries": LedgerEntry.objects.count(),
    }

    assert second_counts == first_counts
