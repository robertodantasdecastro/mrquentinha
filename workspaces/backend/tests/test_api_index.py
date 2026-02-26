def test_api_index_endpoint_retorna_payload_esperado(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "app": "mrquentinha",
        "version": "v1",
        "endpoints": {
            "health": "/api/v1/health",
            "accounts": "/api/v1/accounts",
            "catalog": "/api/v1/catalog",
            "orders": "/api/v1/orders",
            "orders_ops_dashboard": "/api/v1/orders/ops/dashboard/",
            "orders_ops_realtime": "/api/v1/orders/ops/realtime/",
            "finance": "/api/v1/finance",
            "production": "/api/v1/production",
            "ocr": "/api/v1/ocr",
            "portal": "/api/v1/portal",
            "mobile_release_latest": "/api/v1/portal/mobile/releases/latest/",
            "personal_finance": "/api/v1/personal-finance",
        },
    }


def test_favicon_redirect(client):
    response = client.get("/favicon.ico")

    assert response.status_code == 302
    assert response["Location"] == "/static/brand/icon_symbol.svg"
