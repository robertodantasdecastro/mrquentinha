from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .selectors import list_orders, list_payments
from .serializers import (
    OrderSerializer,
    OrderStatusUpdateSerializer,
    PaymentSerializer,
    PaymentStatusUpdateSerializer,
)
from .services import create_order, update_order_status, update_payment_status


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC (cliente proprio x gestao).

    def get_queryset(self):
        return list_orders()

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
        input_serializer = OrderStatusUpdateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            order = update_order_status(
                order_id=int(pk),
                new_status=input_serializer.validated_data["status"],
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(order)
        return Response(output.data, status=status.HTTP_200_OK)


class PaymentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis.

    def get_queryset(self):
        return list_payments()

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
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = PaymentSerializer(updated_payment)
        return Response(output.data, status=status.HTTP_200_OK)
