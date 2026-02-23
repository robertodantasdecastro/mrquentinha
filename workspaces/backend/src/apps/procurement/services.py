from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.inventory.models import StockMovementType, StockReferenceType
from apps.inventory.services import apply_stock_movement

from .models import (
    Purchase,
    PurchaseItem,
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseRequestStatus,
)


def _assert_unique_ingredient_payload(items_payload: list[dict]) -> None:
    ingredient_ids = [item["ingredient"].id for item in items_payload]
    if len(ingredient_ids) != len(set(ingredient_ids)):
        raise ValidationError("Ingrediente duplicado no payload de compra/solicitacao.")


def _assert_items_payload(items_payload: list[dict], qty_key: str) -> None:
    if not items_payload:
        raise ValidationError("Lista de itens nao pode ser vazia.")

    _assert_unique_ingredient_payload(items_payload)

    for item in items_payload:
        if item[qty_key] <= 0:
            raise ValidationError("Quantidade do item deve ser maior que zero.")


@transaction.atomic
def create_purchase_request(
    request_data: dict,
    items_payload: list[dict],
    *,
    requested_by=None,
) -> PurchaseRequest:
    _assert_items_payload(items_payload, qty_key="required_qty")

    purchase_request = PurchaseRequest.objects.create(
        requested_by=requested_by,
        status=request_data.get("status", PurchaseRequestStatus.OPEN),
        note=request_data.get("note"),
    )

    PurchaseRequestItem.objects.bulk_create(
        [
            PurchaseRequestItem(
                purchase_request=purchase_request,
                ingredient=item["ingredient"],
                required_qty=item["required_qty"],
                unit=item["unit"],
            )
            for item in items_payload
        ]
    )

    return PurchaseRequest.objects.prefetch_related("items__ingredient").get(
        pk=purchase_request.pk
    )


def _calculate_total_amount(items_payload: list[dict]) -> Decimal:
    total = Decimal("0")
    for item in items_payload:
        tax_amount = item.get("tax_amount") or Decimal("0")
        total += item["qty"] * item["unit_price"] + tax_amount

    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@transaction.atomic
def create_purchase_and_apply_stock(
    purchase_data: dict,
    items_payload: list[dict],
    *,
    buyer=None,
) -> Purchase:
    _assert_items_payload(items_payload, qty_key="qty")

    total_amount = _calculate_total_amount(items_payload)

    purchase = Purchase.objects.create(
        buyer=buyer,
        supplier_name=purchase_data["supplier_name"],
        invoice_number=purchase_data.get("invoice_number"),
        purchase_date=purchase_data["purchase_date"],
        total_amount=total_amount,
    )

    PurchaseItem.objects.bulk_create(
        [
            PurchaseItem(
                purchase=purchase,
                ingredient=item["ingredient"],
                qty=item["qty"],
                unit=item["unit"],
                unit_price=item["unit_price"],
                tax_amount=item.get("tax_amount"),
                expiry_date=item.get("expiry_date"),
            )
            for item in items_payload
        ]
    )

    for item in items_payload:
        apply_stock_movement(
            ingredient=item["ingredient"],
            movement_type=StockMovementType.IN,
            qty=item["qty"],
            unit=item["unit"],
            reference_type=StockReferenceType.PURCHASE,
            reference_id=purchase.id,
            note=f"Entrada por compra {purchase.invoice_number or purchase.id}",
            created_by=buyer,
        )

    return (
        Purchase.objects.select_related("buyer")
        .prefetch_related("items__ingredient")
        .get(pk=purchase.pk)
    )
