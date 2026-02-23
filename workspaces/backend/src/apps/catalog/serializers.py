from decimal import Decimal

from rest_framework import serializers

from .models import (
    Dish,
    DishIngredient,
    Ingredient,
    MenuDay,
    MenuItem,
    normalize_catalog_name,
)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = [
            "id",
            "name",
            "unit",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_name(self, value: str) -> str:
        normalized = normalize_catalog_name(value)
        queryset = Ingredient.objects.filter(name__iexact=normalized)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("Ingrediente com este nome ja existe.")
        return normalized


class DishIngredientReadSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)

    class Meta:
        model = DishIngredient
        fields = ["id", "ingredient", "quantity", "unit"]


class DishIngredientWriteSerializer(serializers.Serializer):
    ingredient = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )
    quantity = serializers.DecimalField(
        max_digits=10,
        decimal_places=3,
        min_value=Decimal("0.001"),
    )
    unit = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class DishSerializer(serializers.ModelSerializer):
    ingredients = DishIngredientWriteSerializer(
        many=True, write_only=True, required=False
    )
    composition = DishIngredientReadSerializer(
        source="dish_ingredients",
        many=True,
        read_only=True,
    )

    class Meta:
        model = Dish
        fields = [
            "id",
            "name",
            "description",
            "yield_portions",
            "created_at",
            "updated_at",
            "ingredients",
            "composition",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "composition"]

    def validate_name(self, value: str) -> str:
        normalized = " ".join(value.strip().split())
        queryset = Dish.objects.filter(name__iexact=normalized)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("Prato com este nome ja existe.")
        return normalized

    def validate_ingredients(self, value: list[dict]) -> list[dict]:
        ingredient_ids = [item["ingredient"].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError("Ingrediente duplicado no payload.")
        return value


class DishSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Dish
        fields = ["id", "name", "yield_portions"]


class MenuItemReadSerializer(serializers.ModelSerializer):
    dish = DishSummarySerializer(read_only=True)

    class Meta:
        model = MenuItem
        fields = ["id", "dish", "sale_price", "available_qty", "is_active"]


class MenuItemWriteSerializer(serializers.Serializer):
    dish = serializers.PrimaryKeyRelatedField(
        queryset=Dish.objects.all(),
    )
    sale_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0"),
    )
    available_qty = serializers.IntegerField(
        required=False, allow_null=True, min_value=0
    )
    is_active = serializers.BooleanField(required=False, default=True)


class MenuDaySerializer(serializers.ModelSerializer):
    items = MenuItemWriteSerializer(many=True, write_only=True, required=False)
    menu_items = MenuItemReadSerializer(source="items", many=True, read_only=True)

    class Meta:
        model = MenuDay
        fields = [
            "id",
            "menu_date",
            "title",
            "created_by",
            "created_at",
            "updated_at",
            "items",
            "menu_items",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "created_at",
            "updated_at",
            "menu_items",
        ]

    def validate_items(self, value: list[dict]) -> list[dict]:
        dish_ids = [item["dish"].id for item in value]
        if len(dish_ids) != len(set(dish_ids)):
            raise serializers.ValidationError("Prato duplicado no cardapio do dia.")
        return value
