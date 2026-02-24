from datetime import date
from decimal import Decimal

from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .reports import get_cashflow, get_dre, get_kpis
from .selectors import (
    list_accounts,
    list_ap_bills,
    list_ar_receivables,
    list_cash_movements,
    list_ledger_entries,
)
from .serializers import (
    AccountSerializer,
    APBillSerializer,
    ARReceivableSerializer,
    CashMovementSerializer,
    LedgerEntrySerializer,
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


class LedgerEntryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LedgerEntrySerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get_queryset(self):
        return list_ledger_entries()


class PeriodReportMixin:
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

    def _format_money(self, value: Decimal) -> str:
        return f"{value:.2f}"


class CashflowReportAPIView(PeriodReportMixin, APIView):
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get(self, request):
        from_date, to_date = self._parse_period(request)

        cashflow_items = get_cashflow(from_date=from_date, to_date=to_date)
        payload_items = [
            {
                "date": item["date"].isoformat(),
                "total_in": self._format_money(item["total_in"]),
                "total_out": self._format_money(item["total_out"]),
                "net": self._format_money(item["net"]),
                "running_balance": self._format_money(item["running_balance"]),
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


class DreReportAPIView(PeriodReportMixin, APIView):
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get(self, request):
        from_date, to_date = self._parse_period(request)
        dre = get_dre(from_date=from_date, to_date=to_date)

        return Response(
            {
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
                "dre": {
                    "receita_total": self._format_money(dre["receita_total"]),
                    "despesas_total": self._format_money(dre["despesas_total"]),
                    "cmv_estimado": self._format_money(dre["cmv_estimado"]),
                    "lucro_bruto": self._format_money(dre["lucro_bruto"]),
                    "resultado": self._format_money(dre["resultado"]),
                },
            },
            status=status.HTTP_200_OK,
        )


class KpisReportAPIView(PeriodReportMixin, APIView):
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get(self, request):
        from_date, to_date = self._parse_period(request)
        kpis = get_kpis(from_date=from_date, to_date=to_date)

        return Response(
            {
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
                "kpis": {
                    "pedidos": kpis["pedidos"],
                    "receita_total": self._format_money(kpis["receita_total"]),
                    "despesas_total": self._format_money(kpis["despesas_total"]),
                    "cmv_estimado": self._format_money(kpis["cmv_estimado"]),
                    "lucro_bruto": self._format_money(kpis["lucro_bruto"]),
                    "ticket_medio": self._format_money(kpis["ticket_medio"]),
                    "margem_media": self._format_money(kpis["margem_media"]),
                },
            },
            status=status.HTTP_200_OK,
        )
