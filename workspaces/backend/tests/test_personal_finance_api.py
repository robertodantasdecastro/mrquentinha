import pytest

from apps.personal_finance.models import PersonalEntry


@pytest.mark.django_db
def test_personal_finance_endpoints_requerem_autenticacao(anonymous_client):
    response = anonymous_client.get("/api/v1/personal-finance/accounts/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_personal_finance_crud_basico_por_usuario(client):
    account_response = client.post(
        "/api/v1/personal-finance/accounts/",
        {
            "name": "Carteira",
            "type": "CASH",
            "is_active": True,
        },
        format="json",
    )
    assert account_response.status_code == 201
    account_id = account_response.json()["id"]

    category_response = client.post(
        "/api/v1/personal-finance/categories/",
        {
            "name": "Alimentacao",
            "direction": "OUT",
            "is_active": True,
        },
        format="json",
    )
    assert category_response.status_code == 201
    category_id = category_response.json()["id"]

    entry_response = client.post(
        "/api/v1/personal-finance/entries/",
        {
            "account": account_id,
            "category": category_id,
            "direction": "OUT",
            "amount": "32.50",
            "entry_date": "2026-02-26",
            "description": "Almoco",
            "metadata": {"origem": "teste"},
        },
        format="json",
    )
    assert entry_response.status_code == 201

    budget_response = client.post(
        "/api/v1/personal-finance/budgets/",
        {
            "category": category_id,
            "month_ref": "2026-02-15",
            "limit_amount": "500.00",
        },
        format="json",
    )
    assert budget_response.status_code == 201
    assert budget_response.json()["month_ref"] == "2026-02-01"

    list_entries_response = client.get(
        "/api/v1/personal-finance/entries/?from=2026-02-01&to=2026-02-28&direction=OUT"
    )
    assert list_entries_response.status_code == 200
    assert len(list_entries_response.json()) == 1


@pytest.mark.django_db
def test_personal_finance_isola_dados_por_owner(
    client, anonymous_client, create_user_with_roles
):
    secondary_user = create_user_with_roles(username="usuario_financas_pessoais")

    anonymous_client.force_authenticate(user=secondary_user)
    create_response = anonymous_client.post(
        "/api/v1/personal-finance/accounts/",
        {
            "name": "Conta secundaria",
            "type": "CHECKING",
            "is_active": True,
        },
        format="json",
    )
    assert create_response.status_code == 201

    list_response = client.get("/api/v1/personal-finance/accounts/")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 0


@pytest.mark.django_db
def test_personal_entry_bloqueia_conta_de_outro_usuario(
    client, anonymous_client, create_user_with_roles
):
    secondary_user = create_user_with_roles(username="outro_dono")

    anonymous_client.force_authenticate(user=secondary_user)
    account_response = anonymous_client.post(
        "/api/v1/personal-finance/accounts/",
        {
            "name": "Conta de outro usuario",
            "type": "CHECKING",
            "is_active": True,
        },
        format="json",
    )
    category_response = anonymous_client.post(
        "/api/v1/personal-finance/categories/",
        {
            "name": "Transporte",
            "direction": "OUT",
            "is_active": True,
        },
        format="json",
    )

    assert account_response.status_code == 201
    assert category_response.status_code == 201

    response = client.post(
        "/api/v1/personal-finance/entries/",
        {
            "account": account_response.json()["id"],
            "category": category_response.json()["id"],
            "direction": "OUT",
            "amount": "10.00",
            "entry_date": "2026-02-26",
        },
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_personal_budget_unico_por_categoria_mes(client):
    category_response = client.post(
        "/api/v1/personal-finance/categories/",
        {
            "name": "Mercado",
            "direction": "OUT",
            "is_active": True,
        },
        format="json",
    )
    assert category_response.status_code == 201

    category_id = category_response.json()["id"]

    first_response = client.post(
        "/api/v1/personal-finance/budgets/",
        {
            "category": category_id,
            "month_ref": "2026-03-10",
            "limit_amount": "700.00",
        },
        format="json",
    )
    assert first_response.status_code == 201
    assert first_response.json()["month_ref"] == "2026-03-01"

    duplicate_response = client.post(
        "/api/v1/personal-finance/budgets/",
        {
            "category": category_id,
            "month_ref": "2026-03-20",
            "limit_amount": "850.00",
        },
        format="json",
    )
    assert duplicate_response.status_code == 400


@pytest.mark.django_db
def test_personal_recurring_rule_materializacao_idempotente(client):
    account_response = client.post(
        "/api/v1/personal-finance/accounts/",
        {
            "name": "Conta recorrente",
            "type": "CHECKING",
            "is_active": True,
        },
        format="json",
    )
    assert account_response.status_code == 201

    category_response = client.post(
        "/api/v1/personal-finance/categories/",
        {
            "name": "Assinaturas",
            "direction": "OUT",
            "is_active": True,
        },
        format="json",
    )
    assert category_response.status_code == 201

    recurring_response = client.post(
        "/api/v1/personal-finance/recurring-rules/",
        {
            "account": account_response.json()["id"],
            "category": category_response.json()["id"],
            "direction": "OUT",
            "amount": "59.90",
            "description": "Streaming",
            "metadata": {"origem": "teste"},
            "frequency": "MONTHLY",
            "interval": 1,
            "start_date": "2026-01-01",
            "next_run_date": "2026-01-01",
            "is_active": True,
        },
        format="json",
    )
    assert recurring_response.status_code == 201
    recurring_rule_id = recurring_response.json()["id"]

    first_materialize = client.post(
        "/api/v1/personal-finance/recurring-rules/materialize/",
        {
            "from_date": "2026-01-01",
            "to_date": "2026-01-31",
            "recurring_rule_id": recurring_rule_id,
        },
        format="json",
    )
    assert first_materialize.status_code == 200
    first_payload = first_materialize.json()
    assert first_payload["entries_created"] == 1
    assert first_payload["entries_skipped"] == 0

    reset_response = client.patch(
        f"/api/v1/personal-finance/recurring-rules/{recurring_rule_id}/",
        {"next_run_date": "2026-01-01"},
        format="json",
    )
    assert reset_response.status_code == 200

    second_materialize = client.post(
        "/api/v1/personal-finance/recurring-rules/materialize/",
        {
            "from_date": "2026-01-01",
            "to_date": "2026-01-31",
            "recurring_rule_id": recurring_rule_id,
        },
        format="json",
    )
    assert second_materialize.status_code == 200
    second_payload = second_materialize.json()
    assert second_payload["entries_created"] == 0
    assert second_payload["entries_skipped"] == 1
    assert PersonalEntry.objects.filter(owner__username="admin_test").count() == 1


@pytest.mark.django_db
def test_personal_finance_summary_monthly_retorna_totais_e_budgets(client):
    account_response = client.post(
        "/api/v1/personal-finance/accounts/",
        {
            "name": "Conta principal",
            "type": "CHECKING",
            "is_active": True,
        },
        format="json",
    )
    assert account_response.status_code == 201
    account_id = account_response.json()["id"]

    income_category_response = client.post(
        "/api/v1/personal-finance/categories/",
        {
            "name": "Salario",
            "direction": "IN",
            "is_active": True,
        },
        format="json",
    )
    assert income_category_response.status_code == 201

    market_category_response = client.post(
        "/api/v1/personal-finance/categories/",
        {
            "name": "Mercado mensal",
            "direction": "OUT",
            "is_active": True,
        },
        format="json",
    )
    assert market_category_response.status_code == 201

    transport_category_response = client.post(
        "/api/v1/personal-finance/categories/",
        {
            "name": "Transporte app",
            "direction": "OUT",
            "is_active": True,
        },
        format="json",
    )
    assert transport_category_response.status_code == 201

    entries_payload = [
        {
            "account": account_id,
            "category": income_category_response.json()["id"],
            "direction": "IN",
            "amount": "1200.00",
            "entry_date": "2026-02-05",
            "description": "Salario",
        },
        {
            "account": account_id,
            "category": market_category_response.json()["id"],
            "direction": "OUT",
            "amount": "200.00",
            "entry_date": "2026-02-12",
            "description": "Compra mensal",
        },
        {
            "account": account_id,
            "category": transport_category_response.json()["id"],
            "direction": "OUT",
            "amount": "100.00",
            "entry_date": "2026-02-14",
            "description": "Corridas",
        },
    ]
    for payload in entries_payload:
        response = client.post(
            "/api/v1/personal-finance/entries/",
            payload,
            format="json",
        )
        assert response.status_code == 201

    budget_response = client.post(
        "/api/v1/personal-finance/budgets/",
        {
            "category": market_category_response.json()["id"],
            "month_ref": "2026-02-20",
            "limit_amount": "250.00",
        },
        format="json",
    )
    assert budget_response.status_code == 201

    summary_response = client.get(
        "/api/v1/personal-finance/summary/monthly/?month=2026-02"
    )
    assert summary_response.status_code == 200
    payload = summary_response.json()

    assert payload["month_ref"] == "2026-02-01"
    assert payload["totals"]["total_in"] == "1200.00"
    assert payload["totals"]["total_out"] == "300.00"
    assert payload["totals"]["balance"] == "900.00"
    assert payload["entries_count"] == 3
    assert len(payload["top_categories"]) >= 2

    market_budget = next(
        item for item in payload["budgets"] if item["category_name"] == "Mercado mensal"
    )
    assert market_budget["spent_amount"] == "200.00"
    assert market_budget["remaining_amount"] == "50.00"
    assert market_budget["consumption_percent"] == "80.00"
    assert market_budget["status"] == "ALERTA"


@pytest.mark.django_db
def test_personal_import_preview_confirm_com_deduplicacao_basica(client):
    account_response = client.post(
        "/api/v1/personal-finance/accounts/",
        {
            "name": "Conta importacao",
            "type": "CHECKING",
            "is_active": True,
        },
        format="json",
    )
    assert account_response.status_code == 201
    account_name = account_response.json()["name"]

    category_response = client.post(
        "/api/v1/personal-finance/categories/",
        {
            "name": "Mercado import",
            "direction": "OUT",
            "is_active": True,
        },
        format="json",
    )
    assert category_response.status_code == 201
    category_name = category_response.json()["name"]

    csv_content = (
        "entry_date,direction,amount,account,category,description\n"
        f"2026-02-01,OUT,50.00,{account_name},{category_name},Compra 1\n"
        f"2026-02-01,OUT,50.00,{account_name},{category_name},Compra 1\n"
        f"2026-02-02,INVALID,15.00,{account_name},{category_name},Linha invalida\n"
    )

    preview_response = client.post(
        "/api/v1/personal-finance/imports/preview/",
        {
            "csv_content": csv_content,
            "source_filename": "import-test.csv",
            "delimiter": ",",
        },
        format="json",
    )
    assert preview_response.status_code == 201
    preview_payload = preview_response.json()

    assert preview_payload["status"] == "PREVIEWED"
    assert preview_payload["rows_total"] == 3
    assert preview_payload["rows_valid"] == 2
    assert preview_payload["rows_invalid"] == 1

    import_job_id = preview_payload["id"]
    confirm_response = client.post(
        f"/api/v1/personal-finance/imports/{import_job_id}/confirm/",
        {},
        format="json",
    )
    assert confirm_response.status_code == 200
    confirm_payload = confirm_response.json()

    assert confirm_payload["result"]["status"] == "CONFIRMED"
    assert confirm_payload["result"]["imported_count"] == 1
    assert confirm_payload["result"]["skipped_count"] == 1
    assert PersonalEntry.objects.filter(owner__username="admin_test").count() == 1

    idempotent_confirm_response = client.post(
        f"/api/v1/personal-finance/imports/{import_job_id}/confirm/",
        {},
        format="json",
    )
    assert idempotent_confirm_response.status_code == 200
    idempotent_payload = idempotent_confirm_response.json()
    assert idempotent_payload["result"]["status"] == "CONFIRMED"
    assert idempotent_payload["result"]["imported_count"] == 1
    assert idempotent_payload["result"]["skipped_count"] == 1


@pytest.mark.django_db
def test_personal_import_confirm_respeita_ownership(
    client, anonymous_client, create_user_with_roles
):
    account_response = client.post(
        "/api/v1/personal-finance/accounts/",
        {
            "name": "Conta owner",
            "type": "CHECKING",
            "is_active": True,
        },
        format="json",
    )
    assert account_response.status_code == 201

    category_response = client.post(
        "/api/v1/personal-finance/categories/",
        {
            "name": "Mercado owner",
            "direction": "OUT",
            "is_active": True,
        },
        format="json",
    )
    assert category_response.status_code == 201

    csv_content = (
        "entry_date,direction,amount,account,category,description\n"
        "2026-02-01,OUT,50.00,Conta owner,Mercado owner,Compra 1\n"
    )
    preview_response = client.post(
        "/api/v1/personal-finance/imports/preview/",
        {"csv_content": csv_content, "delimiter": ","},
        format="json",
    )
    assert preview_response.status_code == 201
    job_id = preview_response.json()["id"]

    other_user = create_user_with_roles(username="other_personal_owner")
    anonymous_client.force_authenticate(user=other_user)
    response = anonymous_client.post(
        f"/api/v1/personal-finance/imports/{job_id}/confirm/",
        {},
        format="json",
    )

    assert response.status_code == 404
