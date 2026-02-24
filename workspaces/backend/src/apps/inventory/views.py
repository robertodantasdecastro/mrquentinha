from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from apps.accounts.permissions import (
    INVENTORY_READ_ROLES,
    INVENTORY_WRITE_ROLES,
    RoleMatrixPermission,
)

from .models import StockItem, StockMovement
from .serializers import StockItemSerializer, StockMovementSerializer
from .services import apply_stock_movement


class StockItemViewSet(viewsets.ModelViewSet):
    serializer_class = StockItemSerializer
    permission_classes = [RoleMatrixPermission]
    required_roles_by_action = {
        "read": INVENTORY_READ_ROLES,
        "write": INVENTORY_WRITE_ROLES,
    }

    def get_queryset(self):
        return StockItem.objects.select_related("ingredient").order_by(
            "ingredient__name"
        )


class StockMovementViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = StockMovementSerializer
    permission_classes = [RoleMatrixPermission]
    required_roles_by_action = {
        "read": INVENTORY_READ_ROLES,
        "write": INVENTORY_WRITE_ROLES,
    }

    def get_queryset(self):
        return StockMovement.objects.select_related(
            "ingredient", "created_by"
        ).order_by(
            "-created_at",
            "-id",
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created_by = request.user if request.user.is_authenticated else None

        try:
            movement = apply_stock_movement(
                ingredient=serializer.validated_data["ingredient"],
                movement_type=serializer.validated_data["movement_type"],
                qty=serializer.validated_data["qty"],
                unit=serializer.validated_data["unit"],
                reference_type=serializer.validated_data["reference_type"],
                reference_id=serializer.validated_data.get("reference_id"),
                note=serializer.validated_data.get("note"),
                created_by=created_by,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(movement)
        return Response(output.data, status=status.HTTP_201_CREATED)
