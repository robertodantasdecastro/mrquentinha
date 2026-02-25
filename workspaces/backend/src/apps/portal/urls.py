from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PortalConfigAdminViewSet,
    PortalConfigPublicAPIView,
    PortalConfigVersionAPIView,
    PortalSectionAdminViewSet,
)

router = DefaultRouter()
router.register(
    r"admin/config", PortalConfigAdminViewSet, basename="portal-admin-config"
)
router.register(
    r"admin/sections", PortalSectionAdminViewSet, basename="portal-admin-sections"
)

urlpatterns = [
    path("config/", PortalConfigPublicAPIView.as_view(), name="portal-config"),
    path(
        "config/version",
        PortalConfigVersionAPIView.as_view(),
        name="portal-config-version",
    ),
    path("", include(router.urls)),
]
