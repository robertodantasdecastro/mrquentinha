from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import CustomerSupportMessage, CustomerSupportTicket


class SupportMessageSerializer(serializers.ModelSerializer):
    author_username = serializers.SerializerMethodField()

    class Meta:
        model = CustomerSupportMessage
        fields = [
            "id",
            "ticket",
            "author",
            "author_type",
            "author_username",
            "message",
            "is_internal",
            "created_at",
        ]
        read_only_fields = fields

    def get_author_username(self, obj):
        if obj.author_id:
            return getattr(obj.author, "username", "")
        return ""


class SupportTicketSerializer(serializers.ModelSerializer):
    customer_username = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    last_message_at = serializers.SerializerMethodField()

    class Meta:
        model = CustomerSupportTicket
        fields = [
            "id",
            "customer",
            "customer_username",
            "customer_email",
            "subject",
            "status",
            "priority",
            "channel",
            "assigned_to",
            "created_by",
            "last_activity_at",
            "first_response_at",
            "closed_at",
            "last_message_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_customer_username(self, obj):
        return getattr(obj.customer, "username", "")

    def get_customer_email(self, obj):
        return getattr(obj.customer, "email", "")

    def get_last_message_at(self, obj):
        last_message = obj.messages.order_by("-created_at").first()
        return last_message.created_at if last_message else None


class SupportTicketDetailSerializer(SupportTicketSerializer):
    messages = serializers.SerializerMethodField()

    class Meta(SupportTicketSerializer.Meta):
        fields = [*SupportTicketSerializer.Meta.fields, "messages"]
        read_only_fields = fields

    def get_messages(self, obj):
        queryset = obj.messages.select_related("author").all()
        return SupportMessageSerializer(queryset, many=True).data


class SupportTicketCreateSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=180)
    message = serializers.CharField(max_length=4000)
    channel = serializers.ChoiceField(
        choices=CustomerSupportTicket.Channel.choices,
        default=CustomerSupportTicket.Channel.WEB,
    )
    priority = serializers.ChoiceField(
        choices=CustomerSupportTicket.Priority.choices,
        default=CustomerSupportTicket.Priority.NORMAL,
    )


class SupportTicketAdminUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=CustomerSupportTicket.Status.choices,
        required=False,
    )
    priority = serializers.ChoiceField(
        choices=CustomerSupportTicket.Priority.choices,
        required=False,
    )
    channel = serializers.ChoiceField(
        choices=CustomerSupportTicket.Channel.choices,
        required=False,
    )
    assigned_to_id = serializers.IntegerField(required=False, allow_null=True)
    internal_note = serializers.CharField(required=False, allow_blank=True)

    def validate_assigned_to_id(self, value):
        if value is None:
            return None
        User = get_user_model()
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Usuario atribuido inexistente.")
        return value


class SupportMessageCreateSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=4000)
    is_internal = serializers.BooleanField(required=False, default=False)
