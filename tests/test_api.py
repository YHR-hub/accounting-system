"""FastAPI 接口测试（阶段3）。无 fastapi 环境时自动跳过。"""
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["database"] in ("sqlite", "postgresql")


def test_ratios():
    r = client.get("/api/ratios")
    assert r.status_code == 200
    assert isinstance(r.json(), dict)


def test_accounts():
    r = client.get("/api/accounts")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and data
    assert {"code", "name", "category", "debit", "credit", "balance"} <= set(data[0])


def test_vouchers():
    r = client.get("/api/vouchers", params={"year": 2026})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.parametrize("path,expected_len", [
    ("/api/reports/balance", None),
    ("/api/reports/income", None),
    ("/api/reports/cashflow", 4),
])
def test_reports(path, expected_len):
    r = client.get(path)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and data
    assert "label" in data[0] and "amount" in data[0]
    if expected_len is not None:
        assert len(data) == expected_len


def test_tax_vat():
    r = client.get("/api/tax/vat", params={"revenue": 113000, "rate": 0.13})
    assert r.status_code == 200
    assert r.json()["tax_amount"] == 13000.0


def test_tax_pit():
    r = client.get("/api/tax/pit", params={"income": 50000})
    assert r.status_code == 200
    body = r.json()
    assert body["total_tax"] == 2480.0
    assert len(body["brackets"]) == 2


def test_tax_vat_rejects_invalid():
    r = client.get("/api/tax/vat", params={"revenue": -1})
    assert r.status_code == 422


def test_openapi_schema():
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert "paths" in r.json()


def _auth_header(username, password):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_login_wrong_password():
    r = client.post("/api/auth/login", json={"username": "admin", "password": "nope"})
    assert r.status_code == 401


def test_login_and_me():
    h = _auth_header("admin", "admin123")
    r = client.get("/api/auth/me", headers=h)
    assert r.status_code == 200
    assert r.json()["role"] == "admin"


def test_me_without_token():
    assert client.get("/api/auth/me").status_code == 401


def _balanced_payload():
    return {
        "date": "2026-06-10",
        "summary": "API测试凭证",
        "entries": [
            {"account_code": "1002", "debit": 100, "credit": 0},
            {"account_code": "6001", "debit": 0, "credit": 100},
        ],
    }


def test_create_requires_auth():
    assert client.post("/api/vouchers", json=_balanced_payload()).status_code == 401


def test_viewer_cannot_create():
    h = _auth_header("viewer", "view123")
    assert client.post("/api/vouchers", headers=h, json=_balanced_payload()).status_code == 403


def test_create_unbalanced_rejected():
    h = _auth_header("admin", "admin123")
    bad = _balanced_payload()
    bad["entries"][1]["credit"] = 90
    assert client.post("/api/vouchers", headers=h, json=bad).status_code == 400


def test_create_and_delete_voucher():
    h = _auth_header("admin", "admin123")
    r = client.post("/api/vouchers", headers=h, json=_balanced_payload())
    assert r.status_code == 201, r.text
    vid = r.json()["id"]
    assert r.json()["voucher_no"].startswith("记-")
    assert client.delete(f"/api/vouchers/{vid}", headers=h).status_code == 204


@pytest.mark.parametrize("path", [
    "/api/inventory/products",
    "/api/inventory/transactions",
    "/api/employees",
    "/api/payroll",
    "/api/assets",
    "/api/projects",
    "/api/budgets",
    "/api/alerts/rules",
    "/api/alerts/history",
    "/api/audit",
    "/api/esg",
])
def test_module_list_endpoints(path):
    r = client.get(path)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
