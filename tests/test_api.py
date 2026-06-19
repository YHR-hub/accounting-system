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
