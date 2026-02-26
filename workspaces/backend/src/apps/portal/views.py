from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.services import SystemRole, user_has_any_role
from apps.orders.payment_providers import test_payment_provider_connection

from .models import PortalPage
from .selectors import list_mobile_releases, list_portal_configs, list_portal_sections
from .serializers import (
    MobileReleaseAdminSerializer,
    MobileReleaseLatestSerializer,
    PortalConfigAdminSerializer,
    PortalPublicConfigSerializer,
    PortalSectionAdminSerializer,
    PortalVersionSerializer,
)
from .services import (
    CHANNEL_PORTAL,
    build_latest_mobile_release_payload,
    build_portal_version_payload,
    build_public_portal_payload,
    compile_mobile_release,
    create_mobile_release,
    ensure_portal_config,
    publish_mobile_release,
    publish_portal_config,
    save_portal_config,
)


class PortalAdminPermission(permissions.BasePermission):
    message = "Acesso permitido apenas para administradores."

    def has_permission(self, request, _view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser or user.is_staff:
            return True

        # TODO(7.1): substituir fallback por matriz RBAC fina de portal.
        return user_has_any_role(user, [SystemRole.ADMIN])


class PortalConfigPublicAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        page = request.query_params.get("page", PortalPage.HOME)
        channel = request.query_params.get("channel", CHANNEL_PORTAL)

        try:
            payload = build_public_portal_payload(page=page, channel=channel)
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc
        serializer = PortalPublicConfigSerializer(payload)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PortalConfigVersionAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, _request):
        payload = build_portal_version_payload()
        serializer = PortalVersionSerializer(payload)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MobileReleaseLatestAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, _request):
        payload = build_latest_mobile_release_payload()
        serializer = MobileReleaseLatestSerializer(payload)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PortalConfigAdminViewSet(viewsets.ModelViewSet):
    serializer_class = PortalConfigAdminSerializer
    permission_classes = [permissions.IsAuthenticated, PortalAdminPermission]

    def get_queryset(self):
        ensure_portal_config()
        return list_portal_configs()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            config, created = save_portal_config(payload=serializer.validated_data)
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(config)
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(output.data, status=response_status)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            config, _ = save_portal_config(
                payload=serializer.validated_data,
                instance=instance,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output = self.get_serializer(config)
        return Response(output.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="publish")
    def publish(self, _request):
        config = publish_portal_config()
        output = self.get_serializer(config)
        return Response(output.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="test-payment-provider")
    def test_payment_provider(self, request):
        provider_name = str(request.data.get("provider", "")).strip().lower()
        try:
            payload = test_payment_provider_connection(provider_name)
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc
        return Response(payload, status=status.HTTP_200_OK)


class PortalSectionAdminViewSet(viewsets.ModelViewSet):
    serializer_class = PortalSectionAdminSerializer
    permission_classes = [permissions.IsAuthenticated, PortalAdminPermission]

    def get_queryset(self):
        return list_portal_sections()


class MobileReleaseAdminViewSet(viewsets.ModelViewSet):
    serializer_class = MobileReleaseAdminSerializer
    permission_classes = [permissions.IsAuthenticated, PortalAdminPermission]

    def get_queryset(self):
        return list_mobile_releases()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            release = create_mobile_release(
                payload=serializer.validated_data,
                created_by=request.user,
            )
            compiled_release = compile_mobile_release(release)
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc
        output = self.get_serializer(compiled_release)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="compile")
    def compile(self, request, pk=None):
        release = self.get_object()
        compiled_release = compile_mobile_release(release)
        output = self.get_serializer(compiled_release)
        return Response(output.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        release = self.get_object()
        try:
            published_release = publish_mobile_release(release)
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc
        output = self.get_serializer(published_release)
        return Response(output.data, status=status.HTTP_200_OK)
