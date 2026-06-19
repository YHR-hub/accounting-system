"""ORM 版数据层（认 DATABASE_URL，SQLite/PostgreSQL 通用）。

供 FastAPI 使用，全部经 SQLAlchemy ORM/Core 访问，无任何方言专属 SQL。
与 accsys/database.py 等旧 sqlite3 函数并存，互不影响（GUI/webapp 仍用旧函数）。
逻辑与 accsys.accounts.calc_balances / accsys.reports.*_data 保持一致。
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .constants import DEFAULT_ACCOUNTS
from .db import Base
from .tax import compute_pit
from .models import (
    Account,
    AlertHistory,
    AlertRule,
    AuditLog,
    Budget,
    Employee,
    EsgData,
    FixedAsset,
    InventoryTransaction,
    JournalEntry,
    OpeningBalance,
    PayrollRecord,
    Product,
    Project,
    User,
    Voucher,
)

ZERO = Decimal("0")


def _dec(v) -> Decimal:
    return Decimal(str(v)) if v is not None else ZERO


# ── 初始化与播种 ────────────────────────────────────
def init_schema(engine) -> None:
    Base.metadata.create_all(engine)


def seed_accounts(session: Session) -> None:
    if session.scalar(select(func.count()).select_from(Account)):
        return
    for code, info in DEFAULT_ACCOUNTS.items():
        session.add(Account(
            code=code,
            name=info["name"],
            category=info["category"],
            nature=info["nature"],
            level=info.get("level", 1),
            parent=info.get("parent", ""),
            is_contra=1 if info.get("contra") else 0,
            is_active=1,
        ))


def seed_users(session: Session) -> None:
    if session.scalar(select(func.count()).select_from(User)):
        return
    defaults = [
        ("admin", "admin123", "admin", "管理员"),
        ("accountant", "acc123", "accountant", "会计员"),
        ("viewer", "view123", "viewer", "查询员"),
    ]
    for username, pwd, role, display in defaults:
        session.add(User(
            username=username,
            password_hash=hashlib.sha256(pwd.encode()).hexdigest(),
            role=role,
            display_name=display,
            is_active=1,
        ))


def bootstrap(engine) -> None:
    """建表并播种科目/用户（幂等）。"""
    init_schema(engine)
    with Session(engine) as session:
        seed_accounts(session)
        seed_users(session)
        session.commit()


# ── 读取 ────────────────────────────────────────────
def load_accounts(session: Session) -> List[dict]:
    rows = session.execute(
        select(Account).where(Account.is_active == 1).order_by(Account.code)
    ).scalars().all()
    return [{
        "code": a.code, "name": a.name, "category": a.category, "nature": a.nature,
        "level": a.level, "parent": a.parent, "is_contra": a.is_contra, "is_active": a.is_active,
    } for a in rows]


def _movements(session: Session, as_of: Optional[str] = None) -> Dict[str, tuple]:
    stmt = select(
        JournalEntry.account_code,
        func.coalesce(func.sum(JournalEntry.debit), 0),
        func.coalesce(func.sum(JournalEntry.credit), 0),
    )
    if as_of:
        stmt = stmt.where(
            JournalEntry.voucher_id.in_(select(Voucher.id).where(Voucher.date <= as_of))
        )
    stmt = stmt.group_by(JournalEntry.account_code)
    return {code: (_dec(d), _dec(c)) for code, d, c in session.execute(stmt).all()}


def calc_balances(
    session: Session,
    accounts: Optional[List[dict]] = None,
    as_of: Optional[str] = None,
    use_opening: bool = True,
) -> Dict[str, Decimal]:
    if accounts is None:
        accounts = load_accounts(session)
    movements = _movements(session, as_of)

    opening: Dict[str, Decimal] = {}
    if use_opening:
        year = datetime.now().year
        for code, amt in session.execute(
            select(OpeningBalance.account_code, OpeningBalance.amount)
            .where(OpeningBalance.fiscal_year == year)
        ).all():
            opening[code] = _dec(amt)

    balances: Dict[str, Decimal] = {}
    for a in accounts:
        code = a["code"]
        debit, credit = movements.get(code, (ZERO, ZERO))
        ob = opening.get(code, ZERO)
        if (a["nature"] == "debit" and not a["is_contra"]) or (a["nature"] == "credit" and a["is_contra"]):
            bal = ob + debit - credit
        else:
            bal = ob + credit - debit
        if abs(bal) < Decimal("0.001"):
            bal = ZERO
        balances[code] = bal
    return balances


# ── 报表（结构化 [{label, amount}]） ─────────────────
def balance_sheet_data(session: Session) -> List[Dict[str, Any]]:
    accounts = load_accounts(session)
    balances = calc_balances(session, accounts)

    assets, liabilities, equities = [], [], []
    for a in accounts:
        bal = balances.get(a["code"], ZERO)
        if a["category"] == "asset":
            assets.append((a["name"], -bal if a["is_contra"] else bal))
        elif a["category"] == "liability":
            liabilities.append((a["name"], bal))
        elif a["category"] == "equity":
            equities.append((a["name"], bal))

    total_income = sum((balances.get(a["code"], ZERO) for a in accounts if a["category"] == "income"), ZERO)
    total_expense = sum((balances.get(a["code"], ZERO) for a in accounts if a["category"] == "expense"), ZERO)
    net_profit = total_income - total_expense

    total_asset = sum((abs(b) for _, b in assets), ZERO)
    total_liability = sum((b for _, b in liabilities), ZERO)
    total_equity = sum((b for _, b in equities), ZERO) + max(net_profit, ZERO)

    rows: List[Dict[str, Any]] = []
    for name, b in assets:
        rows.append({"label": name, "amount": float(b), "section": "asset"})
    rows.append({"label": "资产总计", "amount": float(total_asset), "section": "total"})
    for name, b in liabilities:
        rows.append({"label": name, "amount": float(b), "section": "liability"})
    rows.append({"label": "净利润(本年)", "amount": float(net_profit), "section": "equity"})
    for name, b in equities:
        rows.append({"label": name, "amount": float(b), "section": "equity"})
    rows.append({"label": "负债及所有者权益总计",
                 "amount": float(total_liability + total_equity), "section": "total"})
    return rows


def income_statement_data(session: Session) -> List[Dict[str, Any]]:
    accounts = load_accounts(session)
    balances = calc_balances(session, accounts)
    income_acc = [a for a in accounts if a["category"] == "income"]
    expense_acc = [a for a in accounts if a["category"] == "expense"]

    operating_revenue = ZERO
    other_income = ZERO
    for a in income_acc:
        bal = balances.get(a["code"], ZERO)
        if "收入" in a["name"]:
            operating_revenue += bal
        else:
            other_income += bal

    operating_expense = sum(
        (balances.get(a["code"], ZERO) for a in expense_acc if a["code"] not in ("6801",)), ZERO
    )
    tax_exp = balances.get("6801", ZERO) if any(a["code"] == "6801" for a in expense_acc) else ZERO

    gross_profit = operating_revenue - operating_expense
    net_profit = gross_profit + other_income - tax_exp

    rows: List[Dict[str, Any]] = [
        {"label": "一、营业收入", "amount": float(operating_revenue)},
        {"label": "二、营业成本及费用", "amount": float(operating_expense)},
        {"label": "三、营业利润", "amount": float(gross_profit)},
    ]
    if other_income != 0:
        rows.append({"label": "加：其他收益", "amount": float(other_income)})
    if tax_exp > 0:
        rows.append({"label": "减：所得税费用", "amount": float(tax_exp)})
    rows.append({"label": "四、净利润", "amount": float(net_profit)})
    return rows


def cash_flow_statement_data(session: Session) -> List[Dict[str, Any]]:
    accounts = load_accounts(session)
    acc_dict = {a["code"]: a for a in accounts}
    rows_db = session.execute(
        select(
            JournalEntry.account_code,
            func.coalesce(func.sum(JournalEntry.debit), 0),
            func.coalesce(func.sum(JournalEntry.credit), 0),
        ).group_by(JournalEntry.account_code)
    ).all()

    op_in = op_out = inv_in = inv_out = fin_in = fin_out = ZERO
    for code, d, c in rows_db:
        debit, credit = _dec(d), _dec(c)
        a = acc_dict.get(code)
        if not a:
            continue
        cat = a["category"]
        if cat == "income":
            op_in += credit
        elif cat == "expense":
            if code in ("6602", "6601", "6401", "6402", "6405", "6603"):
                op_out += debit
        elif code == "1002":
            op_in += credit
            op_out += debit
        elif code == "1601":
            inv_out += debit
            inv_in += credit
        elif code in ("2001", "2501"):
            fin_in += credit
            fin_out += debit
        elif code == "4001":
            fin_in += credit

    op_net = op_in - op_out
    inv_net = inv_in - inv_out
    fin_net = fin_in - fin_out
    net_change = op_net + inv_net + fin_net
    return [
        {"label": "一、经营活动现金流量净额", "amount": float(op_net)},
        {"label": "二、投资活动现金流量净额", "amount": float(inv_net)},
        {"label": "三、筹资活动现金流量净额", "amount": float(fin_net)},
        {"label": "四、现金及现金等价物净增加额", "amount": float(net_change)},
    ]


def financial_ratios(session: Session) -> Dict[str, float]:
    accounts = load_accounts(session)
    balances = calc_balances(session, accounts)

    asset_total = liability_total = equity_total = ZERO
    current_asset = current_liability = inventory = receivable = ZERO
    revenue = cost = expense_total = ZERO

    for a in accounts:
        code = a["code"]
        bal = balances.get(code, ZERO)
        cat = a["category"]
        if cat == "asset":
            asset_total += bal
            if code in ("1001", "1002", "1012", "1101"):
                current_asset += bal
            if code in ("1122",):
                receivable += bal
            if code in ("1403", "1405"):
                inventory += bal
        elif cat == "liability":
            liability_total += bal
            if code in ("2001", "2201", "2202", "2203", "2211", "2221", "2241"):
                current_liability += bal
        elif cat == "equity":
            equity_total += bal
        elif cat == "income":
            revenue += bal
        elif cat == "expense":
            expense_total += bal
            if code == "6401":
                cost += bal

    r: Dict[str, float] = {}
    ca, cl = float(current_asset), float(current_liability)
    r["流动比率"] = round(ca / cl, 2) if cl else 0
    r["速动比率"] = round((ca - float(inventory)) / cl, 2) if cl else 0
    at, lt = float(asset_total), float(liability_total)
    r["资产负债率"] = round(lt / at * 100, 2) if at else 0
    rev, cst = float(revenue), float(cost)
    r["毛利率"] = round((rev - cst) / rev * 100, 2) if rev else 0
    net_profit = rev - float(expense_total)
    r["净利率"] = round(net_profit / rev * 100, 2) if rev else 0
    et = float(equity_total)
    r["净资产收益率(ROE)"] = round(net_profit / et * 100, 2) if et else 0
    r["总资产报酬率(ROA)"] = round(net_profit / at * 100, 2) if at else 0
    r["应收账款周转率"] = round(rev / float(receivable), 2) if float(receivable) else 0
    r["存货周转率"] = round(cst / float(inventory), 2) if float(inventory) else 0
    r["费用占收入比"] = round(float(expense_total) / rev * 100, 2) if rev else 0
    r["净利润率"] = round(net_profit / rev * 100, 2) if rev else 0
    return r


# ── 凭证号 ──────────────────────────────────────────
def next_voucher_no(session: Session, year: int, month: int) -> str:
    last = session.execute(
        select(Voucher.voucher_no)
        .where(Voucher.fiscal_year == year, Voucher.fiscal_month == month)
        .order_by(Voucher.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    seq = int(last.split("-")[-1]) + 1 if last else 1
    return f"记-{year}-{month:02d}-{seq:04d}"


# ── 其他模块（只读列表，纯 ORM） ─────────────────────
def _f(x) -> float:
    try:
        return float(x) if x is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _s(x):
    return x.isoformat() if hasattr(x, "isoformat") else x


def list_products(session: Session) -> List[dict]:
    rows = session.execute(
        select(Product).where(Product.is_active == 1).order_by(Product.code)
    ).scalars().all()
    return [{
        "id": p.id, "code": p.code, "name": p.name, "category": p.category,
        "unit": p.unit, "unit_price": _f(p.unit_price), "quantity": _f(p.quantity),
        "amount": round(_f(p.unit_price) * _f(p.quantity), 2),
        "min_stock": _f(p.min_stock), "location": p.location,
    } for p in rows]


def list_inventory_transactions(session: Session, limit: int = 100) -> List[dict]:
    rows = session.execute(
        select(InventoryTransaction).order_by(InventoryTransaction.id.desc()).limit(limit)
    ).scalars().all()
    return [{
        "id": t.id, "product_id": t.product_id, "trans_type": t.trans_type,
        "quantity": _f(t.quantity), "unit_price": _f(t.unit_price),
        "ref_type": t.ref_type, "ref_id": t.ref_id, "note": t.note,
        "created_at": _s(t.created_at),
    } for t in rows]


def list_employees(session: Session) -> List[dict]:
    rows = session.execute(
        select(Employee).where(Employee.is_active == 1).order_by(Employee.code)
    ).scalars().all()
    return [{
        "id": e.id, "code": e.code, "name": e.name, "department": e.department,
        "position": e.position, "base_salary": _f(e.base_salary),
        "insurance": _f(e.insurance), "housing_fund": _f(e.housing_fund),
    } for e in rows]


def list_payroll_records(session: Session, year: int | None = None, month: int | None = None) -> List[dict]:
    stmt = select(PayrollRecord)
    if year:
        stmt = stmt.where(PayrollRecord.year == year)
    if month:
        stmt = stmt.where(PayrollRecord.month == month)
    rows = session.execute(stmt.order_by(PayrollRecord.id.desc())).scalars().all()
    return [{
        "id": r.id, "employee_id": r.employee_id, "year": r.year, "month": r.month,
        "gross_pay": _f(r.gross_pay), "income_tax": _f(r.income_tax),
        "net_pay": _f(r.net_pay), "status": r.status,
    } for r in rows]


def list_fixed_assets(session: Session) -> List[dict]:
    rows = session.execute(
        select(FixedAsset).where(FixedAsset.is_active == 1).order_by(FixedAsset.id)
    ).scalars().all()
    return [{
        "id": a.id, "name": a.name, "original_value": _f(a.original_value),
        "residual_value": _f(a.residual_value), "useful_life_months": a.useful_life_months,
        "depreciation_method": a.depreciation_method, "purchase_date": a.purchase_date,
        "accumulated_deprec": _f(a.accumulated_deprec),
        "net_value": round(_f(a.original_value) - _f(a.accumulated_deprec), 2),
    } for a in rows]


def list_projects(session: Session) -> List[dict]:
    rows = session.execute(select(Project).order_by(Project.code)).scalars().all()
    return [{
        "id": p.id, "code": p.code, "name": p.name, "budget": _f(p.budget),
        "start_date": p.start_date, "end_date": p.end_date, "status": p.status,
    } for p in rows]


def list_budgets(session: Session, year: int | None = None) -> List[dict]:
    stmt = select(Budget)
    if year:
        stmt = stmt.where(Budget.fiscal_year == year)
    rows = session.execute(
        stmt.order_by(Budget.account_code, Budget.fiscal_month)
    ).scalars().all()
    return [{
        "id": b.id, "account_code": b.account_code, "fiscal_year": b.fiscal_year,
        "fiscal_month": b.fiscal_month, "budget_amount": _f(b.budget_amount), "note": b.note,
    } for b in rows]


def list_alert_rules(session: Session) -> List[dict]:
    rows = session.execute(select(AlertRule).order_by(AlertRule.id)).scalars().all()
    return [{
        "id": r.id, "name": r.name, "indicator": r.indicator, "operator": r.operator,
        "threshold": _f(r.threshold), "enabled": r.enabled, "level": r.level,
    } for r in rows]


def list_alert_history(session: Session, limit: int = 100) -> List[dict]:
    rows = session.execute(
        select(AlertHistory).order_by(AlertHistory.id.desc()).limit(limit)
    ).scalars().all()
    return [{
        "id": h.id, "rule_id": h.rule_id, "message": h.message, "level": h.level,
        "resolved": h.resolved, "created_at": _s(h.created_at),
    } for h in rows]


def list_audit_logs(session: Session, limit: int = 100) -> List[dict]:
    rows = session.execute(
        select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
    ).scalars().all()
    return [{
        "id": a.id, "username": a.username, "action": a.action,
        "target_type": a.target_type, "target_id": a.target_id, "detail": a.detail,
        "created_at": _s(a.created_at),
    } for a in rows]


def list_esg_data(session: Session, year: int | None = None) -> List[dict]:
    stmt = select(EsgData)
    if year:
        stmt = stmt.where(EsgData.year == year)
    rows = session.execute(
        stmt.order_by(EsgData.category, EsgData.indicator)
    ).scalars().all()
    return [{
        "id": d.id, "category": d.category, "year": d.year, "month": d.month,
        "indicator": d.indicator, "value": _f(d.value), "unit": d.unit, "note": d.note,
    } for d in rows]


def list_vouchers(session: Session, year: int, month: int = 0) -> List[dict]:
    totals = dict(session.execute(
        select(JournalEntry.voucher_id, func.coalesce(func.sum(JournalEntry.debit), 0))
        .group_by(JournalEntry.voucher_id)
    ).all())
    stmt = select(Voucher).where(Voucher.fiscal_year == year)
    if month:
        stmt = stmt.where(Voucher.fiscal_month == month)
    stmt = stmt.order_by(Voucher.id.desc())
    return [{
        "id": v.id, "voucher_no": v.voucher_no, "date": v.date, "summary": v.summary,
        "fiscal_year": v.fiscal_year, "fiscal_month": v.fiscal_month,
        "total": float(totals.get(v.id, 0) or 0),
    } for v in session.execute(stmt).scalars().all()]


def list_accounts_with_movements(session: Session) -> List[dict]:
    accts = load_accounts(session)
    balances = calc_balances(session, accts)
    mv = _movements(session)
    out = []
    for a in accts:
        d, c = mv.get(a["code"], (ZERO, ZERO))
        out.append({
            "code": a["code"], "name": a["name"], "category": a["category"],
            "debit": float(d), "credit": float(c), "balance": float(balances.get(a["code"], ZERO)),
        })
    return out


# ── 写操作（由调用方负责 commit；校验失败抛 ValueError） ──
def create_product(session: Session, code: str, name: str, category: str = "",
                   unit: str = "个", unit_price: float = 0, quantity: float = 0,
                   min_stock: float = 0) -> dict:
    if session.scalar(select(Product).where(Product.code == code)):
        raise ValueError(f"商品编码 {code} 已存在")
    p = Product(code=code, name=name, category=category, unit=unit,
                unit_price=Decimal(str(unit_price)), quantity=Decimal(str(quantity)),
                min_stock=Decimal(str(min_stock)), is_active=1)
    session.add(p)
    session.flush()
    return {"id": p.id, "code": p.code, "name": p.name}


def _get_product(session: Session, product_id: int) -> Product:
    p = session.get(Product, product_id)
    if p is None:
        raise ValueError("商品不存在")
    return p


def inventory_in(session: Session, product_id: int, quantity: float,
                 unit_price: float = 0, note: str = "") -> dict:
    if quantity <= 0:
        raise ValueError("入库数量必须大于 0")
    p = _get_product(session, product_id)
    p.quantity = _dec(p.quantity) + Decimal(str(quantity))
    if unit_price:
        p.unit_price = Decimal(str(unit_price))
    session.add(InventoryTransaction(
        product_id=product_id, trans_type="in", quantity=Decimal(str(quantity)),
        unit_price=Decimal(str(unit_price)), note=note))
    session.flush()
    return {"product_id": product_id, "quantity": float(p.quantity)}


def inventory_out(session: Session, product_id: int, quantity: float, note: str = "") -> dict:
    if quantity <= 0:
        raise ValueError("出库数量必须大于 0")
    p = _get_product(session, product_id)
    if _dec(p.quantity) < Decimal(str(quantity)):
        raise ValueError(f"库存不足：现有 {float(p.quantity)}，需出 {quantity}")
    p.quantity = _dec(p.quantity) - Decimal(str(quantity))
    session.add(InventoryTransaction(
        product_id=product_id, trans_type="out", quantity=Decimal(str(quantity)),
        unit_price=p.unit_price, note=note))
    session.flush()
    return {"product_id": product_id, "quantity": float(p.quantity)}


def add_employee(session: Session, code: str, name: str, department: str = "",
                 position: str = "", base_salary: float = 0, insurance: float = 0,
                 housing_fund: float = 0) -> dict:
    if session.scalar(select(Employee).where(Employee.code == code)):
        raise ValueError(f"工号 {code} 已存在")
    e = Employee(code=code, name=name, department=department, position=position,
                 base_salary=Decimal(str(base_salary)), insurance=Decimal(str(insurance)),
                 housing_fund=Decimal(str(housing_fund)), is_active=1)
    session.add(e)
    session.flush()
    return {"id": e.id, "code": e.code, "name": e.name}


def add_fixed_asset(session: Session, name: str, original_value: float,
                    useful_life_months: int, purchase_date: str,
                    residual_value: float = 0, depreciation_method: str = "straight") -> dict:
    if useful_life_months <= 0:
        raise ValueError("使用年限(月)必须大于 0")
    a = FixedAsset(name=name, original_value=Decimal(str(original_value)),
                   residual_value=Decimal(str(residual_value)),
                   useful_life_months=useful_life_months,
                   depreciation_method=depreciation_method,
                   purchase_date=purchase_date, accumulated_deprec=Decimal("0"), is_active=1)
    session.add(a)
    session.flush()
    return {"id": a.id, "name": a.name}


def add_project(session: Session, code: str, name: str, budget: float = 0,
                start_date: str | None = None, end_date: str | None = None) -> dict:
    if session.scalar(select(Project).where(Project.code == code)):
        raise ValueError(f"项目编码 {code} 已存在")
    p = Project(code=code, name=name, budget=Decimal(str(budget)),
                start_date=start_date, end_date=end_date, status="active")
    session.add(p)
    session.flush()
    return {"id": p.id, "code": p.code, "name": p.name}


def calculate_payroll(session: Session, year: int, month: int) -> List[dict]:
    """为当月每位在职员工生成草稿工资记录（已存在则跳过）。

    个税采用年化估算：月应纳税所得额×12 套用年度累进税率后再÷12。
    """
    employees = session.execute(
        select(Employee).where(Employee.is_active == 1)
    ).scalars().all()
    created: List[dict] = []
    for e in employees:
        exists = session.scalar(
            select(PayrollRecord).where(
                PayrollRecord.employee_id == e.id,
                PayrollRecord.year == year,
                PayrollRecord.month == month,
            )
        )
        if exists:
            continue
        gross = _dec(e.base_salary)
        insurance = _dec(e.insurance)
        housing = _dec(e.housing_fund)
        threshold = _dec(e.tax_threshold) if e.tax_threshold is not None else Decimal("5000")
        taxable = gross - insurance - housing - threshold
        if taxable < 0:
            taxable = Decimal("0")
        annual_tax = compute_pit(float(taxable) * 12)["total_tax"]
        tax = round(annual_tax / 12, 2)
        net = float(gross - insurance - housing) - tax
        rec = PayrollRecord(
            employee_id=e.id, year=year, month=month, gross_pay=gross,
            insurance=insurance, housing_fund=housing, taxable_income=taxable,
            income_tax=Decimal(str(tax)), net_pay=Decimal(str(round(net, 2))), status="draft",
        )
        session.add(rec)
        session.flush()
        created.append({"employee_id": e.id, "name": e.name, "gross_pay": float(gross),
                        "income_tax": tax, "net_pay": round(net, 2)})
    return created
