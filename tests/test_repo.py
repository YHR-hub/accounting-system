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


def test_write_operations(engine):
    repo.bootstrap(engine)
    with Session(engine) as s:
        repo.create_product(s, "P100", "螺丝", unit_price=2.0, quantity=10)
        s.commit()
        pid = next(p["id"] for p in repo.list_products(s) if p["code"] == "P100")

        repo.inventory_in(s, pid, 5, unit_price=2.5)
        s.commit()
        assert next(p["quantity"] for p in repo.list_products(s) if p["id"] == pid) == 15.0

        repo.inventory_out(s, pid, 3)
        s.commit()
        assert next(p["quantity"] for p in repo.list_products(s) if p["id"] == pid) == 12.0

        with pytest.raises(ValueError):
            repo.inventory_out(s, pid, 9999)
        with pytest.raises(ValueError):
            repo.create_product(s, "P100", "重复")

        repo.add_employee(s, "E100", "李四", base_salary=20000, insurance=2000, housing_fund=1000)
        s.commit()
        created = repo.calculate_payroll(s, 2026, 7)
        s.commit()
        assert len(created) == 1
        assert created[0]["income_tax"] == 990.0
        assert repo.calculate_payroll(s, 2026, 7) == []

        repo.add_fixed_asset(s, "打印机", 3000, 36, "2026-01-01")
        repo.add_project(s, "PRJ-100", "新项目", budget=100000)
        s.commit()
        assert any(a["name"] == "打印机" for a in repo.list_fixed_assets(s))
        assert any(p["code"] == "PRJ-100" for p in repo.list_projects(s))


def test_voucher_detail_account_and_trial_balance(engine):
    repo.bootstrap(engine)
    with Session(engine) as s:
        vno = repo.next_voucher_no(s, 2026, 6)
        v = Voucher(voucher_no=vno, date="2026-06-01", summary="测试",
                    fiscal_year=2026, fiscal_month=6)
        s.add(v)
        s.flush()
        s.add(JournalEntry(voucher_id=v.id, account_code="1002",
                           debit=Decimal("100"), credit=Decimal("0")))
        s.add(JournalEntry(voucher_id=v.id, account_code="6001",
                           debit=Decimal("0"), credit=Decimal("100")))
        s.commit()

        detail = repo.get_voucher_detail(s, v.id)
        assert detail is not None
        assert len(detail["entries"]) == 2
        assert detail["entries"][0]["account_name"]  # 关联到了科目名
        assert repo.get_voucher_detail(s, 999999) is None

        repo.add_account(s, "1234", "测试科目", "asset")
        s.commit()
        assert any(a["code"] == "1234" for a in repo.load_accounts(s))
        with pytest.raises(ValueError):
            repo.add_account(s, "1234", "重复", "asset")

        tb = repo.trial_balance_data(s)
        assert tb["balanced"] is True
        assert tb["total_debit"] == tb["total_credit"]
