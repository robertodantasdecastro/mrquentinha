from django.db.models import QuerySet

from .models import MobileRelease, MobileReleaseStatus, PortalConfig, PortalSection


def list_portal_configs() -> QuerySet[PortalConfig]:
    return PortalConfig.objects.all().order_by("-updated_at")


def get_portal_singleton() -> PortalConfig | None:
    return PortalConfig.objects.filter(singleton_key=PortalConfig.SINGLETON_KEY).first()


def list_portal_sections() -> QuerySet[PortalSection]:
    return PortalSection.objects.select_related("config").order_by("sort_order", "id")


def list_sections_by_template_page(
    *,
    config: PortalConfig,
    template_id: str,
    page: str,
    enabled_only: bool = True,
) -> QuerySet[PortalSection]:
    queryset = PortalSection.objects.filter(
        config=config,
        template_id=template_id,
        page=page,
    )

    if enabled_only:
        queryset = queryset.filter(is_enabled=True)

    return queryset.order_by("sort_order", "id")


def list_mobile_releases(
    *,
    config: PortalConfig | None = None,
) -> QuerySet[MobileRelease]:
    queryset = MobileRelease.objects.select_related("config", "created_by")
    if config is not None:
        queryset = queryset.filter(config=config)
    return queryset.order_by("-created_at", "-id")


def get_latest_published_mobile_release(
    *,
    config: PortalConfig | None = None,
) -> MobileRelease | None:
    queryset = MobileRelease.objects.filter(status=MobileReleaseStatus.PUBLISHED)
    if config is not None:
        queryset = queryset.filter(config=config)
    return queryset.order_by("-published_at", "-created_at", "-id").first()
