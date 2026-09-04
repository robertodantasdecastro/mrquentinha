import base64
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError
from django.test import override_settings
from django.utils import timezone

from apps.accounts.address_lookup import CepLookupNotFoundError
from apps.accounts.models import UserProfile, UserRole, UserTaskAssignment
from apps.accounts.services import (
    SystemRole,
    assign_roles_to_user,
    ensure_default_roles,
    resolve_client_base_url,
)
from apps.portal.services import ensure_portal_config


@pytest.mark.django_db
def test_accounts_register_cria_usuario_com_role_cliente(anonymous_client):
    response = anonymous_client.post(
        "/api/v1/accounts/register/",
        {
            "username": "cliente_novo",
            "password": "Senha_Forte_123",
            "email": "cliente_novo@example.com",
            "first_name": "Cliente",
            "last_name": "Novo",
        },
        format="json",
    )

    assert response.status_code == 201

    User = get_user_model()
    created_user = User.objects.get(username="cliente_novo")
    assert response.json()["id"] == created_user.id

    role_codes = set(
        UserRole.objects.filter(user=created_user).values_list("role__code", flat=True)
    )
    assert role_codes == {SystemRole.CLIENTE}


def _raise_portal_database_error():
    raise DatabaseError("portal indisponivel")


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    ACCOUNTS_ALLOW_REQUEST_CLIENT_BASE_URL=True,
    ACCOUNTS_CLIENT_BASE_URL_HTTPS_ONLY=False,
)
def test_accounts_register_envia_email_confirmacao_com_url_do_frontend_origem(
    anonymous_client,
):
    response = anonymous_client.post(
        "/api/v1/accounts/register/",
        {
            "username": "cliente_confirmacao",
            "password": "Senha_Forte_123",
            "email": "cliente_confirmacao@example.com",
            "first_name": "Cliente",
            "last_name": "Confirmacao",
        },
        format="json",
        HTTP_ORIGIN="https://anderson-cats-tri-consistently.trycloudflare.com",
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["email_verification_sent"] is True

    User = get_user_model()
    created_user = User.objects.get(username="cliente_confirmacao")
    profile = UserProfile.objects.get(user=created_user)
    assert profile.email_verification_token_hash
    assert profile.email_verification_last_sent_at is not None
    assert (
        profile.email_verification_last_client_base_url
        == "https://anderson-cats-tri-consistently.trycloudflare.com"
    )

    assert len(mail.outbox) == 1
    assert (
        "https://anderson-cats-tri-consistently.trycloudflare.com/"
        "conta/confirmar-email?token="
    ) in mail.outbox[0].body


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_accounts_email_verification_confirm_endpoint_valida_token(anonymous_client):
    register_response = anonymous_client.post(
        "/api/v1/accounts/register/",
        {
            "username": "cliente_confirm_token",
            "password": "Senha_Forte_123",
            "email": "cliente_confirm_token@example.com",
            "first_name": "Cliente",
            "last_name": "Token",
        },
        format="json",
        HTTP_ORIGIN="https://webclient-dev.trycloudflare.com",
    )
    assert register_response.status_code == 201
    assert len(mail.outbox) == 1

    body = mail.outbox[0].body
    match = re.search(r"token=([A-Za-z0-9_\-]+)", body)
    assert match is not None
    token = match.group(1)

    confirm_response = anonymous_client.get(
        "/api/v1/accounts/email-verification/confirm/",
        {"token": token},
    )
    assert confirm_response.status_code == 200
    assert confirm_response.json()["email_verified"] is True

    User = get_user_model()
    user = User.objects.get(username="cliente_confirm_token")
    profile = UserProfile.objects.get(user=user)
    assert profile.email_verified_at is not None
    assert profile.email_verification_token_hash == ""
    assert profile.email_verification_token_created_at is None


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    ACCOUNTS_ALLOW_REQUEST_CLIENT_BASE_URL=True,
    ACCOUNTS_CLIENT_BASE_URL_HTTPS_ONLY=False,
)
def test_accounts_email_verification_resend_usa_origem_ativa(client, admin_user):
    response = client.post(
        "/api/v1/accounts/email-verification/resend/",
        {},
        format="json",
        HTTP_ORIGIN="https://novo-endereco-dev.trycloudflare.com",
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["sent"] is True
    assert payload["client_base_url"] == "https://novo-endereco-dev.trycloudflare.com"

    profile = UserProfile.objects.get(user=admin_user)
    assert (
        profile.email_verification_last_client_base_url
        == "https://novo-endereco-dev.trycloudflare.com"
    )


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    ACCOUNTS_ALLOW_REQUEST_CLIENT_BASE_URL=False,
    ACCOUNTS_CLIENT_BASE_URL_HTTPS_ONLY=True,
    ACCOUNTS_CLIENT_BASE_URL_FALLBACK="https://app.mrquentinha.com.br",
)
@pytest.mark.parametrize("request_source", ["origin", "referer", "body"])
def test_accounts_resend_prod_ignora_url_hostil_e_usa_canonica(
    client,
    admin_user,
    request_source,
):
    config = ensure_portal_config()
    config.client_base_url = "https://app.mrquentinha.com.br"
    config.save(update_fields=["client_base_url", "updated_at"])
    hostile_url = "https://hostil.example"
    data = {}
    request_headers = {}
    if request_source == "origin":
        request_headers["HTTP_ORIGIN"] = hostile_url
    elif request_source == "referer":
        request_headers["HTTP_REFERER"] = f"{hostile_url}/conta"
    else:
        data["preferred_client_base_url"] = hostile_url

    response = client.post(
        "/api/v1/accounts/email-verification/resend/",
        data,
        format="json",
        **request_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["client_base_url"] == "https://app.mrquentinha.com.br"
    assert "token" not in payload
    assert hostile_url not in str(payload)
    profile = UserProfile.objects.get(user=admin_user)
    assert (
        profile.email_verification_last_client_base_url
        == "https://app.mrquentinha.com.br"
    )
    assert len(mail.outbox) == 1
    assert hostile_url not in mail.outbox[0].body
    assert "https://app.mrquentinha.com.br/conta/confirmar-email?token=" in (
        mail.outbox[0].body
    )


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    ACCOUNTS_ALLOW_REQUEST_CLIENT_BASE_URL=True,
    ACCOUNTS_CLIENT_BASE_URL_HTTPS_ONLY=True,
    ACCOUNTS_CLIENT_BASE_URL_FALLBACK="https://app.mrquentinha.com.br",
)
@pytest.mark.parametrize(
    "unsafe_origin",
    [
        "javascript://hostil.example",
        "ftp://hostil.example",
        "https://usuario@hostil.example",
    ],
)
def test_accounts_resend_prod_like_rejeita_origem_insegura_e_config_http(
    client,
    admin_user,
    unsafe_origin,
):
    config = ensure_portal_config()
    type(config).objects.filter(pk=config.pk).update(
        client_base_url="http://localhost:3001"
    )

    response = client.post(
        "/api/v1/accounts/email-verification/resend/",
        {},
        format="json",
        HTTP_ORIGIN=unsafe_origin,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["client_base_url"] == "https://app.mrquentinha.com.br"
    assert payload["client_base_url"].startswith("https://")
    assert "localhost" not in str(payload)
    assert "token" not in payload
    profile = UserProfile.objects.get(user=admin_user)
    assert (
        profile.email_verification_last_client_base_url
        == "https://app.mrquentinha.com.br"
    )


@override_settings(
    ACCOUNTS_ALLOW_REQUEST_CLIENT_BASE_URL=False,
    ACCOUNTS_CLIENT_BASE_URL_HTTPS_ONLY=True,
    ACCOUNTS_CLIENT_BASE_URL_FALLBACK="https://app.mrquentinha.com.br",
)
def test_resolve_client_base_url_usa_fallback_quando_portal_indisponivel(
    monkeypatch,
):
    monkeypatch.setattr(
        "apps.portal.services.ensure_portal_config",
        _raise_portal_database_error,
    )

    assert (
        resolve_client_base_url(preferred_base_url="https://hostil.example")
        == "https://app.mrquentinha.com.br"
    )


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    ACCOUNTS_ALLOW_REQUEST_CLIENT_BASE_URL=False,
    ACCOUNTS_CLIENT_BASE_URL_HTTPS_ONLY=True,
    ACCOUNTS_CLIENT_BASE_URL_FALLBACK="https://app.mrquentinha.com.br",
)
def test_accounts_register_usa_fallback_quando_portal_indisponivel(
    anonymous_client,
    monkeypatch,
):
    monkeypatch.setattr(
        "apps.portal.services.ensure_portal_config",
        _raise_portal_database_error,
    )
    hostile_url = "https://hostil.example"

    response = anonymous_client.post(
        "/api/v1/accounts/register/",
        {
            "username": "cliente_fallback_portal",
            "password": "Senha_Forte_123",
            "email": "cliente_fallback_portal@example.com",
            "first_name": "Cliente",
            "last_name": "Fallback",
        },
        format="json",
        HTTP_ORIGIN=hostile_url,
    )

    assert response.status_code == 201
    payload = response.json()
    assert "token" not in payload
    assert hostile_url not in str(payload)
    User = get_user_model()
    profile = UserProfile.objects.get(
        user=User.objects.get(username="cliente_fallback_portal")
    )
    assert (
        profile.email_verification_last_client_base_url
        == "https://app.mrquentinha.com.br"
    )
    assert len(mail.outbox) == 1
    assert hostile_url not in mail.outbox[0].body
    assert "https://app.mrquentinha.com.br/conta/confirmar-email?token=" in (
        mail.outbox[0].body
    )


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    ACCOUNTS_ALLOW_REQUEST_CLIENT_BASE_URL=False,
    ACCOUNTS_CLIENT_BASE_URL_HTTPS_ONLY=True,
    ACCOUNTS_CLIENT_BASE_URL_FALLBACK="https://app.mrquentinha.com.br",
)
def test_accounts_resend_usa_fallback_quando_portal_indisponivel(
    client,
    admin_user,
    monkeypatch,
):
    monkeypatch.setattr(
        "apps.portal.services.ensure_portal_config",
        _raise_portal_database_error,
    )
    hostile_url = "https://hostil.example"

    response = client.post(
        "/api/v1/accounts/email-verification/resend/",
        {},
        format="json",
        HTTP_ORIGIN=hostile_url,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["client_base_url"] == "https://app.mrquentinha.com.br"
    assert "token" not in payload
    assert hostile_url not in str(payload)
    profile = UserProfile.objects.get(user=admin_user)
    assert (
        profile.email_verification_last_client_base_url
        == "https://app.mrquentinha.com.br"
    )
    assert len(mail.outbox) == 1
    assert hostile_url not in mail.outbox[0].body


@pytest.mark.django_db
def test_accounts_register_rejeita_senha_fraca(anonymous_client):
    response = anonymous_client.post(
        "/api/v1/accounts/register/",
        {
            "username": "cliente_fraco",
            "password": "senhafraca",
            "email": "cliente_fraco@example.com",
        },
        format="json",
    )

    assert response.status_code == 400
    payload = response.json()
    assert "password" in payload


@pytest.mark.django_db
def test_accounts_token_e_me_retorna_usuario_autenticado_com_roles(anonymous_client):
    User = get_user_model()
    user = User.objects.create_user(
        username="cliente_login",
        password="senha_login_123",
        email="cliente_login@example.com",
    )
    ensure_default_roles()
    assign_roles_to_user(user=user, role_codes=[SystemRole.CLIENTE], replace=True)
    profile, _created = UserProfile.objects.get_or_create(user=user)
    profile.email_verified_at = timezone.now()
    profile.save(update_fields=["email_verified_at", "updated_at"])

    token_response = anonymous_client.post(
        "/api/v1/accounts/token/",
        {
            "username": "cliente_login",
            "password": "senha_login_123",
        },
        format="json",
    )
    assert token_response.status_code == 200

    access = token_response.json()["access"]
    me_response = anonymous_client.get(
        "/api/v1/accounts/me/",
        HTTP_AUTHORIZATION=f"Bearer {access}",
    )

    assert me_response.status_code == 200
    payload = me_response.json()
    assert payload["username"] == "cliente_login"
    assert SystemRole.CLIENTE in payload["roles"]


@pytest.mark.django_db
def test_accounts_token_bloqueia_cliente_sem_email_validado(anonymous_client):
    User = get_user_model()
    user = User.objects.create_user(
        username="cliente_sem_validacao",
        password="senha_login_123",
        email="cliente_sem_validacao@example.com",
    )
    ensure_default_roles()
    assign_roles_to_user(user=user, role_codes=[SystemRole.CLIENTE], replace=True)

    token_response = anonymous_client.post(
        "/api/v1/accounts/token/",
        {
            "username": "cliente_sem_validacao",
            "password": "senha_login_123",
        },
        format="json",
    )

    assert token_response.status_code == 401
    assert "Conta nao validada" in str(token_response.json().get("detail", ""))


@pytest.mark.django_db
def test_accounts_token_permite_admin_com_papel_cliente_sem_email_validado(
    anonymous_client,
):
    User = get_user_model()
    user = User.objects.create_user(
        username="gestor_com_cliente",
        password="senha_login_123",
        email="gestor_com_cliente@example.com",
    )
    ensure_default_roles()
    assign_roles_to_user(
        user=user,
        role_codes=[SystemRole.CLIENTE, SystemRole.ADMIN],
        replace=True,
    )

    token_response = anonymous_client.post(
        "/api/v1/accounts/token/",
        {
            "username": "gestor_com_cliente",
            "password": "senha_login_123",
        },
        format="json",
    )

    assert token_response.status_code == 200
    assert "access" in token_response.json()


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_accounts_email_verification_resend_publico_por_identifier(anonymous_client):
    User = get_user_model()
    User.objects.create_user(
        username="cliente_public_resend",
        password="Senha_Forte_123",
        email="cliente_public_resend@example.com",
    )

    response = anonymous_client.post(
        "/api/v1/accounts/email-verification/resend/",
        {
            "identifier": "cliente_public_resend",
        },
        format="json",
        HTTP_ORIGIN="https://cliente-publico-dev.trycloudflare.com",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["sent"] is True

    profile = UserProfile.objects.get(user__username="cliente_public_resend")
    assert (
        profile.email_verification_last_client_base_url
        == "https://cliente-publico-dev.trycloudflare.com"
    )


@pytest.mark.django_db
def test_accounts_roles_assign_exige_admin(client, anonymous_client):
    User = get_user_model()

    target_user = User.objects.create_user(
        username="usuario_alvo",
        password="usuario_alvo_123",
    )
    operador_cliente = User.objects.create_user(
        username="operador_cliente",
        password="operador_cliente_123",
    )

    ensure_default_roles()
    assign_roles_to_user(
        user=operador_cliente,
        role_codes=[SystemRole.CLIENTE],
        replace=True,
    )

    anonymous_client.force_authenticate(user=operador_cliente)
    forbidden_response = anonymous_client.post(
        f"/api/v1/accounts/users/{target_user.id}/roles/",
        {
            "role_codes": [SystemRole.FINANCEIRO],
            "replace": True,
        },
        format="json",
    )
    assert forbidden_response.status_code == 403

    allowed_response = client.post(
        f"/api/v1/accounts/users/{target_user.id}/roles/",
        {
            "role_codes": [SystemRole.FINANCEIRO, SystemRole.COMPRAS],
            "replace": True,
        },
        format="json",
    )

    assert allowed_response.status_code == 200
    assert set(allowed_response.json()["role_codes"]) == {
        SystemRole.FINANCEIRO,
        SystemRole.COMPRAS,
    }


@pytest.mark.django_db
def test_catalog_menu_publico_readonly_sem_auth(anonymous_client):
    by_date_response = anonymous_client.get("/api/v1/catalog/menus/by-date/2026-03-01/")
    assert by_date_response.status_code in {200, 404}

    today_response = anonymous_client.get("/api/v1/catalog/menus/today/")
    assert today_response.status_code in {200, 404}


@pytest.mark.django_db
def test_accounts_users_list_requer_admin(client, anonymous_client):
    User = get_user_model()

    target_user = User.objects.create_user(
        username="operador_financeiro",
        password="operador_financeiro_123",
        email="operador_financeiro@example.com",
        first_name="Operador",
        last_name="Financeiro",
    )

    ensure_default_roles()
    assign_roles_to_user(
        user=target_user,
        role_codes=[SystemRole.FINANCEIRO],
        replace=True,
    )

    allowed_response = client.get("/api/v1/accounts/users/")
    assert allowed_response.status_code == 200

    payload = allowed_response.json()
    assert isinstance(payload, list)

    created_payload = next(item for item in payload if item["id"] == target_user.id)
    assert created_payload["username"] == "operador_financeiro"
    assert set(created_payload["roles"]) == {SystemRole.FINANCEIRO}
    assert created_payload["email_verified"] is False
    assert created_payload["essential_profile_complete"] is False
    assert "email_verificado" in created_payload["missing_essential_profile_fields"]

    operador_cliente = User.objects.create_user(
        username="operador_cliente_list",
        password="operador_cliente_list_123",
    )
    assign_roles_to_user(
        user=operador_cliente,
        role_codes=[SystemRole.CLIENTE],
        replace=True,
    )

    anonymous_client.force_authenticate(user=operador_cliente)
    forbidden_response = anonymous_client.get("/api/v1/accounts/users/")
    assert forbidden_response.status_code == 403


@pytest.mark.django_db
def test_accounts_users_retrieve_retorna_roles(client):
    User = get_user_model()

    target_user = User.objects.create_user(
        username="estoquista_1",
        password="estoquista_123",
    )

    ensure_default_roles()
    assign_roles_to_user(
        user=target_user,
        role_codes=[SystemRole.ESTOQUE, SystemRole.COMPRAS],
        replace=True,
    )

    response = client.get(f"/api/v1/accounts/users/{target_user.id}/")
    assert response.status_code == 200

    payload = response.json()
    assert payload["id"] == target_user.id
    assert payload["username"] == "estoquista_1"
    assert set(payload["roles"]) == {SystemRole.ESTOQUE, SystemRole.COMPRAS}


@pytest.mark.django_db
def test_accounts_users_create_admin_com_roles_e_tarefas(client):
    response = client.post(
        "/api/v1/accounts/users/",
        {
            "username": "cozinha_lider",
            "password": "Senha_Forte_987",
            "email": "cozinha_lider@example.com",
            "first_name": "Lider",
            "last_name": "Cozinha",
            "role_codes": [SystemRole.COZINHA],
            "task_codes": ["PRODUCAO_EXECUCAO", "PRODUCAO_PLANEJAMENTO"],
            "is_active": True,
            "is_staff": False,
        },
        format="json",
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["username"] == "cozinha_lider"
    assert set(payload["roles"]) == {SystemRole.COZINHA}
    assert set(payload["task_codes"]) == {"PRODUCAO_EXECUCAO", "PRODUCAO_PLANEJAMENTO"}

    User = get_user_model()
    created_user = User.objects.get(username="cozinha_lider")
    assert created_user.check_password("Senha_Forte_987")
    assert (
        UserTaskAssignment.objects.filter(
            user=created_user, task__code="PRODUCAO_EXECUCAO"
        ).exists()
        is True
    )


@pytest.mark.django_db
def test_accounts_users_update_admin_altera_status_e_senha(client):
    User = get_user_model()
    target_user = User.objects.create_user(
        username="operador_update",
        password="Senha_Antiga_123",
        email="operador_update@example.com",
        first_name="Operador",
        last_name="Antigo",
    )
    ensure_default_roles()
    assign_roles_to_user(
        user=target_user, role_codes=[SystemRole.ESTOQUE], replace=True
    )

    response = client.patch(
        f"/api/v1/accounts/users/{target_user.id}/",
        {
            "first_name": "Operador Novo",
            "last_name": "Sobrenome Novo",
            "is_active": False,
            "password": "Senha_Nova_123",
        },
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["first_name"] == "Operador Novo"
    assert payload["is_active"] is False

    target_user.refresh_from_db()
    assert target_user.first_name == "Operador Novo"
    assert target_user.last_name == "Sobrenome Novo"
    assert target_user.is_active is False
    assert target_user.check_password("Senha_Nova_123")


@pytest.mark.django_db
def test_accounts_users_assign_tasks_exige_admin(client, anonymous_client):
    User = get_user_model()

    target_user = User.objects.create_user(
        username="usuario_com_tarefas",
        password="usuario_com_tarefas_123",
    )
    operador_cozinha = User.objects.create_user(
        username="operador_sem_admin",
        password="operador_sem_admin_123",
    )
    ensure_default_roles()
    assign_roles_to_user(
        user=operador_cozinha,
        role_codes=[SystemRole.COZINHA],
        replace=True,
    )

    anonymous_client.force_authenticate(user=operador_cozinha)
    forbidden_response = anonymous_client.post(
        f"/api/v1/accounts/users/{target_user.id}/tasks/",
        {
            "task_codes": ["PRODUCAO_EXECUCAO"],
            "replace": True,
        },
        format="json",
    )
    assert forbidden_response.status_code == 403

    allowed_response = client.post(
        f"/api/v1/accounts/users/{target_user.id}/tasks/",
        {
            "task_codes": ["PRODUCAO_EXECUCAO", "ESTOQUE_OPERACAO"],
            "replace": True,
        },
        format="json",
    )

    assert allowed_response.status_code == 200
    assert set(allowed_response.json()["task_codes"]) == {
        "PRODUCAO_EXECUCAO",
        "ESTOQUE_OPERACAO",
    }


@pytest.mark.django_db
def test_accounts_task_categories_list_requer_admin(client, anonymous_client):
    allowed_response = client.get("/api/v1/accounts/task-categories/")
    assert allowed_response.status_code == 200
    payload = allowed_response.json()
    assert isinstance(payload, list)
    assert any(item["code"] == "OPERACAO_PRODUCAO" for item in payload)
    categoria_producao = next(
        item for item in payload if item["code"] == "OPERACAO_PRODUCAO"
    )
    assert any(
        task["code"] == "PRODUCAO_EXECUCAO" for task in categoria_producao["tasks"]
    )

    User = get_user_model()
    operador = User.objects.create_user(
        username="operador_sem_permissao",
        password="operador_sem_permissao_123",
    )
    ensure_default_roles()
    assign_roles_to_user(user=operador, role_codes=[SystemRole.COZINHA], replace=True)
    anonymous_client.force_authenticate(user=operador)
    forbidden_response = anonymous_client.get("/api/v1/accounts/task-categories/")
    assert forbidden_response.status_code == 403


@pytest.mark.django_db
def test_accounts_me_retorna_modulos_permitidos_sem_areas_tecnicas_para_nao_admin(
    anonymous_client,
):
    User = get_user_model()
    user = User.objects.create_user(
        username="cozinha_acesso",
        password="cozinha_acesso_123",
        email="cozinha_acesso@example.com",
    )
    ensure_default_roles()
    assign_roles_to_user(user=user, role_codes=[SystemRole.COZINHA], replace=True)
    anonymous_client.force_authenticate(user=user)

    response = anonymous_client.get("/api/v1/accounts/me/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["can_access_technical_admin"] is False
    assert "portal" not in payload["allowed_admin_module_slugs"]
    assert "instalacao-deploy" not in payload["allowed_admin_module_slugs"]
    assert "pedidos" in payload["allowed_admin_module_slugs"]


@pytest.mark.django_db
def test_accounts_me_is_staff_sem_papel_nao_recebe_acesso_tecnico(anonymous_client):
    User = get_user_model()
    user = User.objects.create_user(
        username="staff_sem_papel_tecnico",
        password="staff_sem_papel_tecnico_123",
        email="staff_sem_papel_tecnico@example.com",
        is_staff=True,
    )
    anonymous_client.force_authenticate(user=user)

    response = anonymous_client.get("/api/v1/accounts/me/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["can_access_technical_admin"] is False
    assert "portal" not in payload["allowed_admin_module_slugs"]
    assert "instalacao-deploy" not in payload["allowed_admin_module_slugs"]


VALID_GIF_BYTES = (
    b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff"
    b"\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02"
    b"\x02\x4c\x01\x00\x3b"
)


@pytest.mark.django_db
def test_accounts_me_profile_exige_autenticacao(anonymous_client):
    response = anonymous_client.get("/api/v1/accounts/me/profile/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_accounts_me_profile_get_cria_perfil_default(client, admin_user):
    response = client.get("/api/v1/accounts/me/profile/")
    assert response.status_code == 200

    payload = response.json()
    assert payload["user"] == admin_user.id
    assert payload["biometric_status"] == UserProfile.BiometricStatus.NOT_CONFIGURED

    profile = UserProfile.objects.get(user=admin_user)
    assert profile.user_id == admin_user.id


@pytest.mark.django_db
def test_accounts_me_profile_patch_atualiza_campos_textuais(client):
    response = client.patch(
        "/api/v1/accounts/me/profile/",
        {
            "full_name": "Administrador Operacional",
            "phone": "(11) 99999-0000",
            "phone_is_whatsapp": True,
            "cpf": "529.982.247-25",
            "postal_code": "01001-000",
            "city": "Sao Paulo",
            "state": "SP",
            "street": "Rua da Operacao",
            "street_number": "245",
            "document_type": "RG",
            "document_number": "55.333.111-9",
        },
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["full_name"] == "Administrador Operacional"
    assert payload["phone"] == "11999990000"
    assert payload["phone_is_whatsapp"] is True
    assert payload["cpf"] == "52998224725"
    assert payload["postal_code"] == "01001000"
    assert payload["city"] == "Sao Paulo"


@pytest.mark.django_db
def test_accounts_me_profile_patch_rejeita_documentos_invalidos(client):
    cpf_response = client.patch(
        "/api/v1/accounts/me/profile/",
        {
            "cpf": "111.111.111-11",
        },
        format="json",
    )
    assert cpf_response.status_code == 400
    assert "cpf" in cpf_response.json()

    cpf_sequencial_response = client.patch(
        "/api/v1/accounts/me/profile/",
        {
            "cpf": "123.456.789-09",
        },
        format="json",
    )
    assert cpf_sequencial_response.status_code == 400
    assert "cpf" in cpf_sequencial_response.json()

    cnpj_response = client.patch(
        "/api/v1/accounts/me/profile/",
        {
            "cnpj": "11.111.111/1111-11",
        },
        format="json",
    )
    assert cnpj_response.status_code == 400
    assert "cnpj" in cnpj_response.json()


@pytest.mark.django_db
def test_accounts_me_profile_patch_rejeita_telefone_invalido(client):
    response = client.patch(
        "/api/v1/accounts/me/profile/",
        {
            "phone": "12345",
        },
        format="json",
    )
    assert response.status_code == 400
    assert "phone" in response.json()


@pytest.mark.django_db
def test_accounts_lookup_cep_publico_retorna_endereco(anonymous_client, monkeypatch):
    def _fake_lookup_address_by_cep(*, cep: str):
        assert cep == "01001000"
        return {
            "postal_code": "01001000",
            "street": "Praca da Se",
            "neighborhood": "Se",
            "city": "Sao Paulo",
            "state": "SP",
            "source": "correios",
        }

    monkeypatch.setattr(
        "apps.accounts.views.lookup_address_by_cep",
        _fake_lookup_address_by_cep,
    )

    response = anonymous_client.get(
        "/api/v1/accounts/lookup-cep/",
        {"cep": "01001-000"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["postal_code"] == "01001000"
    assert payload["city"] == "Sao Paulo"


@pytest.mark.django_db
def test_accounts_lookup_cep_retorna_404_quando_nao_encontrado(
    anonymous_client, monkeypatch
):
    def _fake_lookup_not_found(*, cep: str):
        raise CepLookupNotFoundError(f"CEP {cep} nao encontrado.")

    monkeypatch.setattr(
        "apps.accounts.views.lookup_address_by_cep",
        _fake_lookup_not_found,
    )

    response = anonymous_client.get(
        "/api/v1/accounts/lookup-cep/",
        {"cep": "99999-999"},
    )

    assert response.status_code == 404
    assert "nao encontrado" in response.json()["detail"].lower()


@pytest.mark.django_db
def test_accounts_lookup_cep_rejeita_formato_invalido(anonymous_client):
    response = anonymous_client.get(
        "/api/v1/accounts/lookup-cep/",
        {"cep": "123"},
    )

    assert response.status_code == 400
    assert "cep" in response.json()


@pytest.mark.django_db
def test_accounts_me_profile_patch_uploads_documentos_e_biometria(client):
    response = client.patch(
        "/api/v1/accounts/me/profile/",
        {
            "profile_photo": SimpleUploadedFile(
                "foto-perfil.gif",
                VALID_GIF_BYTES,
                content_type="image/gif",
            ),
            "document_front_image": SimpleUploadedFile(
                "documento-frente.gif",
                VALID_GIF_BYTES,
                content_type="image/gif",
            ),
            "biometric_photo": SimpleUploadedFile(
                "biometria.gif",
                VALID_GIF_BYTES,
                content_type="image/gif",
            ),
        },
        format="multipart",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["profile_photo_url"]
    assert payload["document_front_image_url"]
    assert payload["biometric_photo_url"]
    assert "/api/v1/accounts/profile-media/" in payload["profile_photo_url"]
    assert "/api/v1/accounts/profile-media/" in payload["document_front_image_url"]
    assert "/api/v1/accounts/profile-media/" in payload["biometric_photo_url"]
    assert payload["biometric_status"] == UserProfile.BiometricStatus.PENDING_REVIEW
    assert payload["biometric_captured_at"] is not None


@pytest.mark.django_db
def test_accounts_profile_media_signed_url_funciona(client):
    response = client.patch(
        "/api/v1/accounts/me/profile/",
        {
            "document_front_image": SimpleUploadedFile(
                "documento-frente.gif",
                VALID_GIF_BYTES,
                content_type="image/gif",
            ),
        },
        format="multipart",
    )
    assert response.status_code == 200

    media_url = response.json()["document_front_image_url"]
    assert media_url

    media_response = client.get(media_url)
    assert media_response.status_code == 200
    assert media_response.get("Cache-Control") == "private, no-store"


@pytest.mark.django_db
def test_accounts_media_direta_sensivel_retorna_403(client):
    response = client.patch(
        "/api/v1/accounts/me/profile/",
        {
            "document_front_image": SimpleUploadedFile(
                "documento-frente.gif",
                VALID_GIF_BYTES,
                content_type="image/gif",
            ),
        },
        format="multipart",
    )
    assert response.status_code == 200

    profile = UserProfile.objects.order_by("id").first()
    assert profile is not None
    assert profile.document_front_image.name

    direct_media_path = f"/media/{profile.document_front_image.name}"
    direct_response = client.get(direct_media_path)
    assert direct_response.status_code == 403


TEST_FERNET_KEY = base64.urlsafe_b64encode(bytes(range(32))).decode("ascii")


PROD_SETTINGS_STRONG_ENV = {
    "DATABASE_URL": "postgresql://settings_test@127.0.0.1/settings_test",
    "SECRET_KEY": "S" * 40,
    "FIELD_ENCRYPTION_KEY": TEST_FERNET_KEY,
    "FIELD_HASH_SALT": "H" * 40,
    "FIELD_ENCRYPTION_STRICT": "true",
    "PAYMENTS_WEBHOOK_TOKEN": "W" * 40,
    "ALLOWED_HOSTS": "localhost",
}


def _run_prod_settings_import(*, variable_name: str = "", value=None):
    backend_root = Path(__file__).resolve().parents[1]
    process_env = os.environ.copy()
    process_env.update(PROD_SETTINGS_STRONG_ENV)
    process_env["PYTHONPATH"] = str(backend_root / "src")
    process_env["DJANGO_SETTINGS_MODULE"] = "config.settings.prod"
    if variable_name:
        if value is None:
            process_env.pop(variable_name, None)
        else:
            process_env[variable_name] = str(value)

    return subprocess.run(
        [sys.executable, "-c", "import config.settings.prod"],
        cwd=backend_root,
        env=process_env,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )


@pytest.mark.parametrize(
    "variable_name,value,expected_category",
    [
        ("SECRET_KEY", None, "SECRET_KEY"),
        ("SECRET_KEY", "short", "SECRET_KEY"),
        ("SECRET_KEY", "django-insecure-" + ("S" * 40), "SECRET_KEY"),
        ("FIELD_ENCRYPTION_KEY", None, "FIELD_ENCRYPTION_KEY"),
        ("FIELD_ENCRYPTION_KEY", "short", "FIELD_ENCRYPTION_KEY"),
        ("FIELD_ENCRYPTION_KEY", "E" * 44, "FIELD_ENCRYPTION_KEY"),
        ("FIELD_HASH_SALT", None, "FIELD_HASH_SALT"),
        ("FIELD_HASH_SALT", "short", "FIELD_HASH_SALT"),
        ("FIELD_ENCRYPTION_STRICT", "false", "FIELD_ENCRYPTION_STRICT"),
        ("PAYMENTS_WEBHOOK_TOKEN", None, "PAYMENTS_WEBHOOK_TOKEN"),
        ("PAYMENTS_WEBHOOK_TOKEN", "short", "PAYMENTS_WEBHOOK_TOKEN"),
        (
            "PAYMENTS_WEBHOOK_TOKEN",
            "dev-mrquentinha-webhook-token" + ("W" * 40),
            "PAYMENTS_WEBHOOK_TOKEN",
        ),
    ],
)
def test_prod_settings_rejeita_categoria_critica_insegura(
    variable_name,
    value,
    expected_category,
):
    result = _run_prod_settings_import(variable_name=variable_name, value=value)

    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert expected_category in output
    for strong_value in PROD_SETTINGS_STRONG_ENV.values():
        if len(strong_value) >= 32:
            assert strong_value not in output


def test_prod_settings_aceita_ambiente_forte_sem_expor_valores():
    result = _run_prod_settings_import()

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
