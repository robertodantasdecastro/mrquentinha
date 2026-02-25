from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import (
    PRODUCTION_READ_ROLES,
    PRODUCTION_WRITE_ROLES,
    RoleMatrixPermission,
)
from apps.common.csv_export import build_csv_response
from apps.common.reports import parse_period

from .selectors import list_batches, list_batches_by_period
from .serializers import ProductionBatchSerializer
from .services import complete_batch, create_batch_for_date


class ProductionBatchViewSet(viewsets.ModelViewSet):
    serializer_class = ProductionBatchSerializer
    permission_classes = [RoleMatrixPermission]
    required_roles_by_action = {
        "read": PRODUCTION_READ_ROLES,
        "write": PRODUCTION_WRITE_ROLES,
    }

    def get_queryset(self):
        return list_batches()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created_by = request.user if request.user.is_authenticated else None
        items_payload = serializer.validated_data.get("items", [])

        try:
            batch = create_batch_for_date(
                production_date=serializer.validated_data["production_date"],
                items_payload=items_payload,
                note=serializer.validated_data.get("note"),
                created_by=created_by,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(batch)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        try:
            batch = complete_batch(batch_id=int(pk))
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(batch)
        return Response(output.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        if "items" in request.data:
            raise DRFValidationError(
                ["Atualizacao de itens exige fluxo dedicado de producao."]
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if "items" in request.data:
            raise DRFValidationError(
                ["Atualizacao de itens exige fluxo dedicado de producao."]
            )
        return super().partial_update(request, *args, **kwargs)


class ProductionExportAPIView(APIView):
    permission_classes = [RoleMatrixPermission]
    required_roles_by_method = {"GET": PRODUCTION_READ_ROLES}

    def get(self, request):
        from_date, to_date = parse_period(
            from_raw=request.query_params.get("from"),
            to_raw=request.query_params.get("to"),
        )
        batches = list_batches_by_period(from_date=from_date, to_date=to_date)

        header = [
            "lote_id",
            "data_producao",
            "status",
            "prato",
            "quantidade_planejada",
            "quantidade_produzida",
            "quantidade_perdas",
        ]

        rows = []
        for batch in batches:
            for item in batch.items.all():
                dish_name = item.menu_item.dish.name
                rows.append(
                    [
                        batch.id,
                        batch.production_date.isoformat(),
                        batch.status,
                        dish_name,
                        item.qty_planned,
                        item.qty_produced,
                        item.qty_waste,
                    ]
                )

        filename = f"producao_{from_date.isoformat()}_{to_date.isoformat()}.csv"
        return build_csv_response(filename=filename, header=header, rows=rows)
