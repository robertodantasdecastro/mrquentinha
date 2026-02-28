from django.urls import path

from .views import AdminActivityLogListAPIView

urlpatterns = [
    path(
        "admin-activity/",
        AdminActivityLogListAPIView.as_view(),
        name="admin-audit-admin-activity",
    ),
]
