import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

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
