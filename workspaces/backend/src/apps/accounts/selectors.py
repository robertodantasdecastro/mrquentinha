from django.db.models import QuerySet

from .models import Role, UserRole
from .services import ensure_default_roles


def list_roles() -> QuerySet[Role]:
    ensure_default_roles()
    return Role.objects.order_by("code")


def list_user_roles(*, user_id: int) -> QuerySet[UserRole]:
    return UserRole.objects.filter(user_id=user_id).select_related("role")
