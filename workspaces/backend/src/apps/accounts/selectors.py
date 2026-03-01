from django.db.models import QuerySet

from .models import Role, UserRole, UserTask, UserTaskCategory
from .services import ensure_default_roles, ensure_default_task_catalog


def list_roles() -> QuerySet[Role]:
    ensure_default_roles()
    return Role.objects.order_by("code")


def list_user_roles(*, user_id: int) -> QuerySet[UserRole]:
    return UserRole.objects.filter(user_id=user_id).select_related("role")


def list_task_categories() -> QuerySet[UserTaskCategory]:
    ensure_default_task_catalog()
    return UserTaskCategory.objects.order_by("code").prefetch_related("tasks")


def list_tasks() -> QuerySet[UserTask]:
    ensure_default_task_catalog()
    return UserTask.objects.order_by("category__code", "code").select_related(
        "category"
    )
