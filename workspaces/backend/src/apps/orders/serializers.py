from rest_framework import serializers

from apps.catalog.models import MenuItem

from .models import (
    Order,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentIntent,
    PaymentStatus,
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
    order_items = OrderItemReadSerializer(source="items", many=True, read_only=True)
    payments = PaymentSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "order_date",
            "delivery_date",
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
