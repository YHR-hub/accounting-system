from __future__ import annotations

"""应收应付账龄管理模块。"""

from datetime import date

from .database import get_conn
from .constants import AR_ACCOUNTS, AP_ACCOUNTS, BAD_DEBT_RATES


def aging_analysis(account_type: str = "ar", as_of: str = None) -> list:
    if as_of is None:
        as_of = date.today().isoformat()
    accounts = AR_ACCOUNTS if account_type == "ar" else AP_ACCOUNTS
    conn = get_conn()
    results = []
    for acode, aname in accounts.items():
        rows = conn.execute("""
            SELECT je.id, v.date, v.summary, je.debit, je.credit,
                   v.voucher_no, v.fiscal_year, v.fiscal_month
            FROM journal_entries je
            JOIN vouchers v ON je.voucher_id=v.id
            WHERE je.account_code=? AND v.date<=?
            ORDER BY v.date
        """, (acode, as_of)).fetchall()
        balance = 0.0
        for r in rows:
            balance += float(r["debit"]) - float(r["credit"])
        if abs(balance) < 0.01:
            continue
        days = (date.fromisoformat(as_of) - date.fromisoformat(rows[-1]["date"])).days if rows else 0
        bucket = "0-30天" if days <= 30 else ("31-60天" if days <= 60 else ("61-90天" if days <= 90 else ("91-180天" if days <= 180 else ("181-365天" if days <= 365 else "365天+"))))
        rate = next(r for d, r in BAD_DEBT_RATES if days <= d)
        provision = abs(balance) * rate
        results.append({
            "account_code": acode, "account_name": aname,
            "balance": balance, "last_date": rows[-1]["date"] if rows else "",
            "days": days, "bucket": bucket, "provision_rate": rate,
            "bad_debt_provision": round(provision, 2),
        })
    conn.close()
    return sorted(results, key=lambda x: abs(x["balance"]), reverse=True)


def get_total_ar_ap(account_type: str = "ar") -> dict:
    accounts = AR_ACCOUNTS if account_type == "ar" else AP_ACCOUNTS
    codes = ",".join(f"'{c}'" for c in accounts)
    conn = get_conn()
    total = conn.execute(f"""
        SELECT COALESCE(SUM(je.debit-je.credit),0) as balance
        FROM journal_entries je
        JOIN accounts a ON je.account_code=a.code
        WHERE je.account_code IN ({codes})
    """).fetchone()[0]
    conn.close()
    return {"total": float(total), "account_count": len(accounts)}
