from __future__ import annotations

"""预算管理模块。"""

from .database import get_conn


def init_budget_tables():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_code TEXT NOT NULL,
            fiscal_year INTEGER NOT NULL,
            fiscal_month INTEGER NOT NULL,
            budget_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
            note TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(account_code, fiscal_year, fiscal_month),
            FOREIGN KEY (account_code) REFERENCES accounts(code)
        )
    """)
    conn.commit()
    conn.close()


def set_budget(account_code: str, year: int, month: int, amount: float, note: str = ""):
    conn = get_conn()
    conn.execute("""
        INSERT OR REPLACE INTO budgets (account_code, fiscal_year, fiscal_month, budget_amount, note)
        VALUES (?,?,?,?,?)
    """, (account_code, year, month, amount, note))
    conn.commit()
    conn.close()


def get_budget_status(year: int, month: int = 0) -> list:
    conn = get_conn()
    if month == 0:
        rows = conn.execute("""
            SELECT b.account_code, a.name as account_name, a.category,
                   SUM(b.budget_amount) as budget_total,
                   COALESCE(SUM(CASE WHEN v.fiscal_year=? THEN je.debit ELSE 0 END),0) as actual_debit,
                   COALESCE(SUM(CASE WHEN v.fiscal_year=? THEN je.credit ELSE 0 END),0) as actual_credit
            FROM budgets b
            JOIN accounts a ON b.account_code=a.code
            LEFT JOIN journal_entries je ON je.account_code=b.account_code
            LEFT JOIN vouchers v ON je.voucher_id=v.id AND v.fiscal_year=b.fiscal_year
            WHERE b.fiscal_year=?
            GROUP BY b.account_code
            ORDER BY a.category, a.code
        """, (year, year, year)).fetchall()
    else:
        rows = conn.execute("""
            SELECT b.account_code, a.name as account_name, a.category,
                   b.budget_amount as budget_total,
                   COALESCE(SUM(CASE WHEN v.fiscal_year=? AND v.fiscal_month=? THEN je.debit ELSE 0 END),0) as actual_debit,
                   COALESCE(SUM(CASE WHEN v.fiscal_year=? AND v.fiscal_month=? THEN je.credit ELSE 0 END),0) as actual_credit
            FROM budgets b
            JOIN accounts a ON b.account_code=a.code
            LEFT JOIN journal_entries je ON je.account_code=b.account_code
            LEFT JOIN vouchers v ON je.voucher_id=v.id AND v.fiscal_year=b.fiscal_year AND v.fiscal_month=b.fiscal_month
            WHERE b.fiscal_year=? AND b.fiscal_month=?
            GROUP BY b.account_code
        """, (year, month, year, month, year, month)).fetchall()
    results = []
    for r in rows:
        budget = float(r["budget_total"])
        if r["category"] in ("income", "liability", "equity"):
            actual = float(r["actual_credit"])
        else:
            actual = float(r["actual_debit"])
        variance = budget - actual if budget else 0
        pct = (actual / budget * 100) if budget else 0
        results.append({
            "account_code": r["account_code"], "account_name": r["account_name"],
            "category": r["category"], "budget": budget, "actual": actual,
            "variance": round(variance, 2), "pct": round(pct, 1),
        })
    conn.close()
    return results
