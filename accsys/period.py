"""会计期间结转模块"""
from __future__ import annotations
from decimal import Decimal
from datetime import datetime, date, timedelta
from .database import get_conn
from .accounts import load_accounts_from_db, calc_balances
from .vouchers import next_voucher_no

PERIOD_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS period_close (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    closed_at TEXT,
    status TEXT DEFAULT 'open',
    action TEXT,
    note TEXT,
    UNIQUE(year, month)
)
'''


def auto_close_period(year: int, month: int) -> dict:
    today = date(year, month, 1)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    period_end = (next_month - timedelta(days=1)).isoformat()

    accounts = load_accounts_from_db()
    balances = calc_balances(accounts, as_of=period_end)

    income_accs = [a for a in accounts if a['category'] == 'income']
    expense_accs = [a for a in accounts if a['category'] == 'expense']

    income_code = '6001'
    expense_code = '6602'
    for a in income_accs:
        if '主营' in a['name']:
            income_code = a['code']
            break
    for a in expense_accs:
        if a['code'] == '6602':
            expense_code = a['code']
            break

    profit_account = '4103'

    conn = get_conn()
    results = {"income_total": 0, "expense_total": 0, "profit": 0, "vouchers": []}

    try:
        total_income = Decimal('0')
        income_entries = []
        for a in income_accs:
            bal = balances.get(a['code'], Decimal('0'))
            if bal > 0:
                total_income += bal
                income_entries.append((a['code'], float(bal)))

        if total_income > 0:
            v_no = next_voucher_no(year, month)
            cur = conn.execute(
                "INSERT INTO vouchers (voucher_no, date, summary, fiscal_year, fiscal_month) VALUES (?,?,?,?,?)",
                (v_no, period_end, f"结转{month}月收入", year, month))
            vid = cur.lastrowid

            for code, bal in income_entries:
                conn.execute(
                    "INSERT INTO journal_entries (voucher_id, account_code, debit, credit) VALUES (?,?,?,?)",
                    (vid, code, bal, 0))
            conn.execute(
                "INSERT INTO journal_entries (voucher_id, account_code, debit, credit) VALUES (?,?,?,?)",
                (vid, profit_account, 0, float(total_income)))
            results["vouchers"].append(v_no)

        total_expense = Decimal('0')
        expense_entries = []
        for a in expense_accs:
            bal = balances.get(a['code'], Decimal('0'))
            if bal > 0:
                total_expense += bal
                expense_entries.append((a['code'], float(bal)))

        if total_expense > 0:
            v_no2 = next_voucher_no(year, month)
            cur = conn.execute(
                "INSERT INTO vouchers (voucher_no, date, summary, fiscal_year, fiscal_month) VALUES (?,?,?,?,?)",
                (v_no2, period_end, f"结转{month}月成本费用", year, month))
            vid2 = cur.lastrowid

            conn.execute(
                "INSERT INTO journal_entries (voucher_id, account_code, debit, credit) VALUES (?,?,?,?)",
                (vid2, profit_account, float(total_expense), 0))
            for code, bal in expense_entries:
                conn.execute(
                    "INSERT INTO journal_entries (voucher_id, account_code, debit, credit) VALUES (?,?,?,?)",
                    (vid2, code, 0, bal))
            results["vouchers"].append(v_no2)

        conn.commit()
        results["income_total"] = float(total_income)
        results["expense_total"] = float(total_expense)
        results["profit"] = float(total_income - total_expense)
        print(f"\n[OK] {year}年{month}月期末结转完成")
        print(f"  收入: {results['income_total']:.2f}")
        print(f"  费用: {results['expense_total']:.2f}")
        print(f"  利润: {results['profit']:.2f}")
        if results['vouchers']:
            print(f"  生成凭证: {', '.join(results['vouchers'])}")
    except Exception as e:
        conn.rollback()
        print(f"[ERR] 结转失败: {e}")
    finally:
        conn.close()

    return results


def ensure_period_table():
    conn = get_conn()
    conn.execute(PERIOD_TABLE_SQL)
    conn.commit()
    conn.close()


def get_period_status(year: int, month: int) -> dict:
    ensure_period_table()
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM period_close WHERE year=? AND month=? AND status='closed'",
        (year, month)).fetchone()
    conn.close()
    if row:
        return {"closed": True, "close_time": row['closed_at']}
    return {"closed": False, "close_time": None}


def close_period(year: int, month: int) -> bool:
    ensure_period_table()
    conn = get_conn()
    try:
        now = datetime.now().isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO period_close (year, month, closed_at, status, action) VALUES (?,?,?,?,?)",
            (year, month, now, 'closed', 'manual_close'))
        conn.commit()
        return True
    except Exception as e:
        print(f"[ERR] close_period: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_close_log(limit: int = 20) -> list:
    ensure_period_table()
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM period_close ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            "time": r['closed_at'] or '',
            "period": f"{r['year']}年{r['month']:02d}月",
            "action": r['action'] if r['action'] else '',
            "status": r['status'] if r['status'] else '',
        })
    return result
