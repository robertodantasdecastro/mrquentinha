from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserProfile
from .permissions import RoleMatrixPermission
from .selectors import list_roles
from .serializers import (
    AssignRolesSerializer,
    MeSerializer,
    RegisterSerializer,
    RoleSerializer,
    UserAdminSerializer,
    UserProfileSerializer,
)
from .services import SystemRole, get_user_role_codes


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        output = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "roles": sorted(get_user_role_codes(user)),
        }
        return Response(output, status=status.HTTP_201_CREATED)


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
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = UserAdminSerializer
    permission_classes = [RoleMatrixPermission]
    required_roles = (SystemRole.ADMIN,)

    def get_queryset(self):
        User = get_user_model()
        return User.objects.order_by("id").prefetch_related("user_roles__role")


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
