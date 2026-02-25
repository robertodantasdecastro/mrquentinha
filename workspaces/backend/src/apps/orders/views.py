from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import (
    ORDER_CREATE_ROLES,
    ORDER_READ_ROLES,
    ORDER_STATUS_UPDATE_ROLES,
    PAYMENT_READ_ROLES,
    PAYMENT_WRITE_ROLES,
    RoleMatrixPermission,
)
from apps.accounts.services import SystemRole

from .selectors import list_orders, list_payments
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
