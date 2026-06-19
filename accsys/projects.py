from __future__ import annotations

"""项目会计模块。"""

from datetime import date

from .database import get_conn


def add_project(code: str, name: str, budget: float = 0, start_date: str = "", end_date: str = "") -> dict:
    conn = get_conn()
    try:
        conn.execute("INSERT INTO projects (code, name, budget, start_date, end_date) VALUES (?,?,?,?,?)",
                    (code, name, budget, start_date or date.today().isoformat(), end_date or ""))
        conn.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def get_all_projects() -> list:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM projects ORDER BY status, code").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_project_pnl(project_id: int) -> dict:
    conn = get_conn()
    income = conn.execute("""
        SELECT COALESCE(SUM(je.credit),0) as amount
        FROM journal_entries je
        JOIN vouchers v ON je.voucher_id=v.id
        WHERE je.voucher_id IN (
            SELECT id FROM vouchers WHERE summary LIKE ? OR summary LIKE ?
        )
    """, (f'%[项目{project_id}]%', f'%PROJ-{project_id}%')).fetchone()[0]
    expense = conn.execute("""
        SELECT COALESCE(SUM(je.debit),0) as amount
        FROM journal_entries je
        JOIN vouchers v ON je.voucher_id=v.id
        WHERE je.voucher_id IN (
            SELECT id FROM vouchers WHERE summary LIKE ? OR summary LIKE ?
        )
    """, (f'%[项目{project_id}]%', f'%PROJ-{project_id}%')).fetchone()[0]
    conn.close()
    return {
        "revenue": float(income),
        "cost": float(expense),
        "profit": float(income) - float(expense),
    }


def link_voucher_to_project(voucher_id: int, project_id: int) -> dict:
    conn = get_conn()
    try:
        conn.execute("UPDATE vouchers SET summary=summary||' [项目'||?||']' WHERE id=?",
                    (str(project_id), voucher_id))
        conn.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()
