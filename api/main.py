"""FastAPI 后端（阶段3）。

复用 accsys 业务核心（纯计算 + 报表 *_data）与 SQLAlchemy ORM 模型，
对外提供现代 JSON API，并自动生成 OpenAPI/Swagger 文档（/docs）。

运行：uvicorn api.main:app --reload
文档：http://localhost:8000/docs
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Dict, List

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import accsys as acc
from accsys.db import SessionLocal, get_database_url
from accsys.models import JournalEntry, Voucher

from .schemas import AccountOut, Health, PitResult, ReportRow, VatResult, VoucherOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    acc.init_db()
    acc.ensure_accounts()
    yield


app = FastAPI(title="会计系统 API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/api/health", response_model=Health, tags=["系统"])
def health():
    url = get_database_url()
    backend = "postgresql" if url.startswith("postgres") else "sqlite"
    return Health(status="ok", database=backend)


@app.get("/api/ratios", tags=["报表"])
def ratios() -> Dict[str, float]:
    return acc.calc_financial_ratios()


@app.get("/api/accounts", response_model=List[AccountOut], tags=["科目"])
def accounts(db: Session = Depends(get_db)):
    accts = acc.load_accounts_from_db()
    balances = acc.calc_balances(accts)
    rows = db.execute(
        select(
            JournalEntry.account_code,
            func.coalesce(func.sum(JournalEntry.debit), 0),
            func.coalesce(func.sum(JournalEntry.credit), 0),
        ).group_by(JournalEntry.account_code)
    ).all()
    mv = {r[0]: (float(r[1]), float(r[2])) for r in rows}
    out = []
    for a in accts:
        dt, ct = mv.get(a["code"], (0.0, 0.0))
        out.append(AccountOut(
            code=a["code"], name=a["name"], category=a["category"],
            debit=dt, credit=ct, balance=float(balances.get(a["code"], 0)),
        ))
    return out


@app.get("/api/vouchers", response_model=List[VoucherOut], tags=["凭证"])
def vouchers(
    year: int = Query(2026),
    month: int = Query(0, ge=0, le=12),
    db: Session = Depends(get_db),
):
    totals = dict(db.execute(
        select(JournalEntry.voucher_id, func.coalesce(func.sum(JournalEntry.debit), 0))
        .group_by(JournalEntry.voucher_id)
    ).all())

    stmt = select(Voucher).where(Voucher.fiscal_year == year)
    if month > 0:
        stmt = stmt.where(Voucher.fiscal_month == month)
    stmt = stmt.order_by(Voucher.id.desc())

    out = []
    for v in db.execute(stmt).scalars().all():
        out.append(VoucherOut(
            id=v.id, voucher_no=v.voucher_no, date=v.date, summary=v.summary,
            fiscal_year=v.fiscal_year, fiscal_month=v.fiscal_month,
            total=float(totals.get(v.id, 0) or 0),
        ))
    return out


@app.get("/api/reports/balance", response_model=List[ReportRow], tags=["报表"])
def report_balance():
    return acc.balance_sheet_data()


@app.get("/api/reports/income", response_model=List[ReportRow], tags=["报表"])
def report_income():
    return acc.income_statement_data()


@app.get("/api/reports/cashflow", response_model=List[ReportRow], tags=["报表"])
def report_cashflow():
    return acc.cash_flow_statement_data()


@app.get("/api/tax/vat", response_model=VatResult, tags=["税务"])
def tax_vat(revenue: float = Query(..., gt=0), rate: float = Query(0.13)):
    return acc.compute_vat(revenue, rate)


@app.get("/api/tax/pit", response_model=PitResult, tags=["税务"])
def tax_pit(income: float = Query(..., description="月应纳税所得额")):
    return acc.compute_pit(income)
