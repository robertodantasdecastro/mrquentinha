from __future__ import annotations

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .customer_selectors import list_customer_lgpd_requests, list_customers_queryset
from .customer_serializers import (
    CustomerAccountStatusSerializer,
    CustomerConsentsUpdateSerializer,
    CustomerDetailSerializer,
    CustomerGovernanceSerializer,
    CustomerLgpdRequestCreateSerializer,
    CustomerLgpdRequestSerializer,
    CustomerLgpdRequestStatusSerializer,
    CustomerListSerializer,
    CustomerProfileAdminSerializer,
)
from .customer_services import (
    apply_customer_account_status,
    apply_customer_consents,
    create_lgpd_request,
    ensure_customer_governance_profile,
)
from .models import CustomerGovernanceProfile, CustomerLgpdRequest, UserProfile
from .permissions import MANAGEMENT_ROLES, RoleMatrixPermission
from .services import issue_email_verification_for_user


class CustomerAdminViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [RoleMatrixPermission]
    required_roles = MANAGEMENT_ROLES
    serializer_class = CustomerListSerializer

    def get_queryset(self):
        queryset = list_customers_queryset()
        params = self.request.query_params

        search = str(params.get("search", "")).strip()
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(profile__full_name__icontains=search)
                | Q(profile__cpf__icontains=search)
                | Q(profile__cnpj__icontains=search)
            )

        account_status = str(params.get("account_status", "")).strip().upper()
        if account_status:
            if account_status == CustomerGovernanceProfile.AccountStatus.ACTIVE:
                queryset = queryset.filter(
                    Q(
                        customer_governance__account_status=CustomerGovernanceProfile.AccountStatus.ACTIVE
                    )
                    | Q(customer_governance__isnull=True)
                )
            else:
                queryset = queryset.filter(
                    customer_governance__account_status=account_status
                )

        is_active_value = str(params.get("is_active", "")).strip().lower()
        if is_active_value in {"true", "false"}:
            queryset = queryset.filter(is_active=(is_active_value == "true"))

        compliance = str(params.get("compliance", "")).strip().lower()
        if compliance == "pending_email":
            queryset = queryset.filter(profile__email_verified_at__isnull=True)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CustomerDetailSerializer
        return CustomerListSerializer

    @action(
        detail=True,
        methods=["patch"],
        url_path="profile",
        parser_classes=[JSONParser, MultiPartParser, FormParser],
    )
    def profile(self, request, pk=None):
        customer = self.get_object()
        profile, _created = UserProfile.objects.get_or_create(user=customer)
        serializer = CustomerProfileAdminSerializer(
            profile,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"], url_path="governance")
    def governance(self, request, pk=None):
        customer = self.get_object()
        governance = ensure_customer_governance_profile(user=customer)
        serializer = CustomerGovernanceSerializer(
            governance,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        instance = serializer.save(
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        output = CustomerGovernanceSerializer(instance)
        return Response(output.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="status")
    def status_update(self, request, pk=None):
        customer = self.get_object()
        serializer = CustomerAccountStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        governance = apply_customer_account_status(
            customer=customer,
            account_status=serializer.validated_data["account_status"],
            reason=serializer.validated_data.get("reason", ""),
            actor=request.user,
        )
        output = CustomerGovernanceSerializer(governance)
        return Response(output.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="consents")
    def update_consents(self, request, pk=None):
        customer = self.get_object()
        serializer = CustomerConsentsUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        governance = apply_customer_consents(
            customer=customer,
            accepted_terms=serializer.validated_data.get("accepted_terms"),
            accepted_privacy_policy=serializer.validated_data.get(
                "accepted_privacy_policy"
            ),
            marketing_opt_in=serializer.validated_data.get("marketing_opt_in"),
        )
        output = CustomerGovernanceSerializer(governance)
        return Response(output.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="resend-email-verification")
    def resend_email_verification(self, request, pk=None):
        customer = self.get_object()
        preferred_client_base_url = str(
            request.data.get("preferred_client_base_url", "")
        ).strip()
        result = issue_email_verification_for_user(
            user=customer,
            preferred_client_base_url=preferred_client_base_url,
        )
        response_status = status.HTTP_200_OK
        if not bool(result.get("sent", False)):
            response_status = status.HTTP_202_ACCEPTED
        return Response(result, status=response_status)

    @action(detail=True, methods=["get", "post"], url_path="lgpd-requests")
    def lgpd_requests(self, request, pk=None):
        customer = self.get_object()

        if request.method.upper() == "GET":
            queryset = list_customer_lgpd_requests(customer_id=customer.id)
            serializer = CustomerLgpdRequestSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = CustomerLgpdRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lgpd_request = create_lgpd_request(
            customer=customer,
            request_type=serializer.validated_data["request_type"],
            channel=serializer.validated_data["channel"],
            requested_by_name=serializer.validated_data.get("requested_by_name", ""),
            requested_by_email=serializer.validated_data.get("requested_by_email", ""),
            notes=serializer.validated_data.get("notes", ""),
            request_payload=serializer.validated_data.get("request_payload", {}),
        )
        output = CustomerLgpdRequestSerializer(lgpd_request)
        return Response(output.data, status=status.HTTP_201_CREATED)


class CustomerLgpdRequestStatusAPIView(APIView):
    permission_classes = [RoleMatrixPermission]
    required_roles = MANAGEMENT_ROLES

    def patch(self, request, request_id: int):
        serializer = CustomerLgpdRequestStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lgpd_request = get_object_or_404(CustomerLgpdRequest, pk=request_id)
        lgpd_request.status = serializer.validated_data["status"]

        resolution_notes = str(
            serializer.validated_data.get("resolution_notes", "")
        ).strip()
        if resolution_notes:
            lgpd_request.resolution_notes = resolution_notes

        if lgpd_request.status in {
            CustomerLgpdRequest.RequestStatus.COMPLETED,
            CustomerLgpdRequest.RequestStatus.REJECTED,
        }:
            lgpd_request.resolved_at = timezone.now()
            lgpd_request.resolved_by = request.user
        else:
            lgpd_request.resolved_at = None
            lgpd_request.resolved_by = None

        lgpd_request.save(
            update_fields=[
                "status",
                "resolution_notes",
                "resolved_at",
                "resolved_by",
                "updated_at",
            ]
        )

        output = CustomerLgpdRequestSerializer(lgpd_request)
        return Response(output.data, status=status.HTTP_200_OK)


class CustomerLifecycleOverviewAPIView(APIView):
    permission_classes = [RoleMatrixPermission]
    required_roles = MANAGEMENT_ROLES

    def get(self, _request):
        queryset = list_customers_queryset()
        total = queryset.count()
        active = queryset.filter(is_active=True).count()
        inactive = total - active
        with_pending_email = queryset.filter(
            profile__email_verified_at__isnull=True
        ).count()

        governance_values = list(
            queryset.values_list("customer_governance__account_status", flat=True)
        )
        by_status: dict[str, int] = {
            "ACTIVE": 0,
            "UNDER_REVIEW": 0,
            "SUSPENDED": 0,
            "BLOCKED": 0,
            "UNKNOWN": 0,
        }
        for status_code in governance_values:
            normalized = str(status_code or "").strip().upper()
            if not normalized:
                normalized = CustomerGovernanceProfile.AccountStatus.ACTIVE
            if normalized in by_status:
                by_status[normalized] += 1
            else:
                by_status["UNKNOWN"] += 1

        return Response(
            {
                "total": total,
                "active": active,
                "inactive": inactive,
                "with_pending_email": with_pending_email,
                "by_account_status": by_status,
            },
            status=status.HTTP_200_OK,
        )
