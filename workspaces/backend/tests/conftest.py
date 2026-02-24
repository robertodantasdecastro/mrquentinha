import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.services import (
    SystemRole,
    assign_roles_to_user,
    ensure_default_roles,
)


@pytest.fixture
def admin_user(db):
    User = get_user_model()
    user = User.objects.create_user(
        username="admin_test",
        password="admin_test_123",
        email="admin_test@example.com",
    )
    ensure_default_roles()
    assign_roles_to_user(user=user, role_codes=[SystemRole.ADMIN], replace=True)
    return user


@pytest.fixture
def client(db, admin_user):
    api_client = APIClient()
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def anonymous_client():
    return APIClient()


@pytest.fixture
def create_user_with_roles(db):
    User = get_user_model()
    ensure_default_roles()

    def _factory(
        *,
        username: str,
        role_codes: list[str] | None = None,
        is_staff: bool = False,
        password: str = "test_pass_123",
    ):
        user = User.objects.create_user(
            username=username,
            password=password,
            email=f"{username}@example.com",
            is_staff=is_staff,
        )

        if role_codes:
            assign_roles_to_user(user=user, role_codes=role_codes, replace=True)

        return user

    return _factory
