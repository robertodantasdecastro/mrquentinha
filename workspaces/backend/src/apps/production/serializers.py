from rest_framework import serializers

from apps.catalog.models import MenuItem

from .models import ProductionBatch, ProductionBatchStatus, ProductionItem


class ProductionItemWriteSerializer(serializers.Serializer):
    menu_item = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all())
    qty_planned = serializers.IntegerField(min_value=1)
    qty_produced = serializers.IntegerField(min_value=0, required=False, default=0)
    qty_waste = serializers.IntegerField(min_value=0, required=False, default=0)
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class ProductionItemReadSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source="menu_item.dish.name", read_only=True)

    class Meta:
        model = ProductionItem
        fields = [
            "id",
            "menu_item",
            "menu_item_name",
            "qty_planned",
            "qty_produced",
            "qty_waste",
            "note",
        ]


class ProductionBatchSerializer(serializers.ModelSerializer):
    items = ProductionItemWriteSerializer(many=True, write_only=True, required=False)
    production_items = ProductionItemReadSerializer(
        source="items",
        many=True,
        read_only=True,
    )

    class Meta:
        model = ProductionBatch
        fields = [
            "id",
            "production_date",
            "status",
            "note",
            "created_by",
            "created_at",
            "updated_at",
            "items",
            "production_items",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_by",
            "created_at",
            "updated_at",
            "production_items",
        ]

    def validate_items(self, value: list[dict]) -> list[dict]:
        menu_item_ids = [item["menu_item"].id for item in value]
        if len(menu_item_ids) != len(set(menu_item_ids)):
            raise serializers.ValidationError("Item de cardapio duplicado no lote.")
        return value


class ProductionBatchCompleteSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ProductionBatchStatus.choices)
