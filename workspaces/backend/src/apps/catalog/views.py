from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Dish, Ingredient, MenuDay
from .selectors import get_menu_by_date, list_active_ingredients
from .serializers import DishSerializer, IngredientSerializer, MenuDaySerializer
from .services import (
    create_dish_with_ingredients,
    set_menu_for_day,
    update_dish_with_ingredients,
)


class IngredientViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis.

    def get_queryset(self):
        if self.action == "list":
            return list_active_ingredients()
        return Ingredient.objects.all().order_by("name")


class DishViewSet(viewsets.ModelViewSet):
    serializer_class = DishSerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis.

    def get_queryset(self):
        return Dish.objects.prefetch_related("dish_ingredients__ingredient").order_by(
            "name"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dish_data = {
            "name": serializer.validated_data["name"],
            "description": serializer.validated_data.get("description"),
            "yield_portions": serializer.validated_data["yield_portions"],
        }
        ingredients_payload = serializer.validated_data.get("ingredients", [])

        try:
            dish = create_dish_with_ingredients(dish_data, ingredients_payload)
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(dish)
        return Response(output.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        dish_data = {
            "name": serializer.validated_data.get("name", instance.name),
            "description": serializer.validated_data.get(
                "description",
                instance.description,
            ),
            "yield_portions": serializer.validated_data.get(
                "yield_portions",
                instance.yield_portions,
            ),
        }
        ingredients_payload = serializer.validated_data.get("ingredients")

        try:
            dish = update_dish_with_ingredients(
                instance,
                dish_data,
                ingredients_payload,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(dish)
        return Response(output.data, status=status.HTTP_200_OK)


class MenuDayViewSet(viewsets.ModelViewSet):
    serializer_class = MenuDaySerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis.

    def get_queryset(self):
        return MenuDay.objects.prefetch_related("items__dish").order_by("-menu_date")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created_by = request.user if request.user.is_authenticated else None
        items_payload = serializer.validated_data.get("items", [])

        try:
            menu_day = set_menu_for_day(
                menu_date=serializer.validated_data["menu_date"],
                title=serializer.validated_data["title"],
                items_payload=items_payload,
                created_by=created_by,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(menu_day)
        return Response(output.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        created_by = request.user if request.user.is_authenticated else None
        items_payload = serializer.validated_data.get("items")

        try:
            menu_day = set_menu_for_day(
                menu_date=serializer.validated_data.get(
                    "menu_date", instance.menu_date
                ),
                title=serializer.validated_data.get("title", instance.title),
                items_payload=items_payload,
                created_by=created_by,
                menu_day=instance,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(menu_day)
        return Response(output.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["get"],
        url_path=r"by-date/(?P<menu_date>\d{4}-\d{2}-\d{2})",
    )
    def by_date(self, _request, menu_date: str):
        try:
            menu = get_menu_by_date(menu_date)
        except ValueError as exc:
            raise DRFValidationError(["Data de cardapio invalida."]) from exc

        if menu is None:
            return Response(
                {"detail": "Cardapio nao encontrado para a data informada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        output = self.get_serializer(menu)
        return Response(output.data)
