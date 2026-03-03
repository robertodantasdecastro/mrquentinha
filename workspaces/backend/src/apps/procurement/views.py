import re
from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
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
    SeedParaibaCaseiraWeekInputSerializer,
    SeedParaibaCaseiraWeekResultSerializer,
)
from .services import (
    create_purchase_and_apply_stock,
    create_purchase_request,
    generate_purchase_request_from_menu,
)

ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")
WEEK_RANGE_PATTERN = re.compile(
    r"^- Semana: (?P<start_date>\d{4}-\d{2}-\d{2}) a (?P<end_date>\d{4}-\d{2}-\d{2})$"
)
MENU_DAYS_PATTERN = re.compile(r"^- Cardapios processados: (?P<count>\d+)$")
PURCHASE_REQUESTS_PATTERN = re.compile(
    r"^- Purchase requests simuladas: (?P<count>\d+)$"
)
PURCHASE_PATTERN = re.compile(
    r"^- Compra utilizada: #(?P<id>\d+) \((?P<invoice_number>[^\)]+)\)$"
)
BATCHES_PATTERN = re.compile(r"^- Lotes de producao processados: (?P<count>\d+)$")


def _sanitize_command_output_line(line: str) -> str:
    without_ansi = ANSI_ESCAPE_PATTERN.sub("", line)
    return without_ansi.strip()


def _parse_seed_paraiba_caseira_week_output(raw_output: str) -> dict:
    lines: list[str] = []
    for raw_line in raw_output.splitlines():
        cleaned_line = _sanitize_command_output_line(raw_line)
        if cleaned_line:
            lines.append(cleaned_line)

    result = {
        "start_date": "",
        "end_date": "",
        "menu_days_processed": 0,
        "purchase_requests_created": 0,
        "production_batches_processed": 0,
        "purchase": None,
        "command_log": lines,
    }

    for line in lines:
        week_match = WEEK_RANGE_PATTERN.match(line)
        if week_match:
            result["start_date"] = week_match.group("start_date")
            result["end_date"] = week_match.group("end_date")
            continue

        menu_days_match = MENU_DAYS_PATTERN.match(line)
        if menu_days_match:
            result["menu_days_processed"] = int(menu_days_match.group("count"))
            continue

        purchase_requests_match = PURCHASE_REQUESTS_PATTERN.match(line)
        if purchase_requests_match:
            result["purchase_requests_created"] = int(
                purchase_requests_match.group("count")
            )
            continue

        purchase_match = PURCHASE_PATTERN.match(line)
        if purchase_match:
            result["purchase"] = {
                "id": int(purchase_match.group("id")),
                "invoice_number": purchase_match.group("invoice_number"),
            }
            continue

        batches_match = BATCHES_PATTERN.match(line)
        if batches_match:
            result["production_batches_processed"] = int(batches_match.group("count"))

    return result


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

        image_type = str(request.data.get("image_type", "")).strip().lower()
        side = str(request.data.get("side", "front")).strip().lower()
        if not image_type:
            image_type = side

        field_map = {
            "front": "label_front_image",
            "back": "label_back_image",
            "product": "product_image",
            "price": "price_tag_image",
        }
        field_name = field_map.get(image_type)
        if field_name is None:
            raise DRFValidationError(
                [
                    "Campo 'image_type' deve ser "
                    "'front', 'back', 'product' ou 'price'."
                ]
            )

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


class SeedParaibaCaseiraWeekAPIView(APIView):
    permission_classes = [RoleMatrixPermission]
    required_roles_by_method = {"POST": PROCUREMENT_FROM_MENU_ROLES}

    def post(self, request):
        input_serializer = SeedParaibaCaseiraWeekInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        start_date = input_serializer.validated_data.get("start_date")
        command_kwargs: dict[str, str] = {}
        if start_date is not None:
            command_kwargs["start_date"] = start_date.isoformat()

        command_stdout = StringIO()
        try:
            call_command(
                "seed_paraiba_caseira_week",
                stdout=command_stdout,
                **command_kwargs,
            )
        except CommandError as exc:
            raise DRFValidationError([str(exc)]) from exc

        result = _parse_seed_paraiba_caseira_week_output(command_stdout.getvalue())

        if not result["start_date"] or not result["end_date"]:
            if start_date is None:
                raise DRFValidationError(
                    ["Nao foi possivel interpretar o periodo da simulacao semanal."]
                )
            result["start_date"] = start_date.isoformat()
            result["end_date"] = (start_date + timedelta(days=6)).isoformat()

        output_serializer = SeedParaibaCaseiraWeekResultSerializer(data=result)
        output_serializer.is_valid(raise_exception=True)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
