from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import APBillStatus, ARReceivableStatus
from .reports import get_cashflow, get_dre, get_kpis
from .selectors import (
    list_accounts,
    list_all_statement_lines,
    list_ap_bills,
    list_ar_receivables,
    list_bank_statements,
    list_cash_movements,
    list_financial_closes,
    list_ledger_entries,
    list_statement_lines,
    list_unreconciled_movements,
)
from .serializers import (
    AccountSerializer,
    APBillSerializer,
    ARReceivableSerializer,
    BankStatementSerializer,
    CashMovementSerializer,
    FinancialCloseSerializer,
    LedgerEntrySerializer,
    ReconcileCashMovementSerializer,
    StatementLineSerializer,
)
from .services import (
    close_period,
    ensure_ap_bill_open_for_write,
    ensure_ar_receivable_open_for_write,
    ensure_cash_movement_open_for_write,
    is_date_closed,
    reconcile_cash_movement,
    unreconcile_cash_movement,
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

    def perform_create(self, serializer):
        status_value = serializer.validated_data.get("status", APBillStatus.OPEN)
        due_date = serializer.validated_data.get("due_date")
        paid_at = serializer.validated_data.get("paid_at")

        try:
            ensure_ap_bill_open_for_write(
                due_date=due_date,
                status=status_value,
                paid_at=paid_at,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        serializer.save()

    def perform_update(self, serializer):
        instance = serializer.instance
        status_value = serializer.validated_data.get("status", instance.status)
        due_date = serializer.validated_data.get("due_date", instance.due_date)
        paid_at = serializer.validated_data.get("paid_at", instance.paid_at)

        try:
            ensure_ap_bill_open_for_write(
                due_date=due_date,
                status=status_value,
                paid_at=paid_at,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        serializer.save()

    def perform_destroy(self, instance):
        try:
            ensure_ap_bill_open_for_write(
                due_date=instance.due_date,
                status=instance.status,
                paid_at=instance.paid_at,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        instance.delete()


class ARReceivableViewSet(viewsets.ModelViewSet):
    serializer_class = ARReceivableSerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get_queryset(self):
        return list_ar_receivables()

    def perform_create(self, serializer):
        status_value = serializer.validated_data.get("status", ARReceivableStatus.OPEN)
        due_date = serializer.validated_data.get("due_date")
        received_at = serializer.validated_data.get("received_at")

        try:
            ensure_ar_receivable_open_for_write(
                due_date=due_date,
                status=status_value,
                received_at=received_at,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        serializer.save()

    def perform_update(self, serializer):
        instance = serializer.instance
        status_value = serializer.validated_data.get("status", instance.status)
        due_date = serializer.validated_data.get("due_date", instance.due_date)
        received_at = serializer.validated_data.get("received_at", instance.received_at)

        try:
            ensure_ar_receivable_open_for_write(
                due_date=due_date,
                status=status_value,
                received_at=received_at,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        serializer.save()

    def perform_destroy(self, instance):
        try:
            ensure_ar_receivable_open_for_write(
                due_date=instance.due_date,
                status=instance.status,
                received_at=instance.received_at,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        instance.delete()


class BankStatementViewSet(viewsets.ModelViewSet):
    serializer_class = BankStatementSerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get_queryset(self):
        return list_bank_statements()

    @action(detail=True, methods=["get", "post"], url_path="lines")
    def lines(self, request, pk=None):
        statement = self.get_object()

        if request.method == "GET":
            serializer = StatementLineSerializer(
                list_statement_lines(statement_id=statement.id),
                many=True,
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        payload = request.data.copy()
        payload["statement"] = statement.id
        serializer = StatementLineSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class StatementLineViewSet(viewsets.ModelViewSet):
    serializer_class = StatementLineSerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get_queryset(self):
        statement_id = self.request.query_params.get("statement")
        if statement_id is None:
            return list_all_statement_lines()

        try:
            statement_id_int = int(statement_id)
        except ValueError as exc:
            raise DRFValidationError(
                {"detail": "Parametro 'statement' deve ser numerico."}
            ) from exc

        return list_statement_lines(statement_id=statement_id_int)


class CashMovementViewSet(viewsets.ModelViewSet):
    serializer_class = CashMovementSerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get_queryset(self):
        return list_cash_movements()

    def perform_create(self, serializer):
        movement_date = serializer.validated_data.get("movement_date") or timezone.now()

        try:
            ensure_cash_movement_open_for_write(movement_date=movement_date)
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        serializer.save()

    def perform_update(self, serializer):
        movement_date = serializer.validated_data.get(
            "movement_date",
            serializer.instance.movement_date,
        )

        try:
            ensure_cash_movement_open_for_write(movement_date=movement_date)
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        serializer.save()

    def perform_destroy(self, instance):
        try:
            ensure_cash_movement_open_for_write(movement_date=instance.movement_date)
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        instance.delete()

    @action(detail=True, methods=["post"], url_path="reconcile")
    def reconcile(self, request, pk=None):
        movement = self.get_object()
        input_serializer = ReconcileCashMovementSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            updated_movement = reconcile_cash_movement(
                cash_movement_id=movement.id,
                statement_line_id=input_serializer.validated_data["statement_line_id"],
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(updated_movement)
        return Response(output.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="unreconcile")
    def unreconcile(self, request, pk=None):
        movement = self.get_object()

        try:
            updated_movement = unreconcile_cash_movement(cash_movement_id=movement.id)
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(updated_movement)
        return Response(output.data, status=status.HTTP_200_OK)


class LedgerEntryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LedgerEntrySerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get_queryset(self):
        return list_ledger_entries()


class FinancialCloseViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = FinancialCloseSerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get_queryset(self):
        return list_financial_closes()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            financial_close = close_period(
                period_start=serializer.validated_data["period_start"],
                period_end=serializer.validated_data["period_end"],
                closed_by=serializer.validated_data.get("closed_by"),
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output_serializer = self.get_serializer(financial_close)
        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


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


class UnreconciledReportAPIView(PeriodReportMixin, APIView):
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get(self, request):
        from_date, to_date = self._parse_period(request)

        movements = list_unreconciled_movements(from_date=from_date, to_date=to_date)
        serializer = CashMovementSerializer(movements, many=True)

        return Response(
            {
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
                "items": serializer.data,
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


class IsClosedAPIView(APIView):
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get(self, request):
        date_raw = request.query_params.get("date")
        if not date_raw:
            raise DRFValidationError(
                {"detail": "Parametro 'date' e obrigatorio no formato YYYY-MM-DD."}
            )

        try:
            parsed_date = date.fromisoformat(date_raw)
        except ValueError as exc:
            raise DRFValidationError(
                {"detail": "Formato invalido. Use 'date' como YYYY-MM-DD."}
            ) from exc

        return Response(
            {
                "date": parsed_date.isoformat(),
                "closed": is_date_closed(parsed_date),
            },
            status=status.HTTP_200_OK,
        )
