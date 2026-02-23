from decimal import Decimal

from rest_framework import serializers

from apps.catalog.models import Ingredient, IngredientUnit

from .models import StockItem, StockMovement, StockMovementType, StockReferenceType


class StockItemSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source="ingredient.name", read_only=True)

    class Meta:
        model = StockItem
        fields = [
            "id",
            "ingredient",
            "ingredient_name",
            "balance_qty",
            "unit",
            "min_qty",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "ingredient_name"]


class StockMovementSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source="ingredient.name", read_only=True)
    movement_type = serializers.ChoiceField(choices=StockMovementType.choices)
    reference_type = serializers.ChoiceField(choices=StockReferenceType.choices)
    unit = serializers.ChoiceField(choices=IngredientUnit.choices)
    qty = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal("0.001"),
    )

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "ingredient",
            "ingredient_name",
            "movement_type",
            "qty",
            "unit",
            "reference_type",
            "reference_id",
            "note",
            "created_by",
            "created_at",
        ]
        read_only_fields = ["id", "ingredient_name", "created_by", "created_at"]

    def validate_ingredient(self, value: Ingredient) -> Ingredient:
        if not value.is_active:
            raise serializers.ValidationError(
                "Ingrediente inativo nao pode movimentar estoque."
            )
        return value
