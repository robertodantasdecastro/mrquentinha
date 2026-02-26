from datetime import date

from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PersonalAuditEvent, PersonalDirection
from .selectors import (
    list_personal_accounts,
    list_personal_audit_logs,
    list_personal_budgets,
    list_personal_categories,
    list_personal_entries,
    list_personal_import_jobs,
    list_personal_recurring_rules,
)
from .serializers import (
    PersonalAccountSerializer,
    PersonalAuditLogSerializer,
    PersonalBudgetSerializer,
    PersonalCategorySerializer,
    PersonalEntrySerializer,
    PersonalImportJobSerializer,
    PersonalImportPreviewSerializer,
    PersonalMonthlySummaryQuerySerializer,
    PersonalRecurringMaterializeSerializer,
    PersonalRecurringRuleSerializer,
)
from .services import (
    build_personal_data_export,
    build_personal_monthly_summary,
    confirm_personal_import_job,
    create_personal_budget,
    create_personal_entry,
    create_personal_recurring_rule,
    materialize_personal_recurring_rules,
    preview_personal_import_csv,
    record_personal_audit_log,
    update_personal_budget,
    update_personal_entry,
    update_personal_recurring_rule,
)


class PersonalAuditMixin:
    audit_resource_type = "PERSONAL_RESOURCE"

    def _log_personal_event(
        self,
        *,
        request,
        event_type: str,
        resource_id: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        record_personal_audit_log(
            owner=request.user,
            event_type=event_type,
            resource_type=self.audit_resource_type,
            resource_id=resource_id,
            metadata=metadata,
        )


class PersonalAccountViewSet(PersonalAuditMixin, viewsets.ModelViewSet):
    serializer_class = PersonalAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    audit_resource_type = "ACCOUNT"

    def get_queryset(self):
        return list_personal_accounts(owner=self.request.user)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.LIST,
            metadata={"query_params": request.query_params.dict()},
        )
        return response

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.RETRIEVE,
            resource_id=int(kwargs["pk"]),
        )
        return response

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.CREATE,
            resource_id=response.data["id"],
        )
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.UPDATE,
            resource_id=int(kwargs["pk"]),
            metadata={"partial": kwargs.get("partial", False)},
        )
        return response

    def destroy(self, request, *args, **kwargs):
        resource_id = int(kwargs["pk"])
        response = super().destroy(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.DELETE,
            resource_id=resource_id,
        )
        return response

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PersonalCategoryViewSet(PersonalAuditMixin, viewsets.ModelViewSet):
    serializer_class = PersonalCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    audit_resource_type = "CATEGORY"

    def get_queryset(self):
        return list_personal_categories(owner=self.request.user)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.LIST,
            metadata={"query_params": request.query_params.dict()},
        )
        return response

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.RETRIEVE,
            resource_id=int(kwargs["pk"]),
        )
        return response

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.CREATE,
            resource_id=response.data["id"],
        )
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.UPDATE,
            resource_id=int(kwargs["pk"]),
            metadata={"partial": kwargs.get("partial", False)},
        )
        return response

    def destroy(self, request, *args, **kwargs):
        resource_id = int(kwargs["pk"])
        response = super().destroy(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.DELETE,
            resource_id=resource_id,
        )
        return response

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PersonalEntryViewSet(PersonalAuditMixin, viewsets.ModelViewSet):
    serializer_class = PersonalEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    audit_resource_type = "ENTRY"

    def get_queryset(self):
        from_param = self.request.query_params.get("from")
        to_param = self.request.query_params.get("to")
        direction = self.request.query_params.get("direction")

        from_date = _parse_optional_date(param_name="from", value=from_param)
        to_date = _parse_optional_date(param_name="to", value=to_param)

        if from_date and to_date and from_date > to_date:
            raise DRFValidationError({"detail": "Parametro 'from' deve ser <= 'to'."})

        if direction and direction not in PersonalDirection.values:
            raise DRFValidationError({"detail": "Parametro 'direction' invalido."})

        return list_personal_entries(
            owner=self.request.user,
            from_date=from_date,
            to_date=to_date,
            direction=direction,
        )

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.LIST,
            metadata={"query_params": request.query_params.dict()},
        )
        return response

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.RETRIEVE,
            resource_id=int(kwargs["pk"]),
        )
        return response

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            entry = create_personal_entry(
                owner=request.user,
                payload=serializer.validated_data,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(entry)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.CREATE,
            resource_id=entry.id,
        )
        return Response(output.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            entry = update_personal_entry(
                entry=instance,
                owner=request.user,
                payload=serializer.validated_data,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(entry)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.UPDATE,
            resource_id=entry.id,
            metadata={"partial": partial},
        )
        return Response(output.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        resource_id = int(kwargs["pk"])
        response = super().destroy(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.DELETE,
            resource_id=resource_id,
        )
        return response


class PersonalRecurringRuleViewSet(PersonalAuditMixin, viewsets.ModelViewSet):
    serializer_class = PersonalRecurringRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    audit_resource_type = "RECURRING_RULE"

    def get_queryset(self):
        return list_personal_recurring_rules(owner=self.request.user)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.LIST,
            metadata={"query_params": request.query_params.dict()},
        )
        return response

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.RETRIEVE,
            resource_id=int(kwargs["pk"]),
        )
        return response

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            recurring_rule = create_personal_recurring_rule(
                owner=request.user,
                payload=serializer.validated_data,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(recurring_rule)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.CREATE,
            resource_id=recurring_rule.id,
        )
        return Response(output.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            recurring_rule = update_personal_recurring_rule(
                recurring_rule=instance,
                owner=request.user,
                payload=serializer.validated_data,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(recurring_rule)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.UPDATE,
            resource_id=recurring_rule.id,
            metadata={"partial": partial},
        )
        return Response(output.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        resource_id = int(kwargs["pk"])
        response = super().destroy(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.DELETE,
            resource_id=resource_id,
        )
        return response

    @action(detail=False, methods=["post"], url_path="materialize")
    def materialize(self, request):
        serializer = PersonalRecurringMaterializeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payload = materialize_personal_recurring_rules(
                owner=request.user,
                from_date=serializer.validated_data["from_date"],
                to_date=serializer.validated_data["to_date"],
                recurring_rule_id=serializer.validated_data.get("recurring_rule_id"),
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.UPDATE,
            metadata=payload,
        )
        return Response(payload, status=status.HTTP_200_OK)


class PersonalBudgetViewSet(PersonalAuditMixin, viewsets.ModelViewSet):
    serializer_class = PersonalBudgetSerializer
    permission_classes = [permissions.IsAuthenticated]
    audit_resource_type = "BUDGET"

    def get_queryset(self):
        return list_personal_budgets(owner=self.request.user)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.LIST,
            metadata={"query_params": request.query_params.dict()},
        )
        return response

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.RETRIEVE,
            resource_id=int(kwargs["pk"]),
        )
        return response

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            budget = create_personal_budget(
                owner=request.user,
                payload=serializer.validated_data,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(budget)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.CREATE,
            resource_id=budget.id,
        )
        return Response(output.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            budget = update_personal_budget(
                budget=instance,
                owner=request.user,
                payload=serializer.validated_data,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(budget)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.UPDATE,
            resource_id=budget.id,
            metadata={"partial": partial},
        )
        return Response(output.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        resource_id = int(kwargs["pk"])
        response = super().destroy(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.DELETE,
            resource_id=resource_id,
        )
        return response


class PersonalAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PersonalAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return list_personal_audit_logs(owner=self.request.user)


class PersonalImportJobViewSet(PersonalAuditMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = PersonalImportJobSerializer
    permission_classes = [permissions.IsAuthenticated]
    audit_resource_type = "IMPORT_JOB"

    def get_queryset(self):
        return list_personal_import_jobs(owner=self.request.user)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.LIST,
            metadata={"query_params": request.query_params.dict()},
        )
        return response

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        self._log_personal_event(
            request=request,
            event_type=PersonalAuditEvent.RETRIEVE,
            resource_id=int(kwargs["pk"]),
        )
        return response


class PersonalDataExportAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        payload = build_personal_data_export(owner=request.user)

        record_personal_audit_log(
            owner=request.user,
            event_type=PersonalAuditEvent.EXPORT,
            resource_type="PERSONAL_DATA_EXPORT",
            metadata={
                "accounts": len(payload["data"]["accounts"]),
                "categories": len(payload["data"]["categories"]),
                "recurring_rules": len(payload["data"]["recurring_rules"]),
                "entries": len(payload["data"]["entries"]),
                "budgets": len(payload["data"]["budgets"]),
                "import_jobs": len(payload["data"]["import_jobs"]),
            },
        )

        return Response(payload, status=status.HTTP_200_OK)


class PersonalMonthlySummaryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = PersonalMonthlySummaryQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        month_raw = serializer.validated_data["month"]
        month_ref = date.fromisoformat(f"{month_raw}-01")

        payload = build_personal_monthly_summary(
            owner=request.user,
            month_ref=month_ref,
        )
        record_personal_audit_log(
            owner=request.user,
            event_type=PersonalAuditEvent.LIST,
            resource_type="MONTHLY_SUMMARY",
            metadata={"month": month_raw},
        )

        return Response(payload, status=status.HTTP_200_OK)


class PersonalImportPreviewAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PersonalImportPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_obj = serializer.validated_data.get("file")
        csv_content = serializer.validated_data.get("csv_content")
        source_filename = serializer.validated_data.get("source_filename")

        if file_obj is not None:
            source_filename = source_filename or file_obj.name
            try:
                csv_content = file_obj.read().decode("utf-8")
            except UnicodeDecodeError as exc:
                raise DRFValidationError(
                    {"detail": "Arquivo CSV deve estar em UTF-8."}
                ) from exc

        source_filename = source_filename or "inline.csv"

        try:
            import_job = preview_personal_import_csv(
                owner=request.user,
                csv_content=csv_content,
                source_filename=source_filename,
                delimiter=serializer.validated_data.get("delimiter", ","),
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        payload = PersonalImportJobSerializer(import_job).data
        record_personal_audit_log(
            owner=request.user,
            event_type=PersonalAuditEvent.CREATE,
            resource_type="IMPORT_JOB",
            resource_id=import_job.id,
            metadata={
                "rows_total": import_job.rows_total,
                "rows_valid": import_job.rows_valid,
                "rows_invalid": import_job.rows_invalid,
            },
        )

        return Response(payload, status=status.HTTP_201_CREATED)


class PersonalImportConfirmAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, job_id: int):
        import_job = get_object_or_404(
            list_personal_import_jobs(owner=request.user),
            pk=job_id,
        )

        try:
            result = confirm_personal_import_job(
                owner=request.user,
                import_job=import_job,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        payload = {
            "result": result,
            "job": PersonalImportJobSerializer(import_job).data,
        }

        record_personal_audit_log(
            owner=request.user,
            event_type=PersonalAuditEvent.UPDATE,
            resource_type="IMPORT_JOB",
            resource_id=import_job.id,
            metadata=result,
        )

        return Response(payload, status=status.HTTP_200_OK)


def _parse_optional_date(*, param_name: str, value: str | None) -> date | None:
    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise DRFValidationError(
            {"detail": f"Parametro '{param_name}' deve estar em YYYY-MM-DD."}
        ) from exc
