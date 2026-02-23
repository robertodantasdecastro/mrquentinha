from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Purchase, PurchaseRequest, PurchaseRequestStatus
from .serializers import PurchaseRequestSerializer, PurchaseSerializer
from .services import create_purchase_and_apply_stock, create_purchase_request


class PurchaseRequestViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseRequestSerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis.

    def get_queryset(self):
        return PurchaseRequest.objects.select_related("requested_by").prefetch_related(
            "items__ingredient"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        requested_by = request.user if request.user.is_authenticated else None
        request_data = {
            "status": serializer.validated_data.get(
                "status",
                PurchaseRequestStatus.OPEN,
            ),
            "note": serializer.validated_data.get("note"),
        }
        items_payload = serializer.validated_data.get("items", [])

        try:
            purchase_request = create_purchase_request(
                request_data=request_data,
                items_payload=items_payload,
                requested_by=requested_by,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(purchase_request)
        return Response(output.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        if "items" in request.data:
            raise DRFValidationError(
                ["Atualizacao de itens exige fluxo dedicado de solicitacoes."]
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if "items" in request.data:
            raise DRFValidationError(
                ["Atualizacao de itens exige fluxo dedicado de solicitacoes."]
            )
        return super().partial_update(request, *args, **kwargs)


class PurchaseViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseSerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis.

    def get_queryset(self):
        return Purchase.objects.select_related("buyer").prefetch_related(
            "items__ingredient"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        buyer = request.user if request.user.is_authenticated else None
        purchase_data = {
            "supplier_name": serializer.validated_data["supplier_name"],
            "invoice_number": serializer.validated_data.get("invoice_number"),
            "purchase_date": serializer.validated_data["purchase_date"],
        }
        items_payload = serializer.validated_data.get("items", [])

        try:
            purchase = create_purchase_and_apply_stock(
                purchase_data=purchase_data,
                items_payload=items_payload,
                buyer=buyer,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(purchase)
        return Response(output.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        if "items" in request.data:
            raise DRFValidationError(
                ["Atualizacao de itens deve ser feita em fluxo dedicado de compras."]
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if "items" in request.data:
            raise DRFValidationError(
                ["Atualizacao de itens deve ser feita em fluxo dedicado de compras."]
            )
        return super().partial_update(request, *args, **kwargs)
