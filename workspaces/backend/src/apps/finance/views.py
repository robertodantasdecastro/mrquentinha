from datetime import date

from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .reports import get_cashflow
from .selectors import (
    list_accounts,
    list_ap_bills,
    list_ar_receivables,
    list_cash_movements,
)
from .serializers import (
    AccountSerializer,
    APBillSerializer,
    ARReceivableSerializer,
    CashMovementSerializer,
)


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get_queryset(self):
        return list_accounts()


class APBillViewSet(viewsets.ModelViewSet):
    serializer_class = APBillSerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get_queryset(self):
        return list_ap_bills()


class ARReceivableViewSet(viewsets.ModelViewSet):
    serializer_class = ARReceivableSerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get_queryset(self):
        return list_ar_receivables()


class CashMovementViewSet(viewsets.ModelViewSet):
    serializer_class = CashMovementSerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get_queryset(self):
        return list_cash_movements()


class CashflowReportAPIView(APIView):
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get(self, request):
        from_date, to_date = self._parse_period(request)

        cashflow_items = get_cashflow(from_date=from_date, to_date=to_date)
        payload_items = [
            {
                "date": item["date"].isoformat(),
                "total_in": f"{item['total_in']:.2f}",
                "total_out": f"{item['total_out']:.2f}",
                "net": f"{item['net']:.2f}",
                "running_balance": f"{item['running_balance']:.2f}",
            }
            for item in cashflow_items
        ]

        return Response(
            {
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
                "items": payload_items,
            },
            status=status.HTTP_200_OK,
        )

    def _parse_period(self, request) -> tuple[date, date]:
        from_raw = request.query_params.get("from")
        to_raw = request.query_params.get("to")

        if not from_raw or not to_raw:
            raise DRFValidationError(
                {
                    "detail": (
                        "Parametros 'from' e 'to' sao obrigatorios no formato "
                        "YYYY-MM-DD."
                    )
                }
            )

        try:
            from_date = date.fromisoformat(from_raw)
            to_date = date.fromisoformat(to_raw)
        except ValueError as exc:
            raise DRFValidationError(
                {"detail": "Formato invalido. Use 'from' e 'to' como YYYY-MM-DD."}
            ) from exc

        if from_date > to_date:
            raise DRFValidationError(
                {"detail": "Parametro 'from' deve ser menor ou igual a 'to'."}
            )

        return from_date, to_date
