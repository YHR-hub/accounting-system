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
from .models import Account, JournalEntry, OpeningBalance, User, Voucher

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
