from django.urls import path

from .views import AdminActivityLogListAPIView, AdminActivityOverviewAPIView

urlpatterns = [
    path(
        "admin-activity/overview/",
        AdminActivityOverviewAPIView.as_view(),
        name="admin-audit-admin-activity-overview",
    ),
    path(
        "admin-activity/",
        AdminActivityLogListAPIView.as_view(),
        name="admin-audit-admin-activity",
    ),
]
