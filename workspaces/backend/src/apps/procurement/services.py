from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.catalog.selectors import get_menu_day_for_procurement
from apps.finance.services import create_ap_from_purchase
from apps.inventory.models import StockMovementType, StockReferenceType
from apps.inventory.selectors import get_stock_map_by_ingredient_ids
from apps.inventory.services import apply_stock_movement

from .models import (
    Purchase,
    PurchaseItem,
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseRequestStatus,
)

QTY_DECIMAL_PLACES = Decimal("0.001")
DEFAULT_MENU_MULTIPLIER = Decimal("1")


def _quantize_qty(value: Decimal) -> Decimal:
    return value.quantize(QTY_DECIMAL_PLACES, rounding=ROUND_HALF_UP)


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


def _resolve_recipe_unit(*, ingredient, recipe_unit: str | None) -> str:
    if recipe_unit and recipe_unit != ingredient.unit:
        raise ValidationError(
            f"Unidade incompativel para ingrediente '{ingredient.name}': "
            f"receita usa '{recipe_unit}' e ingrediente usa '{ingredient.unit}'. "
            "TODO: implementar conversao de unidades."
        )
    return recipe_unit or ingredient.unit


def _build_required_ingredient_map(menu_day) -> dict[int, dict]:
    required_map: dict[int, dict] = {}

    for menu_item in menu_day.items.all():
        multiplier = (
            Decimal(menu_item.available_qty)
            if menu_item.available_qty is not None
            else DEFAULT_MENU_MULTIPLIER
        )

        for dish_ingredient in menu_item.dish.dish_ingredients.all():
            ingredient = dish_ingredient.ingredient
            unit = _resolve_recipe_unit(
                ingredient=ingredient,
                recipe_unit=dish_ingredient.unit,
            )

            requirement = required_map.setdefault(
                ingredient.id,
                {
                    "ingredient": ingredient,
                    "unit": unit,
                    "needed_qty": Decimal("0"),
                },
            )
            if requirement["unit"] != unit:
                raise ValidationError(
                    f"Ingrediente '{ingredient.name}' possui unidades "
                    "diferentes nas receitas do cardapio. "
                    "TODO: implementar conversao de unidades."
                )

            requirement["needed_qty"] += dish_ingredient.quantity * multiplier

    return required_map


def _build_shortage_items(required_map: dict[int, dict]) -> list[dict]:
    stock_map = get_stock_map_by_ingredient_ids(required_map.keys())
    shortage_items: list[dict] = []

    sorted_ingredient_ids = sorted(
        required_map,
        key=lambda ingredient_id: required_map[ingredient_id]["ingredient"].name,
    )

    for ingredient_id in sorted_ingredient_ids:
        requirement = required_map[ingredient_id]
        ingredient = requirement["ingredient"]
        unit = requirement["unit"]
        needed_qty = _quantize_qty(requirement["needed_qty"])

        stock_item = stock_map.get(ingredient_id)
        if stock_item and stock_item.unit != unit:
            raise ValidationError(
                f"Unidade de estoque incompativel para ingrediente "
                f"'{ingredient.name}': estoque em '{stock_item.unit}' e "
                f"receita em '{unit}'. TODO: implementar conversao de unidades."
            )

        available_qty = stock_item.balance_qty if stock_item else Decimal("0")
        missing_qty = _quantize_qty(needed_qty - available_qty)

        if missing_qty > 0:
            shortage_items.append(
                {
                    "ingredient": ingredient,
                    "unit": unit,
                    "required_qty": missing_qty,
                }
            )

    return shortage_items


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


@transaction.atomic
def generate_purchase_request_from_menu(menu_day_id: int, requested_by=None) -> dict:
    menu_day = get_menu_day_for_procurement(menu_day_id)
    if menu_day is None:
        raise ValidationError("Cardapio informado nao foi encontrado.")

    required_map = _build_required_ingredient_map(menu_day)
    shortage_items = _build_shortage_items(required_map)

    if not shortage_items:
        return {
            "created": False,
            "purchase_request_id": None,
            "message": "sem compra necessaria",
            "items": [],
        }

    purchase_request = create_purchase_request(
        request_data={
            "status": PurchaseRequestStatus.OPEN,
            "note": (
                "Gerada automaticamente a partir do cardapio "
                f"{menu_day.menu_date.isoformat()}"
            ),
        },
        items_payload=shortage_items,
        requested_by=requested_by,
    )

    response_items = [
        {
            "ingredient_id": item["ingredient"].id,
            "ingredient_name": item["ingredient"].name,
            "required_qty": item["required_qty"],
            "unit": item["unit"],
        }
        for item in shortage_items
    ]

    return {
        "created": True,
        "purchase_request_id": purchase_request.id,
        "message": "purchase request gerada",
        "items": response_items,
    }


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

    create_ap_from_purchase(purchase.id)

    return (
        Purchase.objects.select_related("buyer")
        .prefetch_related("items__ingredient")
        .get(pk=purchase.pk)
    )
