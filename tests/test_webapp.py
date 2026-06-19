"""Flask webapp 接口测试（2b：已迁移到 ORM repo）。无 flask 时跳过。"""
import pytest

pytest.importorskip("flask")

from webapp import app  # noqa: E402

client = app.test_client()


@pytest.mark.parametrize("path", [
    "/",
    "/vouchers",
    "/accounts",
    "/reports",
    "/api/ratios",
    "/api/accounts",
    "/api/vouchers",
    "/api/reports/balance",
    "/api/reports/income",
    "/api/reports/cashflow",
])
def test_webapp_routes_ok(path):
    assert client.get(path).status_code == 200


def test_webapp_api_accounts_shape():
    data = client.get("/api/accounts").get_json()
    assert isinstance(data, list) and data
    assert {"code", "name", "category", "debit", "credit", "balance"} <= set(data[0])
