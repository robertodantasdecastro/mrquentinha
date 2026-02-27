from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Count, Max, Q, QuerySet, Sum, Value
from django.db.models.functions import Coalesce

from apps.orders.models import OrderStatus

from .models import CustomerLgpdRequest
from .services import SystemRole


def list_customers_queryset() -> QuerySet:
    User = get_user_model()
    return (
        User.objects.filter(
            user_roles__role__code=SystemRole.CLIENTE,
            user_roles__role__is_active=True,
        )
        .distinct()
        .select_related("profile", "customer_governance")
        .prefetch_related("user_roles__role")
        .annotate(
            orders_count=Count("orders", distinct=True),
            orders_received_count=Count(
                "orders",
                filter=Q(orders__status=OrderStatus.RECEIVED),
                distinct=True,
            ),
            orders_total_amount=Coalesce(
                Sum("orders__total_amount"),
                Value(Decimal("0.00")),
            ),
            last_order_at=Max("orders__order_date"),
        )
        .order_by("-date_joined", "-id")
    )


def list_customer_lgpd_requests(*, customer_id: int) -> QuerySet[CustomerLgpdRequest]:
    return CustomerLgpdRequest.objects.filter(customer_id=customer_id).order_by(
        "-requested_at",
        "-id",
    )
