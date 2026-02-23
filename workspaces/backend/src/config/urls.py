from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health_view(_request):
    return Response({"status": "ok", "app": "mrquentinha", "version": "v1"})


urlpatterns = [
    path("api/v1/health", health_view, name="health-check"),
]
