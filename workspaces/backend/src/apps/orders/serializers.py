from rest_framework import serializers

from apps.catalog.models import MenuItem

from .models import (
    Order,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentIntent,
    PaymentIntentStatus,
    PaymentMethod,
    PaymentStatus,
    PaymentWebhookEvent,
)


class OrderItemWriteSerializer(serializers.Serializer):
    menu_item = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all())
    qty = serializers.IntegerField(min_value=1)


class OrderItemReadSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source="menu_item.dish.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "menu_item", "menu_item_name", "qty", "unit_price"]


class PaymentSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "method", "status", "amount", "provider_ref", "paid_at"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemWriteSerializer(many=True, write_only=True, required=False)
    payment_method = serializers.ChoiceField(
        choices=PaymentMethod.choices,
        write_only=True,
        required=False,
        default=PaymentMethod.PIX,
    )
    order_items = OrderItemReadSerializer(source="items", many=True, read_only=True)
    payments = PaymentSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "order_date",
            "delivery_date",
            "payment_method",
            "status",
            "total_amount",
            "created_at",
            "updated_at",
            "items",
            "order_items",
            "payments",
        ]
        read_only_fields = [
            "id",
            "customer",
            "order_date",
            "status",
            "total_amount",
            "created_at",
            "updated_at",
            "order_items",
            "payments",
        ]

    def validate_items(self, value: list[dict]) -> list[dict]:
        menu_item_ids = [item["menu_item"].id for item in value]
        if len(menu_item_ids) != len(set(menu_item_ids)):
            raise serializers.ValidationError("Item de cardapio duplicado no pedido.")
        return value


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=OrderStatus.choices)


class PaymentSerializer(serializers.ModelSerializer):
    order_delivery_date = serializers.DateField(
        source="order.delivery_date",
        read_only=True,
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "order_delivery_date",
            "method",
            "status",
            "amount",
            "provider_ref",
            "paid_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "order",
            "order_delivery_date",
            "method",
            "amount",
            "created_at",
        ]


class PaymentStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=PaymentStatus.choices)
    provider_ref = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    paid_at = serializers.DateTimeField(required=False, allow_null=True)


class PaymentIntentSerializer(serializers.ModelSerializer):
    payment_id = serializers.IntegerField(source="payment.id", read_only=True)

    class Meta:
        model = PaymentIntent
        fields = [
            "id",
            "payment_id",
            "provider",
            "status",
            "idempotency_key",
            "provider_intent_ref",
            "client_payload",
            "expires_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PaymentWebhookInputSerializer(serializers.Serializer):
    provider = serializers.CharField(required=False, allow_blank=False)
    event_id = serializers.CharField(max_length=120)
    provider_intent_ref = serializers.CharField(max_length=180)
    intent_status = serializers.ChoiceField(choices=PaymentIntentStatus.choices)
    provider_ref = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    paid_at = serializers.DateTimeField(required=False, allow_null=True)


class PaymentWebhookEventSerializer(serializers.ModelSerializer):
    payment_id = serializers.SerializerMethodField()
    intent_id = serializers.SerializerMethodField()

    class Meta:
        model = PaymentWebhookEvent
        fields = [
            "id",
            "provider",
            "event_id",
            "payment_id",
            "intent_id",
            "intent_status",
            "payment_status",
            "processed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_payment_id(self, obj: PaymentWebhookEvent) -> int | None:
        return obj.payment_id

    def get_intent_id(self, obj: PaymentWebhookEvent) -> int | None:
        return obj.intent_id
