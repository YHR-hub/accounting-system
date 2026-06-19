from __future__ import annotations

"""薪资管理模块。"""

from .audit import log_action
from .auth import CURRENT_USER
from .constants import PIT_RATES
from .database import get_conn
from .vouchers import next_voucher_no


def add_employee(code: str, name: str, department: str = "", position: str = "",
                 base_salary: float = 0, insurance: float = 0, housing_fund: float = 0) -> dict:
    conn = get_conn()
    try:
        conn.execute("INSERT INTO employees (code, name, department, position, base_salary, insurance, housing_fund) VALUES (?,?,?,?,?,?,?)",
                    (code, name, department, position, base_salary, insurance, housing_fund))
        conn.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def update_employee(eid: int, **kwargs):
    conn = get_conn()
    fields = {k: v for k, v in kwargs.items() if k in ("name","department","position","base_salary","insurance","housing_fund","tax_threshold","is_active")}
    if not fields:
        conn.close()
        return
    sets = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [eid]
    conn.execute(f"UPDATE employees SET {sets} WHERE id=?", vals)
    conn.commit()
    conn.close()


def get_all_employees(include_inactive: bool = False) -> list:
    conn = get_conn()
    q = "SELECT * FROM employees" if include_inactive else "SELECT * FROM employees WHERE is_active=1"
    rows = conn.execute(q).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def calculate_payroll(year: int, month: int) -> list:
    conn = get_conn()
    results = []
    employees = conn.execute("SELECT * FROM employees WHERE is_active=1").fetchall()
    for emp in employees:
        existing = conn.execute("SELECT * FROM payroll_records WHERE employee_id=? AND year=? AND month=?",
                               (emp["id"], year, month)).fetchone()
        if existing:
            results.append(dict(existing))
            continue
        insurance = float(emp["insurance"])
        housing_fund = float(emp["housing_fund"])
        threshold = float(emp["tax_threshold"])
        gross = float(emp["base_salary"])
        deductions = insurance + housing_fund
        taxable = max(0, gross - deductions - threshold)
        tax = 0
        remain = taxable
        for lo, hi, rate, quick in PIT_RATES:
            if remain <= 0:
                break
            bracket = min(remain, hi - lo)
            tax += bracket * rate
            remain -= bracket
        annual_taxable = taxable * 12
        annual_tax = 0
        remain_annual = annual_taxable
        for lo, hi, rate, quick in PIT_RATES:
            if remain_annual <= 0:
                break
            bracket = min(remain_annual, hi - lo)
            annual_tax += bracket * rate
            remain_annual -= bracket
        monthly_tax = round(annual_tax / 12, 2)
        net = round(gross - deductions - monthly_tax, 2)
        conn.execute("""
            INSERT INTO payroll_records (employee_id, year, month, gross_pay, insurance, housing_fund,
                                         taxable_income, income_tax, deductions, net_pay)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (emp["id"], year, month, gross, insurance, housing_fund, round(taxable,2), monthly_tax, round(deductions,2), net))
        row = conn.execute("SELECT * FROM payroll_records WHERE employee_id=? AND year=? AND month=?",
                          (emp["id"], year, month)).fetchone()
        results.append(dict(row))
    conn.commit()
    conn.close()
    return results


def confirm_payroll(record_ids: list) -> dict:
    conn = get_conn()
    for rid in record_ids:
        conn.execute("UPDATE payroll_records SET status='confirmed' WHERE id=?", (rid,))
    conn.commit()
    conn.close()
    return {"success": True}


def generate_payroll_voucher(year: int, month: int) -> dict:
    conn = get_conn()
    records = conn.execute("SELECT * FROM payroll_records WHERE year=? AND month=? AND status='confirmed' AND voucher_id IS NULL",
                          (year, month)).fetchall()
    if not records:
        conn.close()
        return {"success": False, "error": "没有待生成凭证的薪资记录"}
    total_gross = sum(float(r["gross_pay"]) for r in records)
    total_deduct = sum(float(r["deductions"]) + float(r["income_tax"]) for r in records)
    total_net = sum(float(r["net_pay"]) for r in records)
    vno = next_voucher_no(year, month)
    conn.execute("INSERT INTO vouchers (voucher_no, date, summary, fiscal_year, fiscal_month) VALUES (?,?,?,?,?)",
                (vno, f"{year}-{month:02d}-28", f"{year}年{month}月工资发放", year, month))
    vid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("INSERT INTO journal_entries (voucher_id, account_code, debit, credit) VALUES (?,?,?,?)",
                (vid, "2211", total_gross, 0))
    conn.execute("INSERT INTO journal_entries (voucher_id, account_code, debit, credit) VALUES (?,?,?,?)",
                (vid, "1002", 0, total_net))
    if total_deduct > 0:
        conn.execute("INSERT INTO journal_entries (voucher_id, account_code, debit, credit) VALUES (?,?,?,?)",
                    (vid, "2221", 0, sum(float(r["income_tax"]) for r in records)))
        conn.execute("INSERT INTO journal_entries (voucher_id, account_code, debit, credit) VALUES (?,?,?,?)",
                    (vid, "2241", 0, sum(float(r["deductions"]) for r in records)))
    for r in records:
        conn.execute("UPDATE payroll_records SET voucher_id=?, status='paid' WHERE id=?", (vid, r["id"]))
    conn.commit()
    conn.close()
    log_action(CURRENT_USER.get("username","system"), "create", "payroll_voucher", str(vid), f"{year}年{month}月工资凭证")
    return {"success": True, "voucher_id": vid, "voucher_no": vno}


def get_payroll_records(year: int = 0, month: int = 0, employee_id: int = 0) -> list:
    conn = get_conn()
    conditions = []
    params = []
    if year:
        conditions.append("p.year=?")
        params.append(year)
    if month:
        conditions.append("p.month=?")
        params.append(month)
    if employee_id:
        conditions.append("p.employee_id=?")
        params.append(employee_id)
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    rows = conn.execute(f"""
        SELECT p.*, e.code as emp_code, e.name as emp_name, e.department
        FROM payroll_records p
        JOIN employees e ON p.employee_id=e.id
        {where}
        ORDER BY p.year DESC, p.month DESC, e.code
    """, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]
