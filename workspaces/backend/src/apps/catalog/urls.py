from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DishViewSet, IngredientViewSet, MenuDayViewSet

router = DefaultRouter()
router.register(r"ingredients", IngredientViewSet, basename="catalog-ingredients")
router.register(r"dishes", DishViewSet, basename="catalog-dishes")
router.register(r"menus", MenuDayViewSet, basename="catalog-menus")

urlpatterns = [
    path("", include(router.urls)),
]
