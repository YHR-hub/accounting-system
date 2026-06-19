from __future__ import annotations

"""银企对账模块。"""

from .database import get_conn


def import_bank_statement(items: list) -> dict:
    conn = get_conn()
    count = 0
    for it in items:
        try:
            conn.execute("INSERT INTO bank_statements (transaction_date, description, amount, balance, ref_no) VALUES (?,?,?,?,?)",
                        (it["transaction_date"], it["description"], it["amount"], it.get("balance",0), it.get("ref_no","")))
            count += 1
        except Exception:
            pass
    conn.commit()
    conn.close()
    return {"success": True, "imported": count}


def auto_reconcile(tolerance: float = 0.01) -> dict:
    conn = get_conn()
    matched = 0
    statements = conn.execute("SELECT * FROM bank_statements WHERE is_reconciled=0 ORDER BY transaction_date").fetchall()
    for stmt in statements:
        matches = conn.execute("""
            SELECT v.id, v.date, v.summary, COALESCE(SUM(je.debit-je.credit),0) as net
            FROM vouchers v
            JOIN journal_entries je ON je.voucher_id=v.id
            JOIN accounts a ON je.account_code=a.code
            WHERE a.code='1002' AND ABS(COALESCE(SUM(je.debit-je.credit),0) - ?) < ?
            AND v.date BETWEEN date(?, '-3 days') AND date(?, '+3 days')
            GROUP BY v.id
            ORDER BY ABS(COALESCE(SUM(je.debit-je.credit),0) - ?)
            LIMIT 1
        """, (stmt["amount"], tolerance, stmt["transaction_date"], stmt["transaction_date"], stmt["amount"])).fetchone()
        if matches:
            conn.execute("INSERT INTO reconciliation (statement_id, voucher_id, match_type) VALUES (?,?,?)",
                        (stmt["id"], matches["id"], "auto"))
            conn.execute("UPDATE bank_statements SET is_reconciled=1 WHERE id=?", (stmt["id"],))
            matched += 1
    conn.commit()
    conn.close()
    return {"success": True, "matched": matched, "total": len(statements)}


def get_reconciliation_status() -> dict:
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM bank_statements").fetchone()[0]
    reconciled = conn.execute("SELECT COUNT(*) FROM bank_statements WHERE is_reconciled=1").fetchone()[0]
    unmatched = conn.execute("SELECT COUNT(*) FROM reconciliation WHERE match_type='unmatched'").fetchone()[0]
    conn.close()
    return {"total": total, "reconciled": reconciled, "unmatched": unmatched, "pending": total - reconciled}


def get_balance_sheet() -> list:
    conn = get_conn()
    rows = conn.execute("""
        SELECT s.*, r.voucher_id, r.match_type, v.voucher_no
        FROM bank_statements s
        LEFT JOIN reconciliation r ON s.id=r.statement_id
        LEFT JOIN vouchers v ON r.voucher_id=v.id
        ORDER BY s.transaction_date DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
