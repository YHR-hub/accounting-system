from __future__ import annotations

"""现金流量表模块。"""

from .database import get_conn


def cash_flow_statement_direct(year: int, month: int = 0) -> dict:
    conn = get_conn()
    conditions = "v.fiscal_year=?"
    params = [year]
    if month:
        conditions += " AND v.fiscal_month<=?"
        params.append(month)
    cash_from_customers = conn.execute(f"""
        SELECT COALESCE(SUM(je.debit),0) - COALESCE(SUM(je.credit),0)
        FROM journal_entries je
        JOIN vouchers v ON je.voucher_id=v.id
        WHERE je.account_code='1002' AND {conditions}
    """, params).fetchone()[0]
    cash_to_suppliers = conn.execute(f"""
        SELECT COALESCE(SUM(je.credit),0) - COALESCE(SUM(je.debit),0)
        FROM journal_entries je
        JOIN vouchers v ON je.voucher_id=v.id
        WHERE je.account_code='1002' AND {conditions}
    """, params).fetchone()[0]
    cash_for_salaries = conn.execute(f"""
        SELECT COALESCE(SUM(je.debit),0)
        FROM journal_entries je
        JOIN vouchers v ON je.voucher_id=v.id
        WHERE je.account_code='2211' AND {conditions}
    """, params).fetchone()[0]
    cash_for_taxes = conn.execute(f"""
        SELECT COALESCE(SUM(je.debit),0)
        FROM journal_entries je
        JOIN vouchers v ON je.voucher_id=v.id
        WHERE je.account_code='2221' AND {conditions}
    """, params).fetchone()[0]
    conn.close()
    cfo = float(cash_from_customers) - float(cash_to_suppliers) - float(cash_for_salaries) - float(cash_for_taxes)
    return {
        "cash_from_customers": float(cash_from_customers),
        "cash_to_suppliers": float(cash_to_suppliers),
        "cash_for_salaries": float(cash_for_salaries),
        "cash_for_taxes": float(cash_for_taxes),
        "net_cash_operating": cfo,
        "year": year,
        "month": month if month else 12,
    }
