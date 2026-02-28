from __future__ import annotations

from datetime import datetime, time

from django.db.models import Q, QuerySet
from django.utils import timezone

from .models import AdminActivityLog


def list_admin_activity_logs() -> QuerySet[AdminActivityLog]:
    return AdminActivityLog.objects.select_related("actor").order_by(
        "-created_at", "-id"
    )


def filter_admin_activity_logs(
    *,
    search: str = "",
    actor: str = "",
    channel: str = "",
    method: str = "",
    status: str = "",
    date_from: str = "",
    date_to: str = "",
) -> QuerySet[AdminActivityLog]:
    queryset = list_admin_activity_logs()

    normalized_search = str(search or "").strip()
    if normalized_search:
        queryset = queryset.filter(
            Q(actor_username__icontains=normalized_search)
            | Q(path__icontains=normalized_search)
            | Q(action_group__icontains=normalized_search)
            | Q(resource__icontains=normalized_search)
        )

    normalized_actor = str(actor or "").strip()
    if normalized_actor:
        queryset = queryset.filter(actor_username__icontains=normalized_actor)

    normalized_channel = str(channel or "").strip().lower()
    if normalized_channel:
        queryset = queryset.filter(channel=normalized_channel)

    normalized_method = str(method or "").strip().upper()
    if normalized_method:
        queryset = queryset.filter(method=normalized_method)

    normalized_status = str(status or "").strip()
    if normalized_status.isdigit():
        queryset = queryset.filter(http_status=int(normalized_status))

    normalized_date_from = str(date_from or "").strip()
    if normalized_date_from:
        parsed_from = _parse_date_start(normalized_date_from)
        if parsed_from is not None:
            queryset = queryset.filter(created_at__gte=parsed_from)

    normalized_date_to = str(date_to or "").strip()
    if normalized_date_to:
        parsed_to = _parse_date_end(normalized_date_to)
        if parsed_to is not None:
            queryset = queryset.filter(created_at__lte=parsed_to)

    return queryset


def _parse_date_start(raw_value: str):
    try:
        parsed = datetime.fromisoformat(raw_value)
    except ValueError:
        try:
            parsed = datetime.combine(
                datetime.strptime(raw_value, "%Y-%m-%d"), time.min
            )
        except ValueError:
            return None

    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _parse_date_end(raw_value: str):
    try:
        parsed = datetime.fromisoformat(raw_value)
    except ValueError:
        try:
            parsed = datetime.combine(
                datetime.strptime(raw_value, "%Y-%m-%d"), time.max
            )
        except ValueError:
            return None

    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed
