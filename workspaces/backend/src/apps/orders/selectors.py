from datetime import date

from django.db.models import QuerySet

from apps.catalog.models import MenuDay

from .models import Order, Payment


def get_menu_day_for_delivery(delivery_date: date) -> MenuDay | None:
    return (
        MenuDay.objects.filter(menu_date=delivery_date)
        .prefetch_related("items__dish")
        .first()
    )


def list_orders() -> QuerySet[Order]:
    return (
        Order.objects.select_related("customer")
        .prefetch_related("items__menu_item__dish", "payments")
        .order_by("-order_date", "-id")
    )


def get_order_detail(order_id: int) -> Order | None:
    return list_orders().filter(pk=order_id).first()


def list_payments() -> QuerySet[Payment]:
    return Payment.objects.select_related("order", "order__customer").order_by(
        "-created_at", "-id"
    )
