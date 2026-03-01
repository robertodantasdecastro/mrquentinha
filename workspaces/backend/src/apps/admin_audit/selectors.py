from __future__ import annotations

import math
from datetime import datetime, time, timedelta

from django.db.models import Avg, Count, Q, QuerySet
from django.db.models.functions import TruncHour
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
    else:
        normalized_status_class = normalized_status.lower()
        if (
            len(normalized_status_class) == 3
            and normalized_status_class[0].isdigit()
            and normalized_status_class.endswith("xx")
        ):
            status_prefix = int(normalized_status_class[0])
            queryset = queryset.filter(
                http_status__gte=status_prefix * 100,
                http_status__lt=(status_prefix * 100) + 100,
            )

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


def build_admin_activity_overview(
    *,
    search: str = "",
    actor: str = "",
    channel: str = "",
    method: str = "",
    status: str = "",
    date_from: str = "",
    date_to: str = "",
) -> dict:
    queryset = filter_admin_activity_logs(
        search=search,
        actor=actor,
        channel=channel,
        method=method,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )
    return summarize_admin_activity_logs(queryset=queryset)


def summarize_admin_activity_logs(*, queryset: QuerySet[AdminActivityLog]) -> dict:
    total_events = queryset.count()
    now = timezone.now()

    aggregated = queryset.aggregate(
        success_count=Count(
            "id",
            filter=Q(http_status__gte=200, http_status__lt=400),
        ),
        client_error_count=Count(
            "id",
            filter=Q(http_status__gte=400, http_status__lt=500),
        ),
        server_error_count=Count("id", filter=Q(http_status__gte=500)),
        unauthorized_count=Count("id", filter=Q(http_status=401)),
        forbidden_count=Count("id", filter=Q(http_status=403)),
        anonymous_count=Count("id", filter=Q(actor_username="")),
        avg_duration_ms=Avg("duration_ms"),
        unique_actors=Count(
            "actor_username",
            distinct=True,
            filter=~Q(actor_username=""),
        ),
        unique_ips=Count(
            "ip_address",
            distinct=True,
            filter=Q(ip_address__isnull=False),
        ),
    )

    durations = list(
        queryset.order_by("duration_ms").values_list("duration_ms", flat=True)
    )
    p95_duration_ms = 0
    max_duration_ms = 0
    if durations:
        max_duration_ms = int(durations[-1])
        p95_index = max(
            0,
            min(
                len(durations) - 1,
                math.ceil(len(durations) * 0.95) - 1,
            ),
        )
        p95_duration_ms = int(durations[p95_index])

    by_method_rows = (
        queryset.values("method")
        .annotate(count=Count("id"))
        .order_by("-count", "method")[:8]
    )
    by_channel_rows = (
        queryset.values("channel")
        .annotate(count=Count("id"))
        .order_by("-count", "channel")[:8]
    )
    by_action_rows = (
        queryset.exclude(action_group="")
        .values("action_group")
        .annotate(count=Count("id"))
        .order_by("-count", "action_group")[:8]
    )
    top_actor_rows = (
        queryset.exclude(actor_username="")
        .values("actor_username")
        .annotate(count=Count("id"))
        .order_by("-count", "actor_username")[:10]
    )
    top_path_rows = (
        queryset.values("path")
        .annotate(count=Count("id"))
        .order_by("-count", "path")[:10]
    )

    current_hour = timezone.localtime(now).replace(minute=0, second=0, microsecond=0)
    start_hour = current_hour - timedelta(hours=23)
    hourly_rows = (
        queryset.filter(created_at__gte=start_hour)
        .annotate(hour=TruncHour("created_at"))
        .values("hour")
        .annotate(
            events=Count("id"),
            successes=Count("id", filter=Q(http_status__gte=200, http_status__lt=400)),
            errors=Count("id", filter=Q(http_status__gte=400)),
        )
        .order_by("hour")
    )
    hourly_map: dict[str, dict] = {}
    for row in hourly_rows:
        hour = row.get("hour")
        if hour is None:
            continue
        hour_key = (
            timezone.localtime(hour)
            .replace(minute=0, second=0, microsecond=0)
            .isoformat()
        )
        hourly_map[hour_key] = {
            "events": int(row.get("events", 0) or 0),
            "successes": int(row.get("successes", 0) or 0),
            "errors": int(row.get("errors", 0) or 0),
        }

    hourly_series: list[dict] = []
    for index in range(24):
        bucket = start_hour + timedelta(hours=index)
        bucket_key = bucket.isoformat()
        values = hourly_map.get(bucket_key, {"events": 0, "successes": 0, "errors": 0})
        hourly_series.append(
            {
                "hour": bucket_key,
                "events": values["events"],
                "successes": values["successes"],
                "errors": values["errors"],
            }
        )

    failed_rows = list(
        queryset.filter(http_status__gte=400)
        .values(
            "id",
            "request_id",
            "created_at",
            "actor_username",
            "channel",
            "method",
            "path",
            "http_status",
            "duration_ms",
            "action_group",
            "resource",
        )
        .order_by("-created_at", "-id")[:12]
    )
    failed_events = [
        {
            "id": int(item["id"]),
            "request_id": str(item["request_id"]),
            "created_at": timezone.localtime(item["created_at"]).isoformat(),
            "actor_username": str(item.get("actor_username") or ""),
            "channel": str(item.get("channel") or ""),
            "method": str(item.get("method") or ""),
            "path": str(item.get("path") or ""),
            "http_status": int(item.get("http_status") or 0),
            "duration_ms": int(item.get("duration_ms") or 0),
            "action_group": str(item.get("action_group") or ""),
            "resource": str(item.get("resource") or ""),
        }
        for item in failed_rows
    ]

    success_count = int(aggregated.get("success_count") or 0)
    client_error_count = int(aggregated.get("client_error_count") or 0)
    server_error_count = int(aggregated.get("server_error_count") or 0)
    error_count = client_error_count + server_error_count
    success_rate_percent = (
        round((success_count / total_events) * 100, 2) if total_events else 0.0
    )
    error_rate_percent = (
        round((error_count / total_events) * 100, 2) if total_events else 0.0
    )

    return {
        "generated_at": timezone.localtime(now).isoformat(),
        "totals": {
            "events": int(total_events),
            "success_count": success_count,
            "error_count": error_count,
            "client_error_count": client_error_count,
            "server_error_count": server_error_count,
            "success_rate_percent": success_rate_percent,
            "error_rate_percent": error_rate_percent,
            "avg_duration_ms": float(aggregated.get("avg_duration_ms") or 0.0),
            "p95_duration_ms": p95_duration_ms,
            "max_duration_ms": max_duration_ms,
            "unique_actors": int(aggregated.get("unique_actors") or 0),
            "unique_ips": int(aggregated.get("unique_ips") or 0),
        },
        "security": {
            "unauthorized_count": int(aggregated.get("unauthorized_count") or 0),
            "forbidden_count": int(aggregated.get("forbidden_count") or 0),
            "anonymous_count": int(aggregated.get("anonymous_count") or 0),
            "failed_events": failed_events,
        },
        "by_method": [
            {"key": str(row["method"]), "count": int(row["count"])}
            for row in by_method_rows
        ],
        "by_channel": [
            {"key": str(row["channel"]), "count": int(row["count"])}
            for row in by_channel_rows
        ],
        "by_action_group": [
            {"key": str(row["action_group"]), "count": int(row["count"])}
            for row in by_action_rows
        ],
        "top_actors": [
            {"key": str(row["actor_username"]), "count": int(row["count"])}
            for row in top_actor_rows
        ],
        "top_paths": [
            {"key": str(row["path"]), "count": int(row["count"])}
            for row in top_path_rows
        ],
        "hourly_series_last_24h": hourly_series,
    }


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
