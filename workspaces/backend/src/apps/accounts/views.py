from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import UserProfile
from .permissions import RoleMatrixPermission
from .selectors import list_roles, list_task_categories, list_tasks
from .serializers import (
    AdminUserCreateSerializer,
    AdminUserUpdateSerializer,
    AssignRolesSerializer,
    AssignTasksSerializer,
    EmailVerificationConfirmSerializer,
    EmailVerificationResendSerializer,
    MeSerializer,
    RegisterSerializer,
    RoleSerializer,
    TokenObtainPairEmailVerifiedSerializer,
    UserAdminSerializer,
    UserProfileSerializer,
    UserTaskCategorySerializer,
    UserTaskSerializer,
)
from .services import (
    SystemRole,
    confirm_email_verification_token,
    get_user_role_codes,
    issue_email_verification_for_user,
)


def _resolve_preferred_client_base_url(request) -> str:
    origin = str(request.headers.get("Origin", "")).strip()
    if origin:
        return origin

    referer = str(request.headers.get("Referer", "")).strip()
    if not referer:
        return ""

    from urllib.parse import urlparse

    parsed = urlparse(referer)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""

    return f"{parsed.scheme}://{parsed.netloc}"


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        preferred_client_base_url = _resolve_preferred_client_base_url(request)
        email_verification_status = issue_email_verification_for_user(
            user=user,
            preferred_client_base_url=preferred_client_base_url,
        )
        output = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "roles": sorted(get_user_role_codes(user)),
            "email_verification_sent": bool(
                email_verification_status.get("sent", False)
            ),
            "email_verification_detail": str(
                email_verification_status.get("detail", "")
            ).strip(),
        }
        return Response(output, status=status.HTTP_201_CREATED)


class TokenObtainPairEmailVerifiedView(TokenObtainPairView):
    serializer_class = TokenObtainPairEmailVerifiedSerializer


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = MeSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MeProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def _get_profile(self, user):
        profile, _created = UserProfile.objects.get_or_create(user=user)
        return profile

    def get(self, request):
        profile = self._get_profile(request.user)
        serializer = UserProfileSerializer(profile, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        profile = self._get_profile(request.user)
        serializer = UserProfileSerializer(
            profile,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class RoleViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = RoleSerializer
    permission_classes = [RoleMatrixPermission]
    required_roles = (SystemRole.ADMIN,)

    def get_queryset(self):
        return list_roles()


class UserAdminViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = UserAdminSerializer
    permission_classes = [RoleMatrixPermission]
    required_roles = (SystemRole.ADMIN,)

    def get_queryset(self):
        User = get_user_model()
        return (
            User.objects.order_by("id")
            .prefetch_related("user_roles__role")
            .prefetch_related("task_assignments__task__category")
            .select_related("profile")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return AdminUserCreateSerializer
        if self.action in {"update", "partial_update"}:
            return AdminUserUpdateSerializer
        return UserAdminSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        output = UserAdminSerializer(user)
        return Response(output.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        user = self.get_object()
        serializer = self.get_serializer(
            data=request.data,
            partial=partial,
            context={"user": user},
        )
        serializer.is_valid(raise_exception=True)
        serializer.apply(user=user)
        output = UserAdminSerializer(user)
        return Response(output.data, status=status.HTTP_200_OK)


class UserRoleAssignmentAPIView(APIView):
    permission_classes = [RoleMatrixPermission]
    required_roles = (SystemRole.ADMIN,)

    def post(self, request, user_id: int):
        User = get_user_model()
        user = get_object_or_404(User, pk=user_id)

        serializer = AssignRolesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        role_codes = serializer.apply(user=user)

        return Response(
            {
                "user_id": user.id,
                "username": user.username,
                "role_codes": sorted(role_codes),
            },
            status=status.HTTP_200_OK,
        )


class UserTaskAssignmentAPIView(APIView):
    permission_classes = [RoleMatrixPermission]
    required_roles = (SystemRole.ADMIN,)

    def post(self, request, user_id: int):
        User = get_user_model()
        user = get_object_or_404(User, pk=user_id)

        serializer = AssignTasksSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task_codes = serializer.apply(user=user, assigned_by=request.user)
        return Response(
            {
                "user_id": user.id,
                "username": user.username,
                "task_codes": sorted(task_codes),
            },
            status=status.HTTP_200_OK,
        )


class UserTaskCategoryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = UserTaskCategorySerializer
    permission_classes = [RoleMatrixPermission]
    required_roles = (SystemRole.ADMIN,)

    def get_queryset(self):
        return list_task_categories()


class UserTaskViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = UserTaskSerializer
    permission_classes = [RoleMatrixPermission]
    required_roles = (SystemRole.ADMIN,)

    def get_queryset(self):
        return list_tasks()


class EmailVerificationConfirmAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        serializer = EmailVerificationConfirmSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            user = confirm_email_verification_token(
                token=serializer.validated_data["token"],
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        return Response(
            {
                "detail": "E-mail confirmado com sucesso.",
                "email_verified": True,
                "username": user.username,
            },
            status=status.HTTP_200_OK,
        )


class EmailVerificationResendAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailVerificationResendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_user = request.user if request.user.is_authenticated else None
        identifier = str(serializer.validated_data.get("identifier", "")).strip()

        if target_user is None:
            if not identifier:
                raise DRFValidationError(
                    {"identifier": ["Informe usuario ou e-mail para reenviar o token."]}
                )

            User = get_user_model()
            target_user = (
                User.objects.filter(
                    Q(username__iexact=identifier) | Q(email__iexact=identifier)
                )
                .order_by("id")
                .first()
            )
            if target_user is None:
                return Response(
                    {
                        "detail": (
                            "Se a conta existir, um novo e-mail de "
                            "confirmacao sera enviado."
                        ),
                        "sent": False,
                        "email": "",
                        "client_base_url": "",
                    },
                    status=status.HTTP_202_ACCEPTED,
                )

        preferred_client_base_url = serializer.validated_data.get(
            "preferred_client_base_url"
        ) or _resolve_preferred_client_base_url(request)
        result = issue_email_verification_for_user(
            user=target_user,
            preferred_client_base_url=preferred_client_base_url,
        )
        response_status = status.HTTP_200_OK
        if not bool(result.get("sent", False)):
            response_status = status.HTTP_202_ACCEPTED
        return Response(
            {
                "detail": str(result.get("detail", "")).strip(),
                "sent": bool(result.get("sent", False)),
                "email": str(result.get("email", "")).strip(),
                "client_base_url": str(result.get("client_base_url", "")).strip(),
            },
            status=response_status,
        )
