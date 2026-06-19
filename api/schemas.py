"""FastAPI 响应模型（Pydantic v2）。"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class Health(BaseModel):
    status: str
    database: str


class ReportRow(BaseModel):
    label: str
    amount: float
    section: Optional[str] = None


class AccountOut(BaseModel):
    code: str
    name: str
    category: str
    debit: float
    credit: float
    balance: float


class VoucherOut(BaseModel):
    id: int
    voucher_no: str
    date: str
    summary: str
    fiscal_year: int
    fiscal_month: int
    total: float


class VatResult(BaseModel):
    rate: float
    revenue: float
    tax_exclusive: float
    tax_amount: float


class PitBracket(BaseModel):
    lower: float
    upper: float
    rate: float
    taxable: float
    tax: float


class PitResult(BaseModel):
    income: float
    total_tax: float
    after_tax: float
    brackets: List[PitBracket]


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    username: str
    role: str
    display_name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class EntryIn(BaseModel):
    account_code: str
    debit: float = 0.0
    credit: float = 0.0


class VoucherCreate(BaseModel):
    date: str
    summary: str
    entries: List[EntryIn]


class VoucherCreated(BaseModel):
    id: int
    voucher_no: str
