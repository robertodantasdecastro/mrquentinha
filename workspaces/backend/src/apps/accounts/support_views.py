from __future__ import annotations

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CustomerSupportMessage, CustomerSupportTicket
from .permissions import MANAGEMENT_ROLES, RoleMatrixPermission
from .support_serializers import (
    SupportMessageCreateSerializer,
    SupportMessageSerializer,
    SupportTicketAdminUpdateSerializer,
    SupportTicketCreateSerializer,
    SupportTicketDetailSerializer,
    SupportTicketSerializer,
)


class SupportTicketAdminViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [RoleMatrixPermission]
    required_roles = MANAGEMENT_ROLES

    def get_queryset(self):
        return (
            CustomerSupportTicket.objects.select_related("customer", "assigned_to")
            .prefetch_related("messages")
            .order_by("-updated_at")
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SupportTicketDetailSerializer
        return SupportTicketSerializer

    def partial_update(self, request, *args, **kwargs):
        ticket = self.get_object()
        serializer = SupportTicketAdminUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        update_fields: list[str] = ["updated_at"]
        if "status" in data:
            ticket.status = data["status"]
            update_fields.append("status")
            if data["status"] in {
                CustomerSupportTicket.Status.RESOLVED,
                CustomerSupportTicket.Status.CLOSED,
            }:
                ticket.closed_at = timezone.now()
                update_fields.append("closed_at")
        if "priority" in data:
            ticket.priority = data["priority"]
            update_fields.append("priority")
        if "channel" in data:
            ticket.channel = data["channel"]
            update_fields.append("channel")
        if "assigned_to_id" in data:
            assigned_to_id = data["assigned_to_id"]
            if assigned_to_id is None:
                ticket.assigned_to = None
            else:
                User = get_user_model()
                ticket.assigned_to = User.objects.get(id=assigned_to_id)
            update_fields.append("assigned_to")

        internal_note = str(data.get("internal_note", "") or "").strip()
        if internal_note:
            CustomerSupportMessage.objects.create(
                ticket=ticket,
                author=request.user,
                author_type=CustomerSupportMessage.AuthorType.AGENT,
                message=internal_note,
                is_internal=True,
            )
            ticket.last_activity_at = timezone.now()
            update_fields.append("last_activity_at")

        ticket.save(update_fields=list(set(update_fields)))
        output = SupportTicketDetailSerializer(ticket)
        return Response(output.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get", "post"], url_path="messages")
    def messages(self, request, pk=None):
        ticket = self.get_object()
        if request.method.upper() == "GET":
            queryset = ticket.messages.select_related("author").all()
            return Response(SupportMessageSerializer(queryset, many=True).data)

        serializer = SupportMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = CustomerSupportMessage.objects.create(
            ticket=ticket,
            author=request.user,
            author_type=CustomerSupportMessage.AuthorType.AGENT,
            message=serializer.validated_data["message"],
            is_internal=serializer.validated_data.get("is_internal", False),
        )
        ticket.last_activity_at = timezone.now()
        ticket.save(update_fields=["last_activity_at", "updated_at"])
        return Response(
            SupportMessageSerializer(message).data,
            status=status.HTTP_201_CREATED,
        )


class SupportTicketCustomerViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            CustomerSupportTicket.objects.filter(customer=self.request.user)
            .select_related("assigned_to")
            .prefetch_related("messages")
            .order_by("-updated_at")
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SupportTicketDetailSerializer
        return SupportTicketSerializer

    @action(detail=False, methods=["post"], url_path="create")
    def create_ticket(self, request):
        serializer = SupportTicketCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = CustomerSupportTicket.objects.create(
            customer=request.user,
            subject=serializer.validated_data["subject"],
            channel=serializer.validated_data.get(
                "channel", CustomerSupportTicket.Channel.WEB
            ),
            priority=serializer.validated_data.get(
                "priority", CustomerSupportTicket.Priority.NORMAL
            ),
            created_by=request.user,
            last_activity_at=timezone.now(),
        )
        CustomerSupportMessage.objects.create(
            ticket=ticket,
            author=request.user,
            author_type=CustomerSupportMessage.AuthorType.CUSTOMER,
            message=serializer.validated_data["message"],
        )
        output = SupportTicketDetailSerializer(ticket)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "post"], url_path="messages")
    def messages(self, request, pk=None):
        ticket = self.get_object()
        if request.method.upper() == "GET":
            queryset = ticket.messages.select_related("author").filter(
                is_internal=False
            )
            return Response(SupportMessageSerializer(queryset, many=True).data)

        serializer = SupportMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = CustomerSupportMessage.objects.create(
            ticket=ticket,
            author=request.user,
            author_type=CustomerSupportMessage.AuthorType.CUSTOMER,
            message=serializer.validated_data["message"],
            is_internal=False,
        )
        ticket.last_activity_at = timezone.now()
        ticket.save(update_fields=["last_activity_at", "updated_at"])
        return Response(
            SupportMessageSerializer(message).data,
            status=status.HTTP_201_CREATED,
        )
