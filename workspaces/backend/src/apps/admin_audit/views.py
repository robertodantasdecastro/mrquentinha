from __future__ import annotations

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.services import SystemRole, user_has_any_role

from .selectors import filter_admin_activity_logs
from .serializers import AdminActivityLogSerializer


class AdminAuditPermission(permissions.BasePermission):
    message = "Acesso permitido apenas para administradores."

    def has_permission(self, request, _view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser or user.is_staff:
            return True

        return user_has_any_role(user, [SystemRole.ADMIN])


class AdminActivityLogListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, AdminAuditPermission]

    def get(self, request):
        query = request.query_params
        try:
            limit = int(query.get("limit", 50))
        except (TypeError, ValueError):
            limit = 50
        try:
            offset = int(query.get("offset", 0))
        except (TypeError, ValueError):
            offset = 0

        limit = max(1, min(limit, 200))
        offset = max(0, offset)

        queryset = filter_admin_activity_logs(
            search=str(query.get("search", "") or ""),
            actor=str(query.get("actor", "") or ""),
            channel=str(query.get("channel", "") or ""),
            method=str(query.get("method", "") or ""),
            status=str(query.get("status", "") or ""),
            date_from=str(query.get("date_from", "") or ""),
            date_to=str(query.get("date_to", "") or ""),
        )

        total_count = queryset.count()
        records = queryset[offset : offset + limit]
        serializer = AdminActivityLogSerializer(records, many=True)

        next_offset = offset + limit if (offset + limit) < total_count else None

        return Response(
            {
                "count": total_count,
                "offset": offset,
                "limit": limit,
                "next_offset": next_offset,
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
