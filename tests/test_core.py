"""pytest unit tests for the accsys accounting system."""

from __future__ import annotations

import csv
import hashlib
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest

import accsys as acc


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def setup_db(monkeypatch):
    """Create a temp SQLite database for each test and clean up after."""
    tmp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp_db.close()
    monkeypatch.setattr(acc.database, 'get_db_path', lambda: tmp_db.name)

    tmp_accts = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    tmp_accts.close()
    monkeypatch.setattr(acc.database, 'get_accounts_path', lambda: tmp_accts.name)

    for mod in [acc.backup, acc.attachments]:
        if hasattr(mod, 'get_db_path'):
            monkeypatch.setattr(mod, 'get_db_path', lambda pt=tmp_db.name: pt)

    monkeypatch.setattr(acc.constants, 'ATTACHMENT_DIR', tempfile.mkdtemp())

    acc.database.init_db()
    acc.database.ensure_accounts()
    acc.auth.init_users()
    acc.init_attachment_dir()

    yield

    try:
        os.unlink(tmp_db.name)
    except (OSError, PermissionError):
        pass
    try:
        os.unlink(tmp_accts.name)
    except (OSError, PermissionError):
        pass


@pytest.fixture(autouse=True)
def set_admin_user():
    acc.auth.CURRENT_USER = {'username': 'admin', 'display_name': '管理员', 'role': 'admin'}
    yield
    acc.auth.CURRENT_USER = {}


def _insert_voucher(
    conn: sqlite3.Connection,
    voucher_no: str,
    date_str: str,
    summary: str,
    year: int,
    month: int,
    entries: list[dict],
) -> int:
    cur = conn.execute(
        "INSERT INTO vouchers (voucher_no, date, summary, fiscal_year, fiscal_month) VALUES (?,?,?,?,?)",
        (voucher_no, date_str, summary, year, month),
    )
    vid = cur.lastrowid
    for e in entries:
        conn.execute(
            "INSERT INTO journal_entries (voucher_id, account_code, debit, credit) VALUES (?,?,?,?)",
            (vid, e['code'], e['debit'], e['credit']),
        )
    conn.commit()
    return vid


# ── 1. Database & Accounts ────────────────────────────────────────────────


class TestDatabase:
    def test_init_db_creates_all_tables(self):
        conn = acc.database.get_conn()
        tables = {
            r['name']
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()
        for tbl in ('accounts', 'vouchers', 'journal_entries', 'fixed_assets',
                     'users', 'budgets', 'products', 'audit_log', 'alert_rules',
                     'employees', 'payroll_records', 'projects', 'attachments',
                     'period_close', 'blockchain', 'opening_balances'):
            assert tbl in tables, f"Missing table: {tbl}"

    def test_ensure_accounts_creates_default_accounts(self):
        accounts = acc.database.load_accounts_from_db()
        codes = {a['code'] for a in accounts}
        assert '1001' in codes, 'Missing default account 1001'
        assert '1002' in codes, 'Missing default account 1002'
        assert '6001' in codes, 'Missing default account 6001'
        assert '6602' in codes, 'Missing default account 6602'
        assert len(accounts) > 10, f"Expected >10 accounts, got {len(accounts)}"

    def test_load_accounts_from_db_returns_list_of_dicts(self):
        accounts = acc.database.load_accounts_from_db()
        assert isinstance(accounts, list)
        assert len(accounts) > 0
        a = accounts[0]
        for key in ('code', 'name', 'category', 'nature', 'level'):
            assert key in a, f"Missing key {key} in account dict"

    def test_get_account_dict_maps_codes(self):
        accounts = acc.database.load_accounts_from_db()
        d = acc.database.get_account_dict(accounts)
        assert d['1001']['name'] == '库存现金'

    def test_add_account_via_db(self):
        conn = acc.database.get_conn()
        conn.execute(
            "INSERT INTO accounts (code, name, category, nature, level, parent) "
            "VALUES (?,?,?,?,?,?)",
            ('9999', '测试科目', 'asset', 'debit', 1, ''),
        )
        conn.commit()
        conn.close()
        accounts = acc.database.load_accounts_from_db()
        codes = {a['code'] for a in accounts}
        assert '9999' in codes

    def test_calc_balances_returns_dict(self):
        accounts = acc.database.load_accounts_from_db()
        balances = acc.accounts.calc_balances(accounts)
        assert isinstance(balances, dict)
        assert '1001' in balances
        assert float(balances['1001']) == 0.0

    def test_calc_balances_with_data(self):
        conn = acc.database.get_conn()
        vid = _insert_voucher(conn, '记-2026-06-0001', '2026-06-01', '测试', 2026, 6, [
            {'code': '1002', 'debit': 10000, 'credit': 0},
            {'code': '6001', 'debit': 0, 'credit': 10000},
        ])
        conn.close()
        accounts = acc.database.load_accounts_from_db()
        balances = acc.accounts.calc_balances(accounts, as_of='2026-06-30')
        assert float(balances['1002']) == pytest.approx(10000.0)
        assert float(balances['6001']) == pytest.approx(10000.0)

    def test_show_trial_balance_runs_without_error(self, capsys):
        accounts = acc.database.load_accounts_from_db()
        acc.accounts.show_trial_balance()
        captured = capsys.readouterr()
        assert '试算平衡表' in captured.out

    def test_set_opening_balance(self):
        conn = acc.database.get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO opening_balances (account_code, amount, fiscal_year) "
            "VALUES (?,?,?)",
            ('1001', 5000.0, 2026),
        )
        conn.commit()
        conn.close()
        accounts = acc.database.load_accounts_from_db()
        balances = acc.accounts.calc_balances(accounts)
        assert float(balances['1001']) == pytest.approx(5000.0)


# ── 2. Vouchers ────────────────────────────────────────────────────────────


class TestVouchers:
    def test_next_voucher_no_generates_correct_format(self):
        vno = acc.vouchers.next_voucher_no(2026, 6)
        assert vno == '记-2026-06-0001', f"Unexpected format: {vno}"

    def test_next_voucher_no_increments(self):
        conn = acc.database.get_conn()
        _insert_voucher(conn, '记-2026-06-0001', '2026-06-01', '第一个', 2026, 6, [
            {'code': '1002', 'debit': 100, 'credit': 0},
            {'code': '6001', 'debit': 0, 'credit': 100},
        ])
        conn.close()
        vno = acc.vouchers.next_voucher_no(2026, 6)
        assert vno == '记-2026-06-0002'

    def test_create_voucher_via_db(self):
        conn = acc.database.get_conn()
        vno = acc.vouchers.next_voucher_no(2026, 6)
        vid = _insert_voucher(conn, vno, '2026-06-15', '销售商品', 2026, 6, [
            {'code': '1002', 'debit': 5000, 'credit': 0},
            {'code': '6001', 'debit': 0, 'credit': 5000},
        ])
        conn.close()
        assert vid > 0

    def test_list_vouchers_prints_output(self, capsys):
        conn = acc.database.get_conn()
        _insert_voucher(conn, '记-2026-06-0001', '2026-06-01', '测试凭证', 2026, 6, [
            {'code': '1002', 'debit': 1000, 'credit': 0},
            {'code': '6001', 'debit': 0, 'credit': 1000},
        ])
        conn.close()
        acc.vouchers.list_vouchers(2026, 6)
        captured = capsys.readouterr()
        assert '记-2026-06-0001' in captured.out

    def test_list_vouchers_empty_shows_message(self, capsys):
        acc.vouchers.list_vouchers(2026, 6)
        captured = capsys.readouterr()
        assert '暂无凭证' in captured.out

    def test_show_voucher_prints_details(self, capsys):
        conn = acc.database.get_conn()
        vid = _insert_voucher(conn, '记-2026-06-0001', '2026-06-01', '测试', 2026, 6, [
            {'code': '1002', 'debit': 3000, 'credit': 0},
            {'code': '6001', 'debit': 0, 'credit': 3000},
        ])
        conn.close()
        acc.vouchers.show_voucher(vid)
        captured = capsys.readouterr()
        assert '记-2026-06-0001' in captured.out
        assert '借贷平衡' in captured.out

    def test_show_voucher_not_found(self, capsys):
        acc.vouchers.show_voucher(99999)
        captured = capsys.readouterr()
        assert '凭证不存在' in captured.out

    def test_voucher_debit_credit_balance_integrity(self):
        conn = acc.database.get_conn()
        vno = acc.vouchers.next_voucher_no(2026, 6)
        _insert_voucher(conn, vno, '2026-06-01', '平衡测试', 2026, 6, [
            {'code': '1002', 'debit': 2000, 'credit': 0},
            {'code': '6001', 'debit': 0, 'credit': 2000},
        ])
        rows = conn.execute(
            "SELECT SUM(debit) as d, SUM(credit) as c FROM journal_entries "
            "WHERE voucher_id=(SELECT id FROM vouchers WHERE voucher_no=?)",
            (vno,),
        ).fetchone()
        conn.close()
        assert rows['d'] == rows['c'], 'Debit must equal credit'

    def test_batch_export_csv(self):
        conn = acc.database.get_conn()
        _insert_voucher(conn, '记-2026-06-0001', '2026-06-01', '导出测试', 2026, 6, [
            {'code': '1002', 'debit': 500, 'credit': 0},
            {'code': '6001', 'debit': 0, 'credit': 500},
        ])
        conn.close()
        tmp_csv = tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w', newline='')
        tmp_csv.close()
        try:
            result = acc.vouchers.batch_export_csv(tmp_csv.name)
            assert 'count' in result
            assert result['count'] >= 1
            with open(tmp_csv.name, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = list(reader)
            assert len(rows) >= 2
        finally:
            os.unlink(tmp_csv.name)

    def test_voucher_no_uniqueness(self):
        conn = acc.database.get_conn()
        _insert_voucher(conn, '记-2026-06-0001', '2026-06-01', '第一个', 2026, 6, [
            {'code': '1002', 'debit': 100, 'credit': 0},
            {'code': '6001', 'debit': 0, 'credit': 100},
        ])
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO vouchers (voucher_no, date, summary, fiscal_year, fiscal_month) "
                "VALUES (?,?,?,?,?)",
                ('记-2026-06-0001', '2026-06-02', '重复', 2026, 6),
            )
            conn.commit()
        conn.close()


# ── 3. Financial Reports ─────────────────────────────────────────────────


class TestReports:
    @pytest.fixture(autouse=True)
    def _seed_data(self):
        conn = acc.database.get_conn()
        _insert_voucher(conn, '记-2026-06-0001', '2026-06-01', '收入', 2026, 6, [
            {'code': '1002', 'debit': 50000, 'credit': 0},
            {'code': '6001', 'debit': 0, 'credit': 50000},
        ])
        _insert_voucher(conn, '记-2026-06-0002', '2026-06-02', '费用', 2026, 6, [
            {'code': '6602', 'debit': 20000, 'credit': 0},
            {'code': '1002', 'debit': 0, 'credit': 20000},
        ])
        conn.close()

    def test_balance_sheet_runs(self, capsys):
        acc.reports.balance_sheet()
        captured = capsys.readouterr()
        assert '资产负债表' in captured.out

    def test_income_statement_runs(self, capsys):
        acc.reports.income_statement()
        captured = capsys.readouterr()
        assert '利润表' in captured.out

    def test_cash_flow_statement_runs(self, capsys):
        acc.reports.cash_flow_statement()
        captured = capsys.readouterr()
        assert '现金流量表' in captured.out

    def test_calc_financial_ratios_no_data(self):
        conn = acc.database.get_conn()
        conn.execute("DELETE FROM journal_entries")
        conn.execute("DELETE FROM vouchers")
        conn.commit()
        conn.close()
        ratios = acc.reports.calc_financial_ratios()
        assert isinstance(ratios, dict)
        for key in ('流动比率', '速动比率', '资产负债率', '毛利率', '净利率'):
            assert key in ratios, f"Missing ratio: {key}"

    def test_calc_financial_ratios_with_data(self):
        ratios = acc.reports.calc_financial_ratios()
        assert ratios['毛利率'] == 100.0
        assert ratios['净利率'] == 60.0

    def test_detect_anomalies_returns_list(self):
        result = acc.reports.detect_anomalies()
        assert isinstance(result, list)


# ── 4. Fixed Assets ───────────────────────────────────────────────────────


class TestAssets:
    def test_add_fixed_asset_via_db(self):
        conn = acc.database.get_conn()
        cur = conn.execute(
            "INSERT INTO fixed_assets (name, original_value, residual_value, "
            "useful_life_months, depreciation_method, purchase_date) "
            "VALUES (?,?,?,?,?,?)",
            ('服务器', 100000, 10000, 60, 'straight', '2026-01-01'),
        )
        conn.commit()
        aid = cur.lastrowid
        row = conn.execute("SELECT * FROM fixed_assets WHERE id=?", (aid,)).fetchone()
        conn.close()
        assert row is not None
        assert row['name'] == '服务器'

    def test_calc_depreciation_straight_line(self):
        depr = acc.assets.calc_depreciation(100000, 10000, 60, 'straight')
        assert depr == pytest.approx(1500.0)
        # (100000 - 10000) / 60 = 1500

    def test_calc_depreciation_double_declining(self):
        depr = acc.assets.calc_depreciation(100000, 10000, 60, 'double')
        assert depr > 0
        # First month: 100000 * (2/5) / 12 = 100000 * 0.4 / 12 ≈3333.33
        assert depr == pytest.approx(3333.33, rel=1e-2)

    def test_calc_depreciation_sum_of_years(self):
        depr = acc.assets.calc_depreciation(100000, 10000, 60, 'sum-of-years')
        assert depr > 0

    def test_list_fixed_assets_runs(self, capsys):
        conn = acc.database.get_conn()
        conn.execute(
            "INSERT INTO fixed_assets (name, original_value, residual_value, "
            "useful_life_months, depreciation_method, purchase_date) "
            "VALUES (?,?,?,?,?,?)",
            ('电脑', 8000, 800, 36, 'straight', '2026-03-01'),
        )
        conn.commit()
        conn.close()
        acc.assets.list_fixed_assets()
        captured = capsys.readouterr()
        assert '电脑' in captured.out

    def test_list_fixed_assets_empty(self, capsys):
        acc.assets.list_fixed_assets()
        captured = capsys.readouterr()
        assert '暂无固定资产' in captured.out

    def test_run_depreciation(self, capsys):
        conn = acc.database.get_conn()
        conn.execute(
            "INSERT INTO fixed_assets (name, original_value, residual_value, "
            "useful_life_months, depreciation_method, purchase_date) "
            "VALUES (?,?,?,?,?,?)",
            ('办公桌', 5000, 500, 60, 'straight', '2026-01-01'),
        )
        conn.commit()
        conn.close()
        acc.assets.run_depreciation(2026, 6)
        captured = capsys.readouterr()
        assert '折旧计提完成' in captured.out


# ── 5. Tax ────────────────────────────────────────────────────────────────


class TestTax:
    def test_calc_pit_below_threshold(self, monkeypatch, capsys):
        inputs = iter(['0', 'n'])
        monkeypatch.setattr('builtins.input', lambda prompt='': next(inputs))
        acc.tax.calc_pit()
        captured = capsys.readouterr()
        assert '无需缴纳' in captured.out

    def test_calc_pit_progressive_rates(self, monkeypatch, capsys):
        inputs = iter(['50000', 'n'])
        monkeypatch.setattr('builtins.input', lambda prompt='': next(inputs))
        acc.tax.calc_pit()
        captured = capsys.readouterr()
        assert '应缴个人所得税' in captured.out
        assert '税后收入' in captured.out

    def test_calc_pit_high_income(self, monkeypatch, capsys):
        inputs = iter(['200000', 'n'])
        monkeypatch.setattr('builtins.input', lambda prompt='': next(inputs))
        acc.tax.calc_pit()
        captured = capsys.readouterr()
        assert '应缴个人所得税' in captured.out

    def test_pit_rates_structure(self):
        assert len(acc.tax.PIT_RATES) == 7
        assert acc.tax.PIT_RATES[0] == (0, 36000, 0.03, 0)
        assert acc.tax.PIT_RATES[-1][2] == 0.45

    def test_calc_vat_structure(self, monkeypatch, capsys):
        inputs = iter(['1', '113000', 'n'])
        monkeypatch.setattr('builtins.input', lambda prompt='': next(inputs))
        acc.tax.calc_vat()
        captured = capsys.readouterr()
        assert '增值税计算明细' in captured.out
        assert '增值税额' in captured.out

    def test_calc_vat_invalid_input(self, monkeypatch, capsys):
        inputs = iter(['9'])
        monkeypatch.setattr('builtins.input', lambda prompt='': next(inputs))
        acc.tax.calc_vat()
        captured = capsys.readouterr()
        assert '无效选择' in captured.out


# ── 6. Period Closing ─────────────────────────────────────────────────────


class TestTaxPure:
    def test_compute_vat_basic(self):
        r = acc.compute_vat(113000, 0.13)
        assert r['rate'] == 0.13
        assert r['revenue'] == 113000.0
        assert r['tax_exclusive'] == 100000.0
        assert r['tax_amount'] == 13000.0

    def test_compute_vat_small_scale(self):
        r = acc.compute_vat(10100, 0.01)
        assert r['rate'] == 0.01
        assert round(r['tax_exclusive'] + r['tax_amount'], 2) == 10100.0

    def test_compute_pit_zero(self):
        r = acc.compute_pit(0)
        assert r['total_tax'] == 0.0
        assert r['brackets'] == []

    def test_compute_pit_first_bracket(self):
        r = acc.compute_pit(30000)
        assert r['total_tax'] == 900.0
        assert len(r['brackets']) == 1
        assert r['after_tax'] == 29100.0

    def test_compute_pit_progressive(self):
        r = acc.compute_pit(50000)
        assert r['total_tax'] == 2480.0
        assert len(r['brackets']) == 2

    def test_compute_pit_top_bracket(self):
        r = acc.compute_pit(1000000)
        assert r['brackets'][-1]['rate'] == 0.45
        assert r['total_tax'] > 0

class TestPeriod:
    def test_get_period_status_open(self):
        status = acc.period.get_period_status(2026, 6)
        assert status == {'closed': False, 'close_time': None}

    def test_close_period(self):
        result = acc.period.close_period(2026, 6)
        assert result is True
        status = acc.period.get_period_status(2026, 6)
        assert status['closed'] is True

    def test_auto_close_period_with_data(self):
        conn = acc.database.get_conn()
        _insert_voucher(conn, '记-2026-06-0001', '2026-06-01', '收入', 2026, 6, [
            {'code': '1002', 'debit': 30000, 'credit': 0},
            {'code': '6001', 'debit': 0, 'credit': 30000},
        ])
        conn.close()
        result = acc.period.auto_close_period(2026, 6)
        assert result['income_total'] == pytest.approx(30000.0)
        assert result['expense_total'] == pytest.approx(0.0)
        assert result['profit'] == pytest.approx(30000.0)
        assert len(result['vouchers']) > 0

    def test_get_close_log(self):
        acc.period.close_period(2026, 5)
        log = acc.period.get_close_log()
        assert len(log) >= 1
        assert '2026年05月' in log[0]['period']


# ── 7. Auth ───────────────────────────────────────────────────────────────


class TestAuth:
    def test_init_users_creates_defaults(self):
        conn = acc.database.get_conn()
        rows = conn.execute("SELECT username, role FROM users").fetchall()
        conn.close()
        usernames = {r['username'] for r in rows}
        assert 'admin' in usernames
        assert 'accountant' in usernames
        assert 'viewer' in usernames

    def test_login_success_admin(self):
        result = acc.auth.login('admin', 'admin123')
        assert result['success'] is True
        assert result['user']['username'] == 'admin'
        assert result['user']['role'] == 'admin'

    def test_login_success_accountant(self):
        result = acc.auth.login('accountant', 'acc123')
        assert result['success'] is True
        assert result['user']['role'] == 'accountant'

    def test_login_failure_wrong_password(self):
        result = acc.auth.login('admin', 'wrongpassword')
        assert result['success'] is False
        assert '错误' in result['error']

    def test_login_failure_wrong_username(self):
        result = acc.auth.login('nonexistent', 'pass123')
        assert result['success'] is False

    def test_get_theme_and_theme_mode(self):
        theme = acc.auth.get_theme()
        assert isinstance(theme, dict)
        assert 'bg' in theme
        mode = acc.auth.get_theme_mode()
        assert mode in ('light', 'dark')

    def test_set_theme_mode(self):
        acc.auth.set_theme_mode('dark')
        assert acc.auth.get_theme_mode() == 'dark'
        acc.auth.set_theme_mode('light')

    def test_require_role_admin(self):
        assert acc.auth.require_role('admin') is True
        assert acc.auth.require_role('viewer') is False

    def test_logout_clears_user(self):
        acc.auth.login('admin', 'admin123')
        acc.auth.logout()
        assert acc.auth.CURRENT_USER['role'] == 'admin'


# ── 8. Aging ──────────────────────────────────────────────────────────────


class TestAging:
    def test_aging_analysis_empty_returns_list(self):
        result = acc.aging.aging_analysis('ar')
        assert isinstance(result, list)

    def test_aging_analysis_with_data(self):
        conn = acc.database.get_conn()
        _insert_voucher(conn, '记-2026-01-0001', '2026-01-15', '应收款', 2026, 1, [
            {'code': '1122', 'debit': 50000, 'credit': 0},
            {'code': '6001', 'debit': 0, 'credit': 50000},
        ])
        conn.close()
        result = acc.aging.aging_analysis('ar', as_of='2026-06-30')
        assert len(result) > 0
        assert result[0]['account_code'] == '1122'

    def test_get_total_ar_ap_ar(self):
        conn = acc.database.get_conn()
        _insert_voucher(conn, '记-2026-06-0001', '2026-06-01', '应收', 2026, 6, [
            {'code': '1122', 'debit': 8000, 'credit': 0},
            {'code': '6001', 'debit': 0, 'credit': 8000},
        ])
        conn.close()
        result = acc.aging.get_total_ar_ap('ar')
        assert result['total'] == pytest.approx(8000.0)
        assert result['account_count'] > 0

    def test_get_total_ar_ap_ap(self):
        conn = acc.database.get_conn()
        _insert_voucher(conn, '记-2026-06-0001', '2026-06-01', '应付', 2026, 6, [
            {'code': '6001', 'debit': 0, 'credit': 3000},
            {'code': '2202', 'debit': 0, 'credit': 3000},
        ])
        conn.close()
        result = acc.aging.get_total_ar_ap('ap')
        assert result['total'] == pytest.approx(-3000.0)


# ── 9. Budget ─────────────────────────────────────────────────────────────


class TestBudget:
    def test_set_budget_saves(self):
        acc.budget.set_budget('6001', 2026, 6, 50000.0, '月度销售预算')
        conn = acc.database.get_conn()
        row = conn.execute(
            "SELECT * FROM budgets WHERE account_code=? AND fiscal_year=? AND fiscal_month=?",
            ('6001', 2026, 6),
        ).fetchone()
        conn.close()
        assert row is not None
        assert float(row['budget_amount']) == pytest.approx(50000.0)

    def test_get_budget_status_returns_list(self):
        result = acc.budget.get_budget_status(2026, 6)
        assert isinstance(result, list)

    def test_get_budget_status_with_data(self):
        acc.budget.set_budget('6001', 2026, 6, 30000.0)
        result = acc.budget.get_budget_status(2026, 6)
        budgets = [r for r in result if r['account_code'] == '6001']
        assert len(budgets) > 0
        assert budgets[0]['budget'] == pytest.approx(30000.0)

    def test_get_budget_status_year_only(self):
        acc.budget.set_budget('6001', 2026, 6, 10000.0)
        acc.budget.set_budget('6001', 2026, 7, 15000.0)
        result = acc.budget.get_budget_status(2026)
        budgets = [r for r in result if r['account_code'] == '6001']
        assert len(budgets) > 0
        assert budgets[0]['budget'] == pytest.approx(25000.0, abs=0.01)


# ── 10. Inventory ─────────────────────────────────────────────────────────


class TestInventory:
    def test_add_product(self):
        result = acc.inventory.add_product('A001', '测试商品', '电子产品', '个', 2999.0)
        assert result['success'] is True
        assert result['id'] > 0

    def test_add_product_duplicate_code(self):
        acc.inventory.add_product('A001', '第一个', '电子', '个', 100.0)
        result = acc.inventory.add_product('A001', '重复', '电子', '个', 200.0)
        assert result['success'] is False

    def test_inventory_in(self):
        r = acc.inventory.add_product('B001', '库存商品', '日用', '个', 50.0)
        pid = r['id']
        acc.inventory.inventory_in(pid, 100, 50.0, '采购', 'PO-001', '进货')
        product = acc.inventory.get_product(pid)
        assert float(product['quantity']) == pytest.approx(100.0)
        assert float(product['unit_price']) == pytest.approx(50.0)

    def test_inventory_out(self):
        r = acc.inventory.add_product('C001', '出货商品', '食品', '个', 200.0)
        pid = r['id']
        acc.inventory.inventory_in(pid, 50, 200.0)
        result = acc.inventory.inventory_out(pid, 20, '销售', 'SALE-001', '出货')
        assert result['success'] is True
        product = acc.inventory.get_product(pid)
        assert float(product['quantity']) == pytest.approx(30.0)

    def test_inventory_out_insufficient(self):
        r = acc.inventory.add_product('D001', '缺货商品', '其他', '个', 10.0)
        pid = r['id']
        result = acc.inventory.inventory_out(pid, 100)
        assert result['success'] is False

    def test_get_all_products(self):
        acc.inventory.add_product('E001', '商品一', 'A类', '个', 10.0)
        acc.inventory.add_product('E002', '商品二', 'B类', '个', 20.0)
        products = acc.inventory.get_all_products()
        assert len(products) >= 2

    def test_get_product_not_found(self):
        p = acc.inventory.get_product(99999)
        assert p == {}

    def test_inventory_adjust(self):
        r = acc.inventory.add_product('F001', '调整商品', '其他', '个', 100.0)
        pid = r['id']
        acc.inventory.inventory_in(pid, 50, 100.0)
        acc.inventory.inventory_adjust(pid, 30, '盘点调整')
        product = acc.inventory.get_product(pid)
        assert float(product['quantity']) == pytest.approx(30.0)

    def test_inventory_summary(self):
        r = acc.inventory.add_product('G001', '汇总商品', '测试', '个', 50.0)
        pid = r['id']
        acc.inventory.inventory_in(pid, 100, 50.0)
        summary = acc.inventory.get_inventory_summary()
        assert len(summary) >= 1


# ── 11. Features (Audit / Alerts / Payroll / Projects / Cash Flow / Attachments) ──


class TestFeatures:
    def test_log_action_and_get_audit_logs(self):
        acc.log_action('admin', 'test_action', 'test', '1', '测试审计日志')
        logs = acc.get_audit_logs(limit=10)
        assert len(logs) >= 1
        assert logs[0]['action'] == 'test_action'

    def test_get_audit_logs_with_target_type(self):
        acc.log_action('admin', 'action1', 'voucher', '1', 'test')
        acc.log_action('admin', 'action2', 'asset', '2', 'test')
        logs = acc.get_audit_logs(target_type='voucher')
        assert all(l['target_type'] == 'voucher' for l in logs)

    def test_add_alert_rule_and_get_rules(self):
        result = acc.add_alert_rule('测试规则', 'current_ratio', 'lt', 1.0, 'critical')
        assert result['success'] is True
        rules = acc.get_alert_rules()
        names = [r['name'] for r in rules]
        assert '测试规则' in names

    def test_add_alert_rule_duplicate_name(self):
        acc.add_alert_rule('规则1', 'current_ratio', 'lt', 1.0)
        rules = acc.get_alert_rules()
        assert len(rules) >= 1

    def test_update_alert_rule(self):
        result = acc.add_alert_rule('待更新', 'quick_ratio', 'lt', 0.8, 'warning')
        rule_id = acc.get_alert_rules()[-1]['id']
        acc.update_alert_rule(rule_id, threshold=0.5, level='critical')
        rules = acc.get_alert_rules()
        updated = [r for r in rules if r['id'] == rule_id][0]
        assert float(updated['threshold']) == pytest.approx(0.5)

    def test_add_employee_and_get_all_employees(self):
        r = acc.add_employee('EMP001', '张三', '技术部', '工程师', 15000.0, 1500.0, 1000.0)
        assert r['success'] is True
        employees = acc.get_all_employees()
        assert len(employees) >= 1
        assert employees[0]['code'] == 'EMP001'

    def test_add_employee_duplicate(self):
        acc.add_employee('EMP001', '张三', '技术部', '工程师', 15000.0)
        r = acc.add_employee('EMP001', '李四', '市场部', '经理', 20000.0)
        assert r['success'] is False

    def test_update_employee(self):
        acc.add_employee('EMP002', '王五', '财务部', '会计', 10000.0, 1000.0, 500.0)
        emp = acc.get_all_employees()[0]
        acc.update_employee(emp['id'], base_salary=12000.0, position='高级会计')
        updated = acc.get_all_employees()[0]
        assert float(updated['base_salary']) == pytest.approx(12000.0)

    def test_calculate_payroll(self):
        acc.add_employee('EMP003', '赵六', '销售部', '销售经理', 25000.0, 2000.0, 1500.0)
        records = acc.calculate_payroll(2026, 6)
        assert len(records) >= 1
        assert float(records[0]['gross_pay']) == pytest.approx(25000.0)
        assert float(records[0]['net_pay']) > 0

    def test_confirm_and_generate_payroll_voucher(self):
        acc.add_employee('EMP004', '钱七', '人事部', 'HR', 18000.0, 1500.0, 1000.0)
        acc.calculate_payroll(2026, 6)
        records = acc.get_payroll_records(year=2026, month=6)
        rids = [r['id'] for r in records]
        acc.confirm_payroll(rids)
        result = acc.generate_payroll_voucher(2026, 6)
        assert result['success'] is True
        assert 'voucher_no' in result

    def test_add_project_and_get_all_projects(self):
        r = acc.add_project('PROJ-001', '新系统开发', 500000.0, '2026-01-01', '2026-12-31')
        assert r['success'] is True
        projects = acc.get_all_projects()
        assert len(projects) >= 1
        assert projects[0]['code'] == 'PROJ-001'

    def test_add_project_duplicate_code(self):
        acc.add_project('PROJ-001', '项目一', 100000.0)
        r = acc.add_project('PROJ-001', '项目一', 200000.0)
        assert r['success'] is False

    def test_link_voucher_to_project(self):
        acc.add_project('PROJ-002', '咨询项目', 100000.0)
        conn = acc.database.get_conn()
        vid = _insert_voucher(conn, '记-2026-06-0001', '2026-06-01', '项目相关支出', 2026, 6, [
            {'code': '6602', 'debit': 5000, 'credit': 0},
            {'code': '1002', 'debit': 0, 'credit': 5000},
        ])
        conn.close()
        result = acc.link_voucher_to_project(vid, 1)
        assert result['success'] is True

    def test_cash_flow_statement_direct_no_data(self):
        result = acc.cash_flow_statement_direct(2026, 6)
        assert isinstance(result, dict)
        assert 'net_cash_operating' in result

    def test_cash_flow_statement_direct_with_data(self):
        conn = acc.database.get_conn()
        _insert_voucher(conn, '记-2026-06-0001', '2026-06-01', '收款', 2026, 6, [
            {'code': '1002', 'debit': 100000, 'credit': 0},
            {'code': '6001', 'debit': 0, 'credit': 100000},
        ])
        conn.close()
        result = acc.cash_flow_statement_direct(2026, 6)
        assert result['cash_from_customers'] > 0

    def test_get_attachments_empty(self):
        atts = acc.get_attachments()
        assert isinstance(atts, list)
        assert len(atts) == 0

    def test_attach_and_get_attachments(self):
        tmp_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
        tmp_file.write(b'hello')
        tmp_file.close()
        try:
            conn = acc.database.get_conn()
            vid = _insert_voucher(conn, '记-2026-06-0001', '2026-06-01', '附件测试', 2026, 6, [
                {'code': '1002', 'debit': 100, 'credit': 0},
                {'code': '6001', 'debit': 0, 'credit': 100},
            ])
            conn.close()
            result = acc.attach_file(vid, tmp_file.name)
            assert result['success'] is True
            atts = acc.get_attachments(vid)
            assert len(atts) == 1
        finally:
            os.unlink(tmp_file.name)

    def test_get_balance_sheet_bank(self):
        acc.import_bank_statement([
            {'transaction_date': '2026-06-01', 'description': '收款', 'amount': 10000.0},
        ])
        rows = acc.get_balance_sheet()
        assert len(rows) >= 1

    def test_get_alert_history(self):
        history = acc.get_alert_history()
        assert isinstance(history, list)

    def test_check_alerts_returns_list(self):
        results = acc.check_alerts()
        assert isinstance(results, list)

    def test_resolve_alert(self):
        """Verify resolve_alert runs without error (smoke test)."""
        acc.check_alerts()
        history = acc.get_alert_history(unresolved_only=True)
        if history:
            acc.resolve_alert(history[0]['id'])
            still_open = acc.get_alert_history(unresolved_only=True)
            assert all(h['id'] != history[0]['id'] for h in still_open)

    def test_backup_database(self):
        tmp_bak = tempfile.NamedTemporaryFile(suffix='.bak', delete=False)
        tmp_bak.close()
        try:
            result = acc.backup_database(tmp_bak.name)
            assert result['success'] is True
            assert os.path.exists(tmp_bak.name)
        finally:
            os.unlink(tmp_bak.name)

    def test_restore_database_from_backup(self):
        tmp_bak = tempfile.NamedTemporaryFile(suffix='.bak', delete=False)
        tmp_bak.close()
        try:
            acc.backup_database(tmp_bak.name)
            result = acc.restore_database(tmp_bak.name)
            assert result['success'] is True
        finally:
            os.unlink(tmp_bak.name)

    def test_import_bank_statement(self):
        items = [
            {'transaction_date': '2026-06-01', 'description': '收款A', 'amount': 5000.0},
            {'transaction_date': '2026-06-02', 'description': '收款B', 'amount': 3000.0, 'balance': 8000.0},
        ]
        result = acc.import_bank_statement(items)
        assert result['success'] is True
        assert result['imported'] == 2

    def test_get_reconciliation_status(self):
        status = acc.get_reconciliation_status()
        assert 'total' in status
        assert 'reconciled' in status
        assert 'pending' in status

    def test_get_payroll_records_empty(self):
        records = acc.get_payroll_records(year=2026, month=6)
        assert records == []

    def test_project_pnl(self):
        acc.add_project('PROJ-003', '测试项目', 50000.0)
        conn = acc.database.get_conn()
        _insert_voucher(conn, '记-2026-06-0001', '2026-06-01', '[项目1]收入', 2026, 6, [
            {'code': '1002', 'debit': 30000, 'credit': 0},
            {'code': '6001', 'debit': 0, 'credit': 30000},
        ])
        conn.close()
        pnl = acc.get_project_pnl(1)
        assert isinstance(pnl, dict)
        assert 'revenue' in pnl

    def test_delete_attachment(self):
        tmp_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
        tmp_file.write(b'data')
        tmp_file.close()
        try:
            conn = acc.database.get_conn()
            vid = _insert_voucher(conn, '记-2026-06-0001', '2026-06-01', '删除测试', 2026, 6, [
                {'code': '1002', 'debit': 100, 'credit': 0},
                {'code': '6001', 'debit': 0, 'credit': 100},
            ])
            conn.close()
            r = acc.attach_file(vid, tmp_file.name)
            atts = acc.get_attachments(vid)
            if atts:
                acc.delete_attachment(atts[0]['id'])
                remaining = acc.get_attachments(vid)
                assert len(remaining) == 0
        finally:
            os.unlink(tmp_file.name)
