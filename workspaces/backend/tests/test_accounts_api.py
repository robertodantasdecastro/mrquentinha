import re

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone

from apps.accounts.models import UserProfile, UserRole
from apps.accounts.services import (
    SystemRole,
    assign_roles_to_user,
    ensure_default_roles,
)


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


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
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
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
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
            "cpf": "123.456.789-09",
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
    assert payload["cpf"] == "12345678909"
    assert payload["postal_code"] == "01001000"
    assert payload["city"] == "Sao Paulo"


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
    assert payload["biometric_status"] == UserProfile.BiometricStatus.PENDING_REVIEW
    assert payload["biometric_captured_at"] is not None
