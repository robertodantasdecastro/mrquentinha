from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    EmailVerificationConfirmAPIView,
    EmailVerificationResendAPIView,
    MeAPIView,
    MeProfileAPIView,
    RegisterAPIView,
    RoleViewSet,
    TokenObtainPairEmailVerifiedView,
    UserAdminViewSet,
    UserRoleAssignmentAPIView,
)

router = DefaultRouter()
router.register(r"roles", RoleViewSet, basename="accounts-roles")
router.register(r"users", UserAdminViewSet, basename="accounts-users")

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="accounts-register"),
    path(
        "email-verification/confirm/",
        EmailVerificationConfirmAPIView.as_view(),
        name="accounts-email-verification-confirm",
    ),
    path(
        "email-verification/resend/",
        EmailVerificationResendAPIView.as_view(),
        name="accounts-email-verification-resend",
    ),
    path("token/", TokenObtainPairEmailVerifiedView.as_view(), name="accounts-token"),
    path("token/refresh/", TokenRefreshView.as_view(), name="accounts-token-refresh"),
    path("me/", MeAPIView.as_view(), name="accounts-me"),
    path("me/profile/", MeProfileAPIView.as_view(), name="accounts-me-profile"),
    path(
        "users/<int:user_id>/roles/",
        UserRoleAssignmentAPIView.as_view(),
        name="accounts-user-roles",
    ),
    path("", include(router.urls)),
]
