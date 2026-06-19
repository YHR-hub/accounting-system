"""ORM 数据层测试：在全新空库上经纯 ORM 跑通（证明 SQLite/Postgres 通用）。"""
import os
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from accsys import repo
from accsys.db import make_engine
from accsys.models import JournalEntry, User, Voucher


@pytest.fixture
def engine(tmp_path):
    path = str(tmp_path / "t.db").replace(os.sep, "/")
    return make_engine(f"sqlite:///{path}")


def test_bootstrap_seeds_accounts_and_users(engine):
    repo.bootstrap(engine)
    with Session(engine) as s:
        assert len(repo.load_accounts(s)) == 38
        assert s.scalar(select(func.count()).select_from(User)) == 3


def test_voucher_no_and_balances_and_reports(engine):
    repo.bootstrap(engine)
    with Session(engine) as s:
        vno = repo.next_voucher_no(s, 2026, 6)
        assert vno == "记-2026-06-0001"

        v = Voucher(voucher_no=vno, date="2026-06-01", summary="测试",
                    fiscal_year=2026, fiscal_month=6)
        s.add(v)
        s.flush()
        s.add(JournalEntry(voucher_id=v.id, account_code="1002",
                           debit=Decimal("50000"), credit=Decimal("0")))
        s.add(JournalEntry(voucher_id=v.id, account_code="6001",
                           debit=Decimal("0"), credit=Decimal("50000")))
        s.commit()

        balances = repo.calc_balances(s)
        assert balances["1002"] == Decimal("50000")

        assert repo.next_voucher_no(s, 2026, 6) == "记-2026-06-0002"

        inc = {r["label"]: r["amount"] for r in repo.income_statement_data(s)}
        assert inc["一、营业收入"] == 50000.0
        assert inc["四、净利润"] == 50000.0

        bs_labels = [r["label"] for r in repo.balance_sheet_data(s)]
        assert "资产总计" in bs_labels

        assert len(repo.cash_flow_statement_data(s)) == 4

        ratios = repo.financial_ratios(s)
        assert "毛利率" in ratios and "净利率" in ratios


def test_module_list_functions_with_data(engine):
    repo.bootstrap(engine)
    from accsys.models import Employee, FixedAsset, Product

    with Session(engine) as s:
        s.add(Product(code="P001", name="测试商品", unit="个",
                      unit_price=Decimal("10"), quantity=Decimal("5"), is_active=1))
        s.add(Employee(code="E001", name="张三", department="技术部",
                       base_salary=Decimal("15000"), is_active=1))
        s.add(FixedAsset(name="服务器", original_value=Decimal("100000"),
                         residual_value=Decimal("0"), useful_life_months=60,
                         depreciation_method="straight", purchase_date="2026-01-01",
                         accumulated_deprec=Decimal("20000"), is_active=1))
        s.commit()

        products = repo.list_products(s)
        assert len(products) == 1
        assert products[0]["amount"] == 50.0

        employees = repo.list_employees(s)
        assert len(employees) == 1 and employees[0]["name"] == "张三"

        assets = repo.list_fixed_assets(s)
        assert len(assets) == 1 and assets[0]["net_value"] == 80000.0
