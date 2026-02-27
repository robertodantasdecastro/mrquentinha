import os
import shutil
import socket
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Sum
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import (
    MANAGEMENT_ROLES,
    ORDER_CREATE_ROLES,
    ORDER_READ_ROLES,
    ORDER_STATUS_UPDATE_ROLES,
    PAYMENT_READ_ROLES,
    PAYMENT_WRITE_ROLES,
    RoleMatrixPermission,
)
from apps.accounts.services import SystemRole
from apps.catalog.models import MenuDay
from apps.common.csv_export import build_csv_response
from apps.common.reports import parse_period
from apps.portal.services import get_payment_providers_config
from apps.procurement.models import Purchase, PurchaseRequest, PurchaseRequestStatus
from apps.production.models import ProductionBatch, ProductionBatchStatus

from .models import (
    Order,
    OrderStatus,
    Payment,
    PaymentIntent,
    PaymentIntentStatus,
    PaymentStatus,
    PaymentWebhookEvent,
)
from .payment_providers import (
    fetch_mercadopago_payment_details,
    map_asaas_status_to_intent,
    map_mercadopago_status_to_intent,
)
from .selectors import list_orders, list_orders_by_period, list_payments
from .serializers import (
    OrderSerializer,
    OrderStatusUpdateSerializer,
    PaymentIntentSerializer,
    PaymentSerializer,
    PaymentStatusUpdateSerializer,
    PaymentWebhookEventSerializer,
    PaymentWebhookInputSerializer,
)
from .services import (
    PaymentIntentConflictError,
    create_or_get_payment_intent,
    create_order,
    get_latest_payment_intent,
    has_global_order_access,
    normalize_idempotency_key,
    process_payment_webhook,
    update_order_status,
    update_payment_status,
)


class PaymentWebhookAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        expected_token = getattr(settings, "PAYMENTS_WEBHOOK_TOKEN", "")
        received_token = request.headers.get("X-Webhook-Token", "")
        if not expected_token or received_token != expected_token:
            return Response(
                {"detail": "Webhook token invalido."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        input_serializer = PaymentWebhookInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            webhook_event, created = process_payment_webhook(
                provider=input_serializer.validated_data.get("provider"),
                event_id=input_serializer.validated_data["event_id"],
                provider_intent_ref=input_serializer.validated_data[
                    "provider_intent_ref"
                ],
                intent_status=input_serializer.validated_data["intent_status"],
                provider_ref=input_serializer.validated_data.get("provider_ref"),
                paid_at=input_serializer.validated_data.get("paid_at"),
                raw_payload=dict(request.data),
            )
        except DjangoValidationError as exc:
            detail = exc.messages[0] if exc.messages else str(exc)
            if "nao encontrado" in detail.lower():
                return Response(
                    {"detail": detail},
                    status=status.HTTP_404_NOT_FOUND,
                )

            raise DRFValidationError(exc.messages) from exc

        output_payload = PaymentWebhookEventSerializer(webhook_event).data
        output_payload["idempotent_replay"] = not created

        return Response(
            output_payload,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


def _resolve_intent_status_from_generic(raw_status: str) -> str:
    normalized = (raw_status or "").strip().upper()
    if normalized in {"PAID", "SUCCEEDED", "CONFIRMED", "APPROVED"}:
        return "SUCCEEDED"
    if normalized in {"FAILED", "CANCELED", "CANCELLED", "REFUNDED"}:
        return "FAILED"
    if normalized in {"PENDING", "PROCESSING", "WAITING"}:
        return "PROCESSING"
    return "REQUIRES_ACTION"


def _resolve_client_channel_from_request(request) -> str:
    raw_channel = (
        request.headers.get("X-Client-Channel")
        or request.headers.get("X-Frontend-Channel")
        or "WEB"
    )
    normalized = str(raw_channel).strip().upper()
    if normalized in {"WEB", "MOBILE"}:
        return normalized
    return "WEB"


class MercadoPagoWebhookAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        expected_token = getattr(settings, "PAYMENTS_WEBHOOK_TOKEN", "")
        received_token = request.headers.get("X-Webhook-Token", "")
        if not expected_token or received_token != expected_token:
            return Response(
                {"detail": "Webhook token invalido."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        payload = dict(request.data)
        data = payload.get("data")
        payment_id = ""
        if isinstance(data, dict):
            payment_id = str(data.get("id", "")).strip()
        payment_id = payment_id or str(payload.get("id", "")).strip()
        if not payment_id:
            raise DRFValidationError(["Campo data.id (payment id) obrigatorio."])

        details = fetch_mercadopago_payment_details(payment_id)
        event_id = str(payload.get("id", "")).strip() or f"mp-{payment_id}"
        provider_ref = str(details.get("id", "")).strip() or payment_id
        paid_at_raw = str(details.get("date_approved", "")).strip()
        paid_at = parse_datetime(paid_at_raw) if paid_at_raw else None

        webhook_event, created = process_payment_webhook(
            provider="mercadopago",
            event_id=event_id,
            provider_intent_ref=payment_id,
            intent_status=map_mercadopago_status_to_intent(
                str(details.get("status", "pending"))
            ),
            provider_ref=provider_ref,
            paid_at=paid_at,
            raw_payload=payload,
        )
        output_payload = PaymentWebhookEventSerializer(webhook_event).data
        output_payload["idempotent_replay"] = not created
        return Response(
            output_payload,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class AsaasWebhookAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        expected_token = getattr(settings, "PAYMENTS_WEBHOOK_TOKEN", "")
        received_token = request.headers.get("X-Webhook-Token", "")
        if not expected_token or received_token != expected_token:
            return Response(
                {"detail": "Webhook token invalido."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        payload = dict(request.data)
        payment_data = payload.get("payment")
        if not isinstance(payment_data, dict):
            raise DRFValidationError(["Campo payment obrigatorio."])

        payment_id = str(payment_data.get("id", "")).strip()
        if not payment_id:
            raise DRFValidationError(["Campo payment.id obrigatorio."])

        event_id = (
            str(payload.get("id", "")).strip() or str(payload.get("event", "")).strip()
        )
        event_id = event_id or f"asaas-{payment_id}"
        payment_status = str(payment_data.get("status", "PENDING")).strip()
        provider_ref = (
            str(payment_data.get("externalReference", "")).strip()
            or str(payment_data.get("invoiceNumber", "")).strip()
            or payment_id
        )
        paid_at_raw = str(payment_data.get("paymentDate", "")).strip()
        paid_at = parse_datetime(f"{paid_at_raw}T00:00:00") if paid_at_raw else None
        if paid_at is not None and timezone.is_naive(paid_at):
            paid_at = timezone.make_aware(paid_at, timezone.get_current_timezone())

        webhook_event, created = process_payment_webhook(
            provider="asaas",
            event_id=event_id,
            provider_intent_ref=payment_id,
            intent_status=map_asaas_status_to_intent(payment_status),
            provider_ref=provider_ref,
            paid_at=paid_at,
            raw_payload=payload,
        )
        output_payload = PaymentWebhookEventSerializer(webhook_event).data
        output_payload["idempotent_replay"] = not created
        return Response(
            output_payload,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class EfiWebhookAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        expected_token = getattr(settings, "PAYMENTS_WEBHOOK_TOKEN", "")
        received_token = request.headers.get("X-Webhook-Token", "")
        if not expected_token or received_token != expected_token:
            return Response(
                {"detail": "Webhook token invalido."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        payload = dict(request.data)
        event_id = (
            str(payload.get("event_id", "")).strip()
            or str(payload.get("id", "")).strip()
        )
        provider_intent_ref = str(payload.get("provider_intent_ref", "")).strip()
        status_raw = str(payload.get("status", "")).strip()
        provider_ref = (
            str(payload.get("provider_ref", "")).strip() or provider_intent_ref
        )
        if not event_id or not provider_intent_ref:
            required_fields_message = (
                "Campos event_id e provider_intent_ref "
                "sao obrigatorios para webhook Efi."
            )
            raise DRFValidationError([required_fields_message])

        webhook_event, created = process_payment_webhook(
            provider="efi",
            event_id=event_id,
            provider_intent_ref=provider_intent_ref,
            intent_status=_resolve_intent_status_from_generic(status_raw),
            provider_ref=provider_ref,
            raw_payload=payload,
        )
        output_payload = PaymentWebhookEventSerializer(webhook_event).data
        output_payload["idempotent_replay"] = not created
        return Response(
            output_payload,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = OrderSerializer
    permission_classes = [RoleMatrixPermission]
    required_roles_by_action = {
        "create": ORDER_CREATE_ROLES,
        "list": ORDER_READ_ROLES,
        "retrieve": ORDER_READ_ROLES,
        "status": (*ORDER_STATUS_UPDATE_ROLES, SystemRole.CLIENTE),
        "confirm_receipt": (*ORDER_STATUS_UPDATE_ROLES, SystemRole.CLIENTE),
    }

    def get_queryset(self):
        queryset = list_orders()
        user = self.request.user

        if has_global_order_access(user):
            return queryset

        return queryset.filter(customer=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer = request.user if request.user.is_authenticated else None
        items_payload = serializer.validated_data.get("items", [])

        try:
            order = create_order(
                customer=customer,
                delivery_date=serializer.validated_data["delivery_date"],
                items_payload=items_payload,
                payment_method=serializer.validated_data.get("payment_method"),
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(order)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="status")
    def status(self, request, pk=None):
        order = self.get_object()

        input_serializer = OrderStatusUpdateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            updated_order = update_order_status(
                order_id=order.id,
                new_status=input_serializer.validated_data["status"],
                actor_user=request.user,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(updated_order)
        return Response(output.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="confirm-receipt")
    def confirm_receipt(self, request, pk=None):
        order = self.get_object()

        try:
            updated_order = update_order_status(
                order_id=order.id,
                new_status=OrderStatus.RECEIVED,
                actor_user=request.user,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(updated_order)
        return Response(output.data, status=status.HTTP_200_OK)


class PaymentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [RoleMatrixPermission]
    required_roles_by_action = {
        "list": PAYMENT_READ_ROLES,
        "retrieve": PAYMENT_READ_ROLES,
        "update": (*PAYMENT_WRITE_ROLES, SystemRole.CLIENTE),
        "partial_update": (*PAYMENT_WRITE_ROLES, SystemRole.CLIENTE),
        "intent": (*PAYMENT_WRITE_ROLES, SystemRole.CLIENTE),
        "intent_latest": PAYMENT_READ_ROLES,
    }

    def get_queryset(self):
        queryset = list_payments()
        user = self.request.user

        if has_global_order_access(user):
            return queryset

        return queryset.filter(order__customer=user)

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return PaymentStatusUpdateSerializer
        return PaymentSerializer

    def update(self, request, *args, **kwargs):
        return self._update_payment(request, partial=False)

    def partial_update(self, request, *args, **kwargs):
        return self._update_payment(request, partial=True)

    def _update_payment(self, request, *, partial: bool) -> Response:
        payment = self.get_object()
        serializer = self.get_serializer(payment, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            updated_payment = update_payment_status(
                payment_id=payment.id,
                update_data=serializer.validated_data,
                actor_user=request.user,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = PaymentSerializer(updated_payment)
        return Response(output.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="intent")
    def intent(self, request, pk=None):
        payment = self.get_object()

        try:
            idempotency_key = normalize_idempotency_key(
                request.headers.get("Idempotency-Key", "")
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        try:
            intent, created = create_or_get_payment_intent(
                payment_id=payment.id,
                idempotency_key=idempotency_key,
                source_channel=_resolve_client_channel_from_request(request),
                actor_user=request.user,
            )
        except PaymentIntentConflictError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        payload = PaymentIntentSerializer(intent).data
        payload["idempotent_replay"] = not created

        return Response(
            payload,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="intent/latest")
    def intent_latest(self, request, pk=None):
        payment = self.get_object()

        try:
            intent = get_latest_payment_intent(
                payment_id=payment.id,
                actor_user=request.user,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        if intent is None:
            return Response(
                {"detail": "Intent de pagamento nao encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        payload = PaymentIntentSerializer(intent)
        return Response(payload.data, status=status.HTTP_200_OK)


class OrdersExportAPIView(APIView):
    permission_classes = [RoleMatrixPermission]
    required_roles_by_method = {"GET": MANAGEMENT_ROLES}

    def get(self, request):
        from_date, to_date = parse_period(
            from_raw=request.query_params.get("from"),
            to_raw=request.query_params.get("to"),
        )
        orders = list_orders_by_period(from_date=from_date, to_date=to_date)

        header = [
            "pedido_id",
            "data_entrega",
            "status",
            "valor_total",
            "cliente_id",
            "cliente_nome",
            "metodos_pagamento",
            "total_pago",
        ]

        rows = []
        for order in orders:
            customer = order.customer
            customer_name = ""
            if customer:
                full_name = f"{customer.first_name} {customer.last_name}".strip()
                customer_name = full_name or customer.username

            payment_methods = sorted(
                {payment.method for payment in order.payments.all()}
            )
            paid_total = sum(
                (
                    payment.amount
                    for payment in order.payments.all()
                    if payment.status == PaymentStatus.PAID
                ),
                Decimal("0"),
            )

            rows.append(
                [
                    order.id,
                    order.delivery_date.isoformat(),
                    order.status,
                    f"{order.total_amount:.2f}",
                    customer.id if customer else "",
                    customer_name,
                    ";".join(payment_methods),
                    f"{paid_total:.2f}",
                ]
            )

        filename = f"pedidos_{from_date.isoformat()}_{to_date.isoformat()}.csv"
        return build_csv_response(filename=filename, header=header, rows=rows)


PROJECT_ROOT = Path(__file__).resolve().parents[6]
OPS_RUNTIME_DIR = PROJECT_ROOT / ".runtime" / "ops"
OPS_PID_DIR = OPS_RUNTIME_DIR / "pids"
SERVICE_MONITOR_SPECS = (
    {"key": "backend", "name": "Backend Django", "port": 8000},
    {"key": "admin", "name": "Admin Web", "port": 3002},
    {"key": "portal", "name": "Portal Web", "port": 3000},
    {"key": "client", "name": "Client Web", "port": 3001},
    {
        "key": "cloudflare",
        "name": "Cloudflare Tunnel",
        "port": None,
        "process_only": True,
    },
)


def _is_port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.25):
            return True
    except OSError:
        return False


def _read_pid_from_file(service_key: str) -> int | None:
    pid_file = OPS_PID_DIR / f"{service_key}.pid"
    if not pid_file.exists():
        return None

    try:
        pid = int(pid_file.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None

    try:
        os.kill(pid, 0)
        return pid
    except OSError:
        return None


def _read_server_memory_snapshot() -> dict[str, float]:
    mem_total_kb = 0.0
    mem_available_kb = 0.0

    try:
        with open("/proc/meminfo", encoding="utf-8") as meminfo_file:
            for line in meminfo_file:
                if line.startswith("MemTotal:"):
                    mem_total_kb = float(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_available_kb = float(line.split()[1])
    except OSError:
        return {
            "total_mb": 0.0,
            "available_mb": 0.0,
            "used_mb": 0.0,
            "used_percent": 0.0,
        }

    used_kb = max(mem_total_kb - mem_available_kb, 0.0)
    used_percent = (used_kb / mem_total_kb * 100.0) if mem_total_kb > 0 else 0.0
    return {
        "total_mb": round(mem_total_kb / 1024.0, 2),
        "available_mb": round(mem_available_kb / 1024.0, 2),
        "used_mb": round(used_kb / 1024.0, 2),
        "used_percent": round(used_percent, 2),
    }


def _read_server_uptime_seconds() -> float:
    try:
        with open("/proc/uptime", encoding="utf-8") as uptime_file:
            raw = uptime_file.read().strip().split()
            if not raw:
                return 0.0
            return round(float(raw[0]), 2)
    except OSError:
        return 0.0


def _read_process_rss_mb(pid: int | None) -> float | None:
    if pid is None:
        return None

    statm_path = Path("/proc") / str(pid) / "statm"
    try:
        content = statm_path.read_text(encoding="utf-8").strip().split()
        if len(content) < 2:
            return None
        resident_pages = int(content[1])
        page_size = os.sysconf("SC_PAGE_SIZE")
        rss_bytes = resident_pages * page_size
        return round(rss_bytes / (1024.0 * 1024.0), 2)
    except (OSError, ValueError):
        return None


def _read_process_uptime_seconds(pid: int | None) -> float | None:
    if pid is None:
        return None

    stat_path = Path("/proc") / str(pid) / "stat"
    try:
        content = stat_path.read_text(encoding="utf-8").strip().split()
        if len(content) < 22:
            return None
        start_ticks = int(content[21])
        clock_ticks = os.sysconf(os.sysconf_names["SC_CLK_TCK"])
        system_uptime = _read_server_uptime_seconds()
        process_uptime = system_uptime - (start_ticks / clock_ticks)
        return round(max(process_uptime, 0.0), 2)
    except (OSError, ValueError, KeyError):
        return None


def _build_service_monitor_payload() -> list[dict]:
    services_payload: list[dict] = []
    for service in SERVICE_MONITOR_SPECS:
        pid = _read_pid_from_file(service["key"])
        port = service.get("port")
        process_only = bool(service.get("process_only", False))
        port_open = bool(port and _is_port_open(int(port)))
        if process_only:
            status = "running" if pid else "offline"
            listener_ok = pid is not None
        else:
            status = "online" if port_open else ("running" if pid else "offline")
            listener_ok = port_open
        services_payload.append(
            {
                "key": service["key"],
                "name": service["name"],
                "port": port,
                "status": status,
                "pid": pid,
                "uptime_seconds": _read_process_uptime_seconds(pid),
                "rss_mb": _read_process_rss_mb(pid),
                "listener_ok": listener_ok,
            }
        )
    return services_payload


def _build_server_health_payload() -> dict:
    load_avg_1m, load_avg_5m, load_avg_15m = os.getloadavg()
    memory = _read_server_memory_snapshot()
    disk = shutil.disk_usage("/")
    disk_used = disk.total - disk.free
    disk_used_percent = (disk_used / disk.total * 100.0) if disk.total > 0 else 0.0
    return {
        "uptime_seconds": _read_server_uptime_seconds(),
        "cpu_count": os.cpu_count() or 0,
        "load_avg_1m": round(load_avg_1m, 3),
        "load_avg_5m": round(load_avg_5m, 3),
        "load_avg_15m": round(load_avg_15m, 3),
        "memory": memory,
        "disk": {
            "total_gb": round(disk.total / (1024.0**3), 2),
            "used_gb": round(disk_used / (1024.0**3), 2),
            "free_gb": round(disk.free / (1024.0**3), 2),
            "used_percent": round(disk_used_percent, 2),
        },
    }


def _build_payment_monitor_payload() -> dict:
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_15m = now - timedelta(minutes=15)
    payment_config_public = get_payment_providers_config(public=True)
    payment_providers = ("mercadopago", "efi", "asaas", "mock")

    lifecycle_counts = {
        "created": Order.objects.filter(status=OrderStatus.CREATED).count(),
        "confirmed": Order.objects.filter(status=OrderStatus.CONFIRMED).count(),
        "in_progress": Order.objects.filter(status=OrderStatus.IN_PROGRESS).count(),
        "out_for_delivery": Order.objects.filter(
            status=OrderStatus.OUT_FOR_DELIVERY
        ).count(),
        "delivered": Order.objects.filter(status=OrderStatus.DELIVERED).count(),
        "received": Order.objects.filter(status=OrderStatus.RECEIVED).count(),
        "canceled": Order.objects.filter(status=OrderStatus.CANCELED).count(),
    }

    provider_rows: list[dict] = []
    for provider_name in payment_providers:
        provider_cfg = payment_config_public.get(provider_name, {})
        intents_24h = PaymentIntent.objects.filter(
            provider=provider_name,
            created_at__gte=last_24h,
        ).count()
        webhooks_24h_qs = PaymentWebhookEvent.objects.filter(
            provider=provider_name,
            created_at__gte=last_24h,
        )
        webhooks_24h = webhooks_24h_qs.count()
        succeeded_24h = webhooks_24h_qs.filter(
            intent_status=PaymentIntentStatus.SUCCEEDED
        ).count()
        failed_24h = webhooks_24h_qs.filter(
            intent_status=PaymentIntentStatus.FAILED
        ).count()
        last_event = (
            PaymentWebhookEvent.objects.filter(provider=provider_name)
            .order_by("-created_at")
            .values_list("created_at", flat=True)
            .first()
        )

        success_rate = (
            (succeeded_24h / webhooks_24h * 100.0) if webhooks_24h > 0 else 0.0
        )
        enabled = (
            bool(provider_cfg.get("enabled"))
            if isinstance(provider_cfg, dict)
            else False
        )
        configured = (
            bool(provider_cfg.get("configured"))
            if isinstance(provider_cfg, dict)
            else (provider_name == "mock")
        )
        if enabled and configured:
            sync_status = "ok" if failed_24h == 0 else "warning"
        elif enabled and not configured:
            sync_status = "danger"
        else:
            sync_status = "neutral"

        provider_rows.append(
            {
                "provider": provider_name,
                "enabled": enabled,
                "configured": configured,
                "sync_status": sync_status,
                "intents_24h": intents_24h,
                "webhooks_24h": webhooks_24h,
                "webhooks_failed_24h": failed_24h,
                "success_rate_24h": round(success_rate, 2),
                "last_event_at": last_event.isoformat() if last_event else None,
            }
        )

    series: list[dict] = []
    for minute_offset in range(14, -1, -1):
        bucket_start = now - timedelta(minutes=minute_offset + 1)
        bucket_end = now - timedelta(minutes=minute_offset)
        orders_created = Order.objects.filter(
            created_at__gte=bucket_start,
            created_at__lt=bucket_end,
        ).count()
        payments_paid = Payment.objects.filter(
            paid_at__gte=bucket_start,
            paid_at__lt=bucket_end,
            status=PaymentStatus.PAID,
        ).count()
        webhooks_received = PaymentWebhookEvent.objects.filter(
            created_at__gte=bucket_start,
            created_at__lt=bucket_end,
        ).count()
        series.append(
            {
                "minute": bucket_end.strftime("%H:%M"),
                "orders_created": orders_created,
                "payments_paid": payments_paid,
                "webhooks_received": webhooks_received,
            }
        )

    return {
        "communication_channel": {
            "transport": "HTTPS",
            "auth": "JWT",
            "encryption": "TLS",
        },
        "frontend_provider": payment_config_public.get(
            "frontend_provider",
            {"web": "mock", "mobile": "mock"},
        ),
        "summary": {
            "payments_pending": Payment.objects.filter(
                status=PaymentStatus.PENDING
            ).count(),
            "payments_paid": Payment.objects.filter(status=PaymentStatus.PAID).count(),
            "payments_failed": Payment.objects.filter(
                status=PaymentStatus.FAILED
            ).count(),
            "intents_active": PaymentIntent.objects.filter(
                status=PaymentIntentStatus.REQUIRES_ACTION
            ).count(),
            "intents_processing": PaymentIntent.objects.filter(
                status=PaymentIntentStatus.PROCESSING
            ).count(),
            "webhooks_last_15m": PaymentWebhookEvent.objects.filter(
                created_at__gte=last_15m
            ).count(),
        },
        "providers": provider_rows,
        "order_lifecycle": lifecycle_counts,
        "series_last_15_minutes": series,
    }


class EcosystemOpsRealtimeAPIView(APIView):
    permission_classes = [RoleMatrixPermission]
    required_roles_by_method = {"GET": MANAGEMENT_ROLES}

    def get(self, _request):
        payload = {
            "generated_at": timezone.now().isoformat(),
            "server_health": _build_server_health_payload(),
            "services": _build_service_monitor_payload(),
            "payment_monitor": _build_payment_monitor_payload(),
        }
        return Response(payload, status=status.HTTP_200_OK)


class OrdersOpsDashboardAPIView(APIView):
    permission_classes = [RoleMatrixPermission]
    required_roles_by_method = {"GET": MANAGEMENT_ROLES}

    def get(self, _request):
        today = timezone.localdate()

        menus_hoje = MenuDay.objects.filter(menu_date=today).count()
        requisicoes_abertas = PurchaseRequest.objects.filter(
            status=PurchaseRequestStatus.OPEN
        ).count()
        requisicoes_aprovadas = PurchaseRequest.objects.filter(
            status=PurchaseRequestStatus.APPROVED
        ).count()
        compras_hoje = Purchase.objects.filter(purchase_date=today).count()

        lotes_hoje = ProductionBatch.objects.filter(production_date=today)
        lotes_planejados = lotes_hoje.filter(
            status=ProductionBatchStatus.PLANNED
        ).count()
        lotes_em_progresso = lotes_hoje.filter(
            status=ProductionBatchStatus.IN_PROGRESS
        ).count()
        lotes_concluidos = lotes_hoje.filter(status=ProductionBatchStatus.DONE).count()

        pedidos_hoje_qs = Order.objects.filter(delivery_date=today)
        pedidos_total = pedidos_hoje_qs.count()
        pedidos_fila = pedidos_hoje_qs.filter(
            status__in=[
                OrderStatus.CREATED,
                OrderStatus.CONFIRMED,
                OrderStatus.IN_PROGRESS,
                OrderStatus.OUT_FOR_DELIVERY,
            ]
        ).count()
        pedidos_entregues = pedidos_hoje_qs.filter(status=OrderStatus.DELIVERED).count()
        pedidos_recebidos = pedidos_hoje_qs.filter(status=OrderStatus.RECEIVED).count()

        receita_hoje = Payment.objects.filter(
            order__delivery_date=today,
            status=PaymentStatus.PAID,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        pipeline = [
            {
                "stage": "Cardapio",
                "count": menus_hoje,
                "status": "ok" if menus_hoje > 0 else "warning",
                "detail": "menus do dia publicados",
                "path": "/modulos/cardapio",
            },
            {
                "stage": "Compras",
                "count": requisicoes_abertas + requisicoes_aprovadas,
                "status": "warning" if requisicoes_abertas > 0 else "ok",
                "detail": "requisicoes pendentes para suprir estoque",
                "path": "/modulos/compras",
            },
            {
                "stage": "Producao",
                "count": lotes_planejados + lotes_em_progresso + lotes_concluidos,
                "status": "ok" if lotes_concluidos > 0 else "warning",
                "detail": "lotes planejados, em progresso e concluidos",
                "path": "/modulos/producao",
            },
            {
                "stage": "Pedidos",
                "count": pedidos_total,
                "status": "ok" if pedidos_total > 0 else "neutral",
                "detail": "pedidos para entrega hoje",
                "path": "/modulos/pedidos",
            },
            {
                "stage": "Entrega",
                "count": pedidos_entregues,
                "status": "ok" if pedidos_entregues > 0 else "neutral",
                "detail": "pedidos marcados como entregues",
                "path": "/modulos/pedidos",
            },
            {
                "stage": "Confirmacao",
                "count": pedidos_recebidos,
                "status": "ok" if pedidos_recebidos > 0 else "neutral",
                "detail": "confirmacoes de recebimento do cliente",
                "path": "/modulos/pedidos",
            },
        ]

        alerts: list[dict] = []
        if requisicoes_abertas > 0:
            alerts.append(
                {
                    "level": "warning",
                    "title": "Compras pendentes",
                    "detail": (
                        f"Existem {requisicoes_abertas} requisicoes abertas "
                        "para compra."
                    ),
                    "path": "/modulos/compras",
                }
            )
        if lotes_planejados > 0 and lotes_concluidos == 0:
            alerts.append(
                {
                    "level": "info",
                    "title": "Producao aguardando conclusao",
                    "detail": (
                        f"{lotes_planejados} lote(s) planejado(s) ainda sem conclusao."
                    ),
                    "path": "/modulos/producao",
                }
            )
        if pedidos_fila > 0:
            alerts.append(
                {
                    "level": "info",
                    "title": "Fila de pedidos ativa",
                    "detail": f"{pedidos_fila} pedido(s) em fila operacional.",
                    "path": "/modulos/pedidos",
                }
            )

        series = []
        for day_offset in range(6, -1, -1):
            target_day = today - timedelta(days=day_offset)
            total_orders = Order.objects.filter(delivery_date=target_day).count()
            paid_revenue = Payment.objects.filter(
                order__delivery_date=target_day,
                status=PaymentStatus.PAID,
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
            total_deliveries = Order.objects.filter(
                delivery_date=target_day,
                status__in=[OrderStatus.DELIVERED, OrderStatus.RECEIVED],
            ).count()
            series.append(
                {
                    "date": target_day.isoformat(),
                    "orders": total_orders,
                    "revenue": f"{paid_revenue:.2f}",
                    "deliveries": total_deliveries,
                }
            )

        return Response(
            {
                "generated_at": timezone.now().isoformat(),
                "kpis": {
                    "menus_hoje": menus_hoje,
                    "requisicoes_abertas": requisicoes_abertas,
                    "requisicoes_aprovadas": requisicoes_aprovadas,
                    "compras_hoje": compras_hoje,
                    "lotes_planejados": lotes_planejados,
                    "lotes_em_progresso": lotes_em_progresso,
                    "lotes_concluidos": lotes_concluidos,
                    "pedidos_hoje": pedidos_total,
                    "pedidos_fila": pedidos_fila,
                    "pedidos_entregues": pedidos_entregues,
                    "pedidos_recebidos": pedidos_recebidos,
                    "receita_hoje": f"{receita_hoje:.2f}",
                },
                "pipeline": pipeline,
                "alerts": alerts,
                "series_last_7_days": series,
            }
        )
