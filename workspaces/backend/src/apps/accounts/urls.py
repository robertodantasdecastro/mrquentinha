from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import MeAPIView, RegisterAPIView, RoleViewSet, UserRoleAssignmentAPIView

router = DefaultRouter()
router.register(r"roles", RoleViewSet, basename="accounts-roles")

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="accounts-register"),
    path("token/", TokenObtainPairView.as_view(), name="accounts-token"),
    path("token/refresh/", TokenRefreshView.as_view(), name="accounts-token-refresh"),
    path("me/", MeAPIView.as_view(), name="accounts-me"),
    path(
        "users/<int:user_id>/roles/",
        UserRoleAssignmentAPIView.as_view(),
        name="accounts-user-roles",
    ),
    path("", include(router.urls)),
]
