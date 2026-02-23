from django.db.models import QuerySet

from .models import Purchase, PurchaseRequest, PurchaseRequestStatus


def list_open_requests() -> QuerySet[PurchaseRequest]:
    return (
        PurchaseRequest.objects.filter(status=PurchaseRequestStatus.OPEN)
        .select_related("requested_by")
        .prefetch_related("items__ingredient")
        .order_by("-requested_at", "-id")
    )


def get_purchase_detail(purchase_id: int) -> Purchase | None:
    return (
        Purchase.objects.filter(pk=purchase_id)
        .select_related("buyer")
        .prefetch_related("items__ingredient")
        .first()
    )
