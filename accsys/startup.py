from __future__ import annotations

"""创业工具模块（报税/记账/考证）。"""

from datetime import datetime, date, timedelta

from .database import get_conn
from .constants import STUDENT_TAX_DEDUCTIONS, STUDENT_TAX_TIPS, CERT_EXAMS


MICRO_LEDGER_SQL = '''
CREATE TABLE IF NOT EXISTS micro_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('income','expense')),
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    note TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now','localtime'))
)
'''

MICRO_CATEGORIES = {
    "income": ["销售收入", "服务收入", "投资收益", "其他收入"],
    "expense": ["采购成本", "房租水电", "员工工资", "交通差旅", "餐饮招待",
                 "办公用品", "市场推广", "设备维护", "税费", "其他支出"],
}


def init_micro_ledger():
    conn = get_conn()
    conn.execute(MICRO_LEDGER_SQL)
    conn.commit()
    conn.close()


def add_micro_entry(date_str: str, entry_type: str, category: str, amount: float, note: str = "") -> bool:
    init_micro_ledger()
    conn = get_conn()
    try:
        conn.execute("INSERT INTO micro_ledger (date, type, category, amount, note) VALUES (?,?,?,?,?)",
                     (date_str, entry_type, category, amount, note))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"[ERR] add_micro_entry: {e}")
        return False
    finally:
        conn.close()


def delete_micro_entry(eid: int) -> bool:
    conn = get_conn()
    try:
        conn.execute("DELETE FROM micro_ledger WHERE id=?", (eid,))
        conn.commit()
        return True
    except:
        conn.rollback()
        return False
    finally:
        conn.close()


def get_micro_entries(year: int = 0, month: int = 0) -> list:
    init_micro_ledger()
    conn = get_conn()
    if year and month:
        prefix = f"{year:04d}-{month:02d}"
        rows = conn.execute(
            "SELECT * FROM micro_ledger WHERE date LIKE ? ORDER BY date DESC, id DESC",
            (f"{prefix}%",)).fetchall()
    elif year:
        prefix = f"{year:04d}"
        rows = conn.execute(
            "SELECT * FROM micro_ledger WHERE date LIKE ? ORDER BY date DESC, id DESC",
            (f"{prefix}%",)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM micro_ledger ORDER BY date DESC, id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def calc_micro_summary(year: int, month: int = 0) -> dict:
    entries = get_micro_entries(year, month)
    total_income = sum(e['amount'] for e in entries if e['type'] == 'income')
    total_expense = sum(e['amount'] for e in entries if e['type'] == 'expense')
    income_cats = {}
    expense_cats = {}
    for e in entries:
        target = income_cats if e['type'] == 'income' else expense_cats
        cat = e['category']
        target[cat] = target.get(cat, 0) + e['amount']
    return {
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "profit": round(total_income - total_expense, 2),
        "income_categories": income_cats,
        "expense_categories": expense_cats,
        "count": len(entries),
    }


def calc_student_tax(annual_income: float) -> dict:
    if annual_income <= 0:
        return {"total_income": 0, "taxable_income": 0, "tax": 0, "effective_rate": 0,
                "refund": 0, "refund_eligible": True, "message": "无收入无需申报"}
    standard_deduction = 60000
    taxable = max(0, annual_income - standard_deduction)
    if taxable <= 36000:
        tax = taxable * 0.03
    elif taxable <= 144000:
        tax = 36000 * 0.03 + (taxable - 36000) * 0.10
    elif taxable <= 300000:
        tax = 36000 * 0.03 + 108000 * 0.10 + (taxable - 144000) * 0.20
    elif taxable <= 420000:
        tax = 36000 * 0.03 + 108000 * 0.10 + 156000 * 0.20 + (taxable - 300000) * 0.25
    elif taxable <= 660000:
        tax = 36000 * 0.03 + 108000 * 0.10 + 156000 * 0.20 + 120000 * 0.25 + (taxable - 420000) * 0.30
    else:
        tax = 36000 * 0.03 + 108000 * 0.10 + 156000 * 0.20 + 120000 * 0.25 + 240000 * 0.30 + (taxable - 660000) * 0.35
    estimated_withheld = annual_income * 0.20 * 0.80
    refund = max(0, estimated_withheld - tax)
    return {
        "total_income": annual_income,
        "standard_deduction": standard_deduction,
        "taxable_income": taxable,
        "tax": round(tax, 2),
        "effective_rate": round(tax / annual_income * 100, 2) if annual_income else 0,
        "estimated_withheld": round(estimated_withheld, 2),
        "refund": round(refund, 2),
        "refund_eligible": refund > 0,
        "message": "",
    }


def get_student_tax_guide() -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("  大学生报税指南")
    lines.append("=" * 60)
    lines.append("")
    lines.append("【申报时间】")
    lines.append("  每年 3月1日 - 6月30日 办理上年度汇算清缴")
    lines.append("")
    lines.append("【适用人群】")
    lines.append("  有兼职收入（家教、实习、稿酬等）的大学生")
    lines.append("")
    lines.append("【所需材料】")
    lines.append("  ① 身份证")
    lines.append("  ② 兼职收入记录（银行流水、平台账单）")
    lines.append("  ③ 专项附加扣除信息（租房合同等）")
    lines.append("  ④ 已预缴税款记录（个税APP可查）")
    lines.append("")
    lines.append("【操作步骤】")
    lines.append('  1. 下载个人所得税APP并注册登录')
    lines.append('  2. 进入综合所得年度汇算')
    lines.append('  3. 选择申报年度为上一年')
    lines.append("  4. 核对收入信息（系统自动带出）")
    lines.append("  5. 填报专项附加扣除")
    lines.append("  6. 系统计算应退/应补税额")
    lines.append("  7. 提交申报，绑定银行卡等待退税")
    lines.append("")
    lines.append("【注意事项】")
    for tip in STUDENT_TAX_TIPS:
        lines.append(f"  {tip}")
    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def get_cert_info(cert_key: str) -> dict:
    return CERT_EXAMS.get(cert_key, {})


def generate_study_plan(cert_key: str, start_date_str: str, daily_hours: float = 2.0) -> dict:
    cert = CERT_EXAMS.get(cert_key)
    if not cert:
        return {"error": f"未找到考试: {cert_key}"}
    try:
        start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "日期格式错误，请使用 YYYY-MM-DD"}
    total_hours = cert["total_hours"]
    days_needed = int(total_hours / daily_hours) + 1
    end_date = start + timedelta(days=days_needed)
    weeks = []
    hours_per_week = daily_hours * 7
    subjects = cert["subjects"]
    hours_map = cert["study_hours"]
    current_date = start
    remaining = {s: hours_map.get(s, 0) for s in subjects}
    total_remaining = total_hours
    week_num = 1
    while total_remaining > 0 and week_num <= 104:
        week_subjects = []
        week_hours = min(hours_per_week, total_remaining)
        allocated = 0
        for s in subjects:
            if remaining.get(s, 0) > 0:
                share = min(remaining[s], max(1, week_hours * remaining[s] / total_remaining))
                share = round(share, 1)
                allocated += share
                remaining[s] -= share
                remaining[s] = max(0, remaining[s])
                week_subjects.append((s, share))
                total_remaining -= share
        week_end = current_date + timedelta(days=6)
        weeks.append({
            "week": week_num,
            "start": current_date.isoformat(),
            "end": week_end.isoformat(),
            "hours": round(week_hours, 1),
            "subjects": week_subjects,
        })
        current_date = week_end + timedelta(days=1)
        week_num += 1
    return {
        "cert_name": cert["name"],
        "total_hours": total_hours,
        "daily_hours": daily_hours,
        "days_needed": days_needed,
        "start_date": start_date_str,
        "end_date": end_date.isoformat(),
        "weeks": weeks,
        "subjects": subjects,
        "subject_hours": hours_map,
    }


def format_study_plan(cert_key: str, start_date_str: str, daily_hours: float = 2.0) -> str:
    plan = generate_study_plan(cert_key, start_date_str, daily_hours)
    if "error" in plan:
        return f"❌ {plan['error']}"
    lines = []
    lines.append("=" * 60)
    lines.append(f"  {plan['cert_name']} - 学习计划")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"📅 开始: {plan['start_date']}  →  结束: {plan['end_date']}")
    lines.append(f"⏱ 总学时: {plan['total_hours']}h  |  每日: {plan['daily_hours']}h  |  共需: {plan['days_needed']}天")
    lines.append("")
    lines.append("📚 科目分配:")
    for s in plan['subjects']:
        h = plan['subject_hours'].get(s, 0)
        pct = h / plan['total_hours'] * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        lines.append(f"  {s:12s} {h:>4d}h {bar} {pct:.0f}%")
    lines.append("")
    lines.append("📋 每周计划:")
    lines.append(f"  {'周次':>4s}  {'起始':>12s}  {'结束':>12s}  {'学时':>6s}  {'科目':<30s}")
    lines.append("  " + "-" * 66)
    for w in plan['weeks'][:30]:
        subs = ", ".join(f"{s}({h}h)" for s, h in w['subjects'])
        lines.append(f"  {w['week']:4d}  {w['start']:>12s}  {w['end']:>12s}  {w['hours']:5.1f}h  {subs[:40]}")
    if len(plan['weeks']) > 30:
        lines.append(f"  ... 还有 {len(plan['weeks']) - 30} 周 ...")
    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)
