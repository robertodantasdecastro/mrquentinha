from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    MobileReleaseAdminViewSet,
    MobileReleaseLatestAPIView,
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
router.register(
    r"admin/mobile/releases",
    MobileReleaseAdminViewSet,
    basename="portal-admin-mobile-releases",
)

urlpatterns = [
    path("config/", PortalConfigPublicAPIView.as_view(), name="portal-config"),
    path(
        "config/version",
        PortalConfigVersionAPIView.as_view(),
        name="portal-config-version",
    ),
    path(
        "mobile/releases/latest/",
        MobileReleaseLatestAPIView.as_view(),
        name="portal-mobile-release-latest",
    ),
    path("", include(router.urls)),
]
