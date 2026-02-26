from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Sum
from django.utils import timezone
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
from apps.procurement.models import Purchase, PurchaseRequest, PurchaseRequestStatus
from apps.production.models import ProductionBatch, ProductionBatchStatus

from .models import Order, OrderStatus, Payment, PaymentStatus
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
