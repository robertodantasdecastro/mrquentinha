from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


def normalize_catalog_name(value: str) -> str:
    return " ".join(value.strip().split()).lower()


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class IngredientUnit(models.TextChoices):
    GRAM = "g", "g"
    KILOGRAM = "kg", "kg"
    MILLILITER = "ml", "ml"
    LITER = "l", "l"
    UNIT = "unidade", "unidade"


class NutritionSource(models.TextChoices):
    MANUAL = "MANUAL", "MANUAL"
    OCR = "OCR", "OCR"
    ESTIMATED = "ESTIMATED", "ESTIMATED"


class Ingredient(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    unit = models.CharField(max_length=16, choices=IngredientUnit.choices)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(
        upload_to="catalog/ingredients/%Y/%m/%d",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        self.name = normalize_catalog_name(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class NutritionFact(TimeStampedModel):
    ingredient = models.OneToOneField(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="nutrition_fact",
    )

    energy_kcal_100g = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        null=True,
        blank=True,
    )
    carbs_g_100g = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        null=True,
        blank=True,
    )
    protein_g_100g = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        null=True,
        blank=True,
    )
    fat_g_100g = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        null=True,
        blank=True,
    )
    sat_fat_g_100g = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        null=True,
        blank=True,
    )
    fiber_g_100g = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        null=True,
        blank=True,
    )
    sodium_mg_100g = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        null=True,
        blank=True,
    )

    serving_size_g = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        null=True,
        blank=True,
    )

    energy_kcal_per_serving = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        null=True,
        blank=True,
    )
    carbs_g_per_serving = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        null=True,
        blank=True,
    )
    protein_g_per_serving = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        null=True,
        blank=True,
    )
    fat_g_per_serving = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        null=True,
        blank=True,
    )
    sat_fat_g_per_serving = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        null=True,
        blank=True,
    )
    fiber_g_per_serving = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        null=True,
        blank=True,
    )
    sodium_mg_per_serving = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        null=True,
        blank=True,
    )

    source = models.CharField(
        max_length=16,
        choices=NutritionSource.choices,
        default=NutritionSource.MANUAL,
    )

    class Meta:
        ordering = ["ingredient__name"]

    def __str__(self) -> str:
        return f"Nutrição {self.ingredient.name}"


class Dish(TimeStampedModel):
    name = models.CharField(max_length=140, unique=True)
    description = models.TextField(blank=True, null=True)
    yield_portions = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    image = models.ImageField(
        upload_to="catalog/dishes/%Y/%m/%d",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class DishIngredient(models.Model):
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        related_name="dish_ingredients",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="dish_ingredients",
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    unit = models.CharField(max_length=16, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["dish", "ingredient"],
                name="catalog_dishingredient_dish_ingredient_unique",
            )
        ]

    def __str__(self) -> str:
        return f"{self.dish.name} - {self.ingredient.name}"


class MenuDay(TimeStampedModel):
    menu_date = models.DateField(unique=True)
    title = models.CharField(max_length=180)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="catalog_menus_created",
    )

    class Meta:
        ordering = ["-menu_date"]

    def __str__(self) -> str:
        return f"{self.menu_date} - {self.title}"


class MenuItem(models.Model):
    menu_day = models.ForeignKey(
        MenuDay,
        on_delete=models.CASCADE,
        related_name="items",
    )
    dish = models.ForeignKey(
        Dish,
        on_delete=models.PROTECT,
        related_name="menu_items",
    )
    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    available_qty = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.menu_day.menu_date} - {self.dish.name}"
