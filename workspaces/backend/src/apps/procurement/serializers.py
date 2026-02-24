from decimal import Decimal

from rest_framework import serializers

from apps.catalog.models import Ingredient, IngredientUnit
from apps.catalog.serializers import build_media_url

from .models import (
    Purchase,
    PurchaseItem,
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseRequestStatus,
)


class IngredientSummarySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = ["id", "name", "unit", "image_url"]

    def get_image_url(self, obj: Ingredient) -> str | None:
        return build_media_url(
            request=self.context.get("request"), file_field=obj.image
        )


class PurchaseRequestItemWriteSerializer(serializers.Serializer):
    ingredient = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    required_qty = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal("0.001"),
    )
    unit = serializers.ChoiceField(choices=IngredientUnit.choices)


class PurchaseRequestItemReadSerializer(serializers.ModelSerializer):
    ingredient = IngredientSummarySerializer(read_only=True)

    class Meta:
        model = PurchaseRequestItem
        fields = ["id", "ingredient", "required_qty", "unit"]


class PurchaseRequestSerializer(serializers.ModelSerializer):
    items = PurchaseRequestItemWriteSerializer(
        many=True, write_only=True, required=False
    )
    request_items = PurchaseRequestItemReadSerializer(
        source="items",
        many=True,
        read_only=True,
    )

    class Meta:
        model = PurchaseRequest
        fields = [
            "id",
            "requested_by",
            "status",
            "requested_at",
            "note",
            "items",
            "request_items",
        ]
        read_only_fields = ["id", "requested_by", "requested_at", "request_items"]

    def validate_status(self, value: str) -> str:
        return value or PurchaseRequestStatus.OPEN

    def validate_items(self, value: list[dict]) -> list[dict]:
        ingredient_ids = [item["ingredient"].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError("Ingrediente duplicado na solicitacao.")
        return value


class GeneratePurchaseRequestFromMenuSerializer(serializers.Serializer):
    menu_day_id = serializers.IntegerField(min_value=1)


class PurchaseRequestFromMenuItemSerializer(serializers.Serializer):
    ingredient_id = serializers.IntegerField()
    ingredient_name = serializers.CharField()
    required_qty = serializers.DecimalField(max_digits=12, decimal_places=3)
    unit = serializers.ChoiceField(choices=IngredientUnit.choices)


class PurchaseRequestFromMenuResultSerializer(serializers.Serializer):
    created = serializers.BooleanField()
    purchase_request_id = serializers.IntegerField(allow_null=True)
    message = serializers.CharField()
    items = PurchaseRequestFromMenuItemSerializer(many=True)


class PurchaseItemWriteSerializer(serializers.Serializer):
    ingredient = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    qty = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal("0.001"),
    )
    unit = serializers.ChoiceField(choices=IngredientUnit.choices)
    unit_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0"),
    )
    tax_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0"),
        required=False,
        allow_null=True,
    )
    expiry_date = serializers.DateField(required=False, allow_null=True)
    label_front_image = serializers.ImageField(required=False, allow_null=True)
    label_back_image = serializers.ImageField(required=False, allow_null=True)


class PurchaseItemReadSerializer(serializers.ModelSerializer):
    ingredient = IngredientSummarySerializer(read_only=True)
    label_front_image_url = serializers.SerializerMethodField()
    label_back_image_url = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseItem
        fields = [
            "id",
            "ingredient",
            "qty",
            "unit",
            "unit_price",
            "tax_amount",
            "expiry_date",
            "label_front_image",
            "label_front_image_url",
            "label_back_image",
            "label_back_image_url",
            "metadata",
        ]

    def get_label_front_image_url(self, obj: PurchaseItem) -> str | None:
        return build_media_url(
            request=self.context.get("request"),
            file_field=obj.label_front_image,
        )

    def get_label_back_image_url(self, obj: PurchaseItem) -> str | None:
        return build_media_url(
            request=self.context.get("request"),
            file_field=obj.label_back_image,
        )


class PurchaseSerializer(serializers.ModelSerializer):
    items = PurchaseItemWriteSerializer(many=True, write_only=True, required=False)
    purchase_items = PurchaseItemReadSerializer(
        source="items",
        many=True,
        read_only=True,
    )
    receipt_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Purchase
        fields = [
            "id",
            "buyer",
            "supplier_name",
            "invoice_number",
            "purchase_date",
            "total_amount",
            "receipt_image",
            "receipt_image_url",
            "created_at",
            "updated_at",
            "items",
            "purchase_items",
        ]
        read_only_fields = [
            "id",
            "buyer",
            "total_amount",
            "receipt_image_url",
            "created_at",
            "updated_at",
            "purchase_items",
        ]

    def validate_items(self, value: list[dict]) -> list[dict]:
        ingredient_ids = [item["ingredient"].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError("Ingrediente duplicado na compra.")
        return value

    def get_receipt_image_url(self, obj: Purchase) -> str | None:
        return build_media_url(
            request=self.context.get("request"),
            file_field=obj.receipt_image,
        )
