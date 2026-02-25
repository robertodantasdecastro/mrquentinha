from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.accounts.services import SystemRole
from apps.catalog.models import (
    Dish,
    DishIngredient,
    Ingredient,
    IngredientUnit,
    MenuDay,
    MenuItem,
)
from apps.finance.models import (
    AccountType,
    ARReceivable,
    ARReceivableStatus,
    CashDirection,
    CashMovement,
)
from apps.finance.services import create_ar_from_order
from apps.orders.models import OrderStatus, PaymentStatus
from apps.orders.services import (
    create_order,
    update_order_status,
    update_payment_status,
)


def _create_menu_item(
    *,
    menu_date: date,
    sale_price: Decimal,
    dish_name: str,
    ingredient_name: str,
) -> MenuItem:
    ingredient = Ingredient.objects.create(
        name=ingredient_name,
        unit=IngredientUnit.KILOGRAM,
    )
    dish = Dish.objects.create(name=dish_name, yield_portions=10)
    DishIngredient.objects.create(
        dish=dish,
        ingredient=ingredient,
        quantity=Decimal("1.000"),
        unit=IngredientUnit.KILOGRAM,
    )

    menu_day, _ = MenuDay.objects.get_or_create(
        menu_date=menu_date,
        defaults={"title": f"Cardapio {menu_date.isoformat()}"},
    )

    return MenuItem.objects.create(
        menu_day=menu_day,
        dish=dish,
        sale_price=sale_price,
        is_active=True,
    )


@pytest.mark.django_db
def test_create_order_calcula_total_e_snapshot_unit_price():
    delivery_date = date(2026, 3, 5)
    menu_item_1 = _create_menu_item(
        menu_date=delivery_date,
        sale_price=Decimal("20.00"),
        dish_name="Prato Arroz",
        ingredient_name="Ingrediente Arroz",
    )
    menu_item_2 = _create_menu_item(
        menu_date=delivery_date,
        sale_price=Decimal("15.50"),
        dish_name="Prato Feijao",
        ingredient_name="Ingrediente Feijao",
    )

    order = create_order(
        customer=None,
        delivery_date=delivery_date,
        items_payload=[
            {"menu_item": menu_item_1, "qty": 2},
            {"menu_item": menu_item_2, "qty": 1},
        ],
    )

    assert order.total_amount == Decimal("55.50")
    assert order.status == OrderStatus.CREATED

    order_item = order.items.get(menu_item=menu_item_1)
    assert order_item.unit_price == Decimal("20.00")

    menu_item_1.sale_price = Decimal("30.00")
    menu_item_1.save(update_fields=["sale_price"])
    order_item.refresh_from_db()
    assert order_item.unit_price == Decimal("20.00")

    payment = order.payments.get()
    assert payment.status == PaymentStatus.PENDING
    assert payment.amount == Decimal("55.50")


@pytest.mark.django_db
def test_create_order_cria_ar_automaticamente_e_idempotente_por_referencia():
    delivery_date = date(2026, 3, 6)
    menu_item = _create_menu_item(
        menu_date=delivery_date,
        sale_price=Decimal("18.00"),
        dish_name="Prato AR",
        ingredient_name="Ingrediente AR",
    )

    order = create_order(
        customer=None,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 2}],
    )

    receivable = ARReceivable.objects.get(
        reference_type="ORDER",
        reference_id=order.id,
    )
    assert receivable.amount == Decimal("36.00")
    assert receivable.due_date == delivery_date
    assert receivable.status == ARReceivableStatus.OPEN
    assert receivable.account.name == "Vendas"
    assert receivable.account.type == AccountType.REVENUE

    receivable_second = create_ar_from_order(order.id)
    assert receivable_second.id == receivable.id
    assert (
        ARReceivable.objects.filter(
            reference_type="ORDER",
            reference_id=order.id,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_update_payment_status_paid_recebe_ar_e_cria_caixa_sem_duplicar():
    delivery_date = date(2026, 3, 7)
    menu_item = _create_menu_item(
        menu_date=delivery_date,
        sale_price=Decimal("22.00"),
        dish_name="Prato Caixa",
        ingredient_name="Ingrediente Caixa",
    )

    order = create_order(
        customer=None,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 2}],
    )
    payment = order.payments.get()

    updated_payment = update_payment_status(
        payment_id=payment.id,
        update_data={"status": PaymentStatus.PAID, "provider_ref": "pix-001"},
    )

    assert updated_payment.status == PaymentStatus.PAID
    assert updated_payment.paid_at is not None

    receivable = ARReceivable.objects.get(
        reference_type="ORDER",
        reference_id=order.id,
    )
    assert receivable.status == ARReceivableStatus.RECEIVED
    assert receivable.received_at is not None

    movements = CashMovement.objects.filter(
        direction=CashDirection.IN,
        reference_type="AR",
        reference_id=receivable.id,
    )
    assert movements.count() == 1

    movement = movements.get()
    assert movement.amount == order.total_amount
    assert movement.account.name == "Caixa/Banco"
    assert movement.account.type == AccountType.ASSET

    update_payment_status(
        payment_id=payment.id,
        update_data={"status": PaymentStatus.PAID},
    )

    assert (
        CashMovement.objects.filter(
            direction=CashDirection.IN,
            reference_type="AR",
            reference_id=receivable.id,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_create_order_bloqueia_menu_item_de_outra_data():
    requested_date = date(2026, 3, 6)
    other_date = date(2026, 3, 7)

    MenuDay.objects.create(menu_date=requested_date, title="Cardapio Solicitado")

    menu_item = _create_menu_item(
        menu_date=other_date,
        sale_price=Decimal("25.00"),
        dish_name="Prato Outra Data",
        ingredient_name="Ingrediente Outra Data",
    )

    with pytest.raises(ValidationError):
        create_order(
            customer=None,
            delivery_date=requested_date,
            items_payload=[{"menu_item": menu_item, "qty": 1}],
        )


@pytest.mark.django_db
def test_update_order_status_transicao_invalida_falha():
    delivery_date = date(2026, 3, 8)
    menu_item = _create_menu_item(
        menu_date=delivery_date,
        sale_price=Decimal("21.00"),
        dish_name="Prato Status",
        ingredient_name="Ingrediente Status",
    )
    order = create_order(
        customer=None,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )

    with pytest.raises(ValidationError):
        update_order_status(order_id=order.id, new_status=OrderStatus.DELIVERED)


@pytest.mark.django_db
def test_update_order_status_bloqueia_usuario_nao_dono(create_user_with_roles):
    delivery_date = date(2026, 3, 13)
    menu_item = _create_menu_item(
        menu_date=delivery_date,
        sale_price=Decimal("18.00"),
        dish_name="Prato Ownership",
        ingredient_name="Ingrediente Ownership",
    )

    owner = create_user_with_roles(
        username="owner_service", role_codes=[SystemRole.CLIENTE]
    )
    other = create_user_with_roles(
        username="other_service", role_codes=[SystemRole.CLIENTE]
    )

    order = create_order(
        customer=owner,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )

    with pytest.raises(ValidationError, match="Pedido nao encontrado"):
        update_order_status(
            order_id=order.id,
            new_status=OrderStatus.CANCELED,
            actor_user=other,
        )


@pytest.mark.django_db
def test_update_payment_status_bloqueia_usuario_nao_dono(create_user_with_roles):
    delivery_date = date(2026, 3, 14)
    menu_item = _create_menu_item(
        menu_date=delivery_date,
        sale_price=Decimal("18.00"),
        dish_name="Prato Payment Ownership",
        ingredient_name="Ingrediente Payment Ownership",
    )

    owner = create_user_with_roles(
        username="owner_payment", role_codes=[SystemRole.CLIENTE]
    )
    other = create_user_with_roles(
        username="other_payment", role_codes=[SystemRole.CLIENTE]
    )

    order = create_order(
        customer=owner,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )
    payment = order.payments.get()

    with pytest.raises(ValidationError, match="Pagamento nao encontrado"):
        update_payment_status(
            payment_id=payment.id,
            update_data={"status": PaymentStatus.PAID},
            actor_user=other,
        )


@pytest.mark.django_db
def test_update_order_status_permite_papel_gestao_em_pedido_de_terceiro(
    create_user_with_roles,
):
    delivery_date = date(2026, 3, 15)
    menu_item = _create_menu_item(
        menu_date=delivery_date,
        sale_price=Decimal("18.00"),
        dish_name="Prato Management Status",
        ingredient_name="Ingrediente Management Status",
    )

    owner = create_user_with_roles(
        username="owner_management_status", role_codes=[SystemRole.CLIENTE]
    )
    financeiro = create_user_with_roles(
        username="financeiro_management_status",
        role_codes=[SystemRole.FINANCEIRO],
        is_staff=False,
    )

    order = create_order(
        customer=owner,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )

    updated_order = update_order_status(
        order_id=order.id,
        new_status=OrderStatus.CANCELED,
        actor_user=financeiro,
    )

    assert updated_order.status == OrderStatus.CANCELED


@pytest.mark.django_db
def test_update_payment_status_permite_papel_gestao_em_pagamento_de_terceiro(
    create_user_with_roles,
):
    delivery_date = date(2026, 3, 16)
    menu_item = _create_menu_item(
        menu_date=delivery_date,
        sale_price=Decimal("18.00"),
        dish_name="Prato Management Payment",
        ingredient_name="Ingrediente Management Payment",
    )

    owner = create_user_with_roles(
        username="owner_management_payment", role_codes=[SystemRole.CLIENTE]
    )
    financeiro = create_user_with_roles(
        username="financeiro_management_payment",
        role_codes=[SystemRole.FINANCEIRO],
        is_staff=False,
    )

    order = create_order(
        customer=owner,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )
    payment = order.payments.get()

    updated_payment = update_payment_status(
        payment_id=payment.id,
        update_data={"status": PaymentStatus.PAID},
        actor_user=financeiro,
    )

    assert updated_payment.status == PaymentStatus.PAID


@pytest.mark.django_db
def test_create_or_get_payment_intent_replay_idempotente():
    from apps.orders.models import PaymentIntentStatus
    from apps.orders.services import create_or_get_payment_intent

    delivery_date = date(2026, 3, 18)
    menu_item = _create_menu_item(
        menu_date=delivery_date,
        sale_price=Decimal("19.00"),
        dish_name="Prato Intent Replay",
        ingredient_name="Ingrediente Intent Replay",
    )

    order = create_order(
        customer=None,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )
    payment = order.payments.get()

    intent_1, created_1 = create_or_get_payment_intent(
        payment_id=payment.id,
        idempotency_key="intent-replay-001",
    )
    intent_2, created_2 = create_or_get_payment_intent(
        payment_id=payment.id,
        idempotency_key="intent-replay-001",
    )

    assert created_1 is True
    assert created_2 is False
    assert intent_1.id == intent_2.id
    assert intent_1.status == PaymentIntentStatus.REQUIRES_ACTION


@pytest.mark.django_db
def test_create_or_get_payment_intent_bloqueia_segundo_intent_ativo_com_outra_chave():
    from apps.orders.services import (
        PaymentIntentConflictError,
        create_or_get_payment_intent,
    )

    delivery_date = date(2026, 3, 19)
    menu_item = _create_menu_item(
        menu_date=delivery_date,
        sale_price=Decimal("17.00"),
        dish_name="Prato Intent Conflito",
        ingredient_name="Ingrediente Intent Conflito",
    )

    order = create_order(
        customer=None,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )
    payment = order.payments.get()

    create_or_get_payment_intent(
        payment_id=payment.id,
        idempotency_key="intent-conflito-001",
    )

    with pytest.raises(PaymentIntentConflictError, match="intent ativo"):
        create_or_get_payment_intent(
            payment_id=payment.id,
            idempotency_key="intent-conflito-002",
        )


@pytest.mark.django_db
def test_create_or_get_payment_intent_bloqueia_pagamento_ja_pago():
    from apps.orders.services import (
        PaymentIntentConflictError,
        create_or_get_payment_intent,
    )

    delivery_date = date(2026, 3, 20)
    menu_item = _create_menu_item(
        menu_date=delivery_date,
        sale_price=Decimal("20.00"),
        dish_name="Prato Intent Pago",
        ingredient_name="Ingrediente Intent Pago",
    )

    order = create_order(
        customer=None,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )
    payment = order.payments.get()
    payment.status = PaymentStatus.PAID
    payment.save(update_fields=["status"])

    with pytest.raises(PaymentIntentConflictError, match="Pagamento ja confirmado"):
        create_or_get_payment_intent(
            payment_id=payment.id,
            idempotency_key="intent-paid-001",
        )


@pytest.mark.django_db
def test_create_or_get_payment_intent_bloqueia_metodo_cash():
    from apps.orders.models import PaymentMethod
    from apps.orders.services import create_or_get_payment_intent

    delivery_date = date(2026, 3, 21)
    menu_item = _create_menu_item(
        menu_date=delivery_date,
        sale_price=Decimal("21.00"),
        dish_name="Prato Intent Cash",
        ingredient_name="Ingrediente Intent Cash",
    )

    order = create_order(
        customer=None,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )
    payment = order.payments.get()
    payment.method = PaymentMethod.CASH
    payment.save(update_fields=["method"])

    with pytest.raises(ValidationError, match="nao suporta intent online"):
        create_or_get_payment_intent(
            payment_id=payment.id,
            idempotency_key="intent-cash-001",
        )
