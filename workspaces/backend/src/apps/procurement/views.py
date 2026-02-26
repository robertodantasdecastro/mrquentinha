from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import (
    PROCUREMENT_FROM_MENU_ROLES,
    PROCUREMENT_PURCHASE_READ_ROLES,
    PROCUREMENT_PURCHASE_WRITE_ROLES,
    PROCUREMENT_REQUEST_READ_ROLES,
    PROCUREMENT_REQUEST_WRITE_ROLES,
    RoleMatrixPermission,
)
from apps.common.csv_export import build_csv_response
from apps.common.reports import parse_period

from .models import Purchase, PurchaseRequest, PurchaseRequestStatus
from .selectors import list_purchases_by_period
from .serializers import (
    GeneratePurchaseRequestFromMenuSerializer,
    PurchaseItemReadSerializer,
    PurchaseRequestFromMenuResultSerializer,
    PurchaseRequestSerializer,
    PurchaseSerializer,
)
from .services import (
    create_purchase_and_apply_stock,
    create_purchase_request,
    generate_purchase_request_from_menu,
)


class PurchaseRequestViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseRequestSerializer
    permission_classes = [RoleMatrixPermission]
    required_roles_by_action = {
        "read": PROCUREMENT_REQUEST_READ_ROLES,
        "write": PROCUREMENT_REQUEST_WRITE_ROLES,
        "from_menu": PROCUREMENT_FROM_MENU_ROLES,
    }

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

    @action(detail=False, methods=["post"], url_path="from-menu")
    def from_menu(self, request, *args, **kwargs):
        input_serializer = GeneratePurchaseRequestFromMenuSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        requested_by = request.user if request.user.is_authenticated else None

        try:
            result = generate_purchase_request_from_menu(
                menu_day_id=input_serializer.validated_data["menu_day_id"],
                requested_by=requested_by,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output_serializer = PurchaseRequestFromMenuResultSerializer(data=result)
        output_serializer.is_valid(raise_exception=True)

        status_code = (
            status.HTTP_201_CREATED if result["created"] else status.HTTP_200_OK
        )
        return Response(output_serializer.data, status=status_code)

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
    permission_classes = [RoleMatrixPermission]
    required_roles_by_action = {
        "read": PROCUREMENT_PURCHASE_READ_ROLES,
        "write": PROCUREMENT_PURCHASE_WRITE_ROLES,
    }

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
            "receipt_image": serializer.validated_data.get("receipt_image"),
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

    @action(
        detail=True,
        methods=["post", "patch"],
        url_path="receipt-image",
        parser_classes=[MultiPartParser, FormParser],
    )
    def receipt_image(self, request, pk=None):
        purchase = self.get_object()

        image = request.FILES.get("receipt_image") or request.FILES.get("image")
        if image is None:
            raise DRFValidationError(["Envie o arquivo em 'receipt_image'."])

        purchase.receipt_image = image
        purchase.save(update_fields=["receipt_image", "updated_at"])

        output = self.get_serializer(purchase)
        return Response(output.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["post", "patch"],
        url_path=r"items/(?P<item_id>\d+)/label-image",
        parser_classes=[MultiPartParser, FormParser],
    )
    def label_image(self, request, pk=None, item_id=None):
        purchase = self.get_object()
        purchase_item = (
            purchase.items.filter(pk=item_id).select_related("ingredient").first()
        )
        if purchase_item is None:
            raise DRFValidationError(["Item da compra nao encontrado."])

        image = request.FILES.get("label_image") or request.FILES.get("image")
        if image is None:
            raise DRFValidationError(["Envie o arquivo em 'label_image'."])

        side = str(request.data.get("side", "front")).strip().lower()
        if side not in {"front", "back"}:
            raise DRFValidationError(["Campo 'side' deve ser 'front' ou 'back'."])

        field_name = "label_front_image" if side == "front" else "label_back_image"
        setattr(purchase_item, field_name, image)
        purchase_item.save(update_fields=[field_name])

        output = PurchaseItemReadSerializer(purchase_item, context={"request": request})
        return Response(output.data, status=status.HTTP_200_OK)


class PurchasesExportAPIView(APIView):
    permission_classes = [RoleMatrixPermission]
    required_roles_by_method = {"GET": PROCUREMENT_PURCHASE_READ_ROLES}

    def get(self, request):
        from_date, to_date = parse_period(
            from_raw=request.query_params.get("from"),
            to_raw=request.query_params.get("to"),
        )
        purchases = list_purchases_by_period(from_date=from_date, to_date=to_date)

        header = [
            "compra_id",
            "data_compra",
            "fornecedor",
            "nota_fiscal",
            "ingrediente",
            "quantidade",
            "unidade",
            "preco_unitario",
            "imposto",
            "total_item",
            "total_compra",
        ]

        rows = []
        for purchase in purchases:
            for item in purchase.items.all():
                item_total = item.qty * item.unit_price
                tax_amount = item.tax_amount or Decimal("0")
                rows.append(
                    [
                        purchase.id,
                        purchase.purchase_date.isoformat(),
                        purchase.supplier_name,
                        purchase.invoice_number or "",
                        item.ingredient.name,
                        f"{item.qty:.3f}",
                        item.unit,
                        f"{item.unit_price:.2f}",
                        f"{tax_amount:.2f}",
                        f"{item_total:.2f}",
                        f"{purchase.total_amount:.2f}",
                    ]
                )

        filename = f"compras_{from_date.isoformat()}_{to_date.isoformat()}.csv"
        return build_csv_response(filename=filename, header=header, rows=rows)

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
