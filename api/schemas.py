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


class ProductCreate(BaseModel):
    code: str
    name: str
    category: str = ""
    unit: str = "个"
    unit_price: float = 0
    quantity: float = 0
    min_stock: float = 0


class InventoryMove(BaseModel):
    product_id: int
    quantity: float
    unit_price: float = 0
    note: str = ""


class EmployeeCreate(BaseModel):
    code: str
    name: str
    department: str = ""
    position: str = ""
    base_salary: float = 0
    insurance: float = 0
    housing_fund: float = 0


class FixedAssetCreate(BaseModel):
    name: str
    original_value: float
    useful_life_months: int
    purchase_date: str
    residual_value: float = 0
    depreciation_method: str = "straight"


class ProjectCreate(BaseModel):
    code: str
    name: str
    budget: float = 0
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class PayrollRun(BaseModel):
    year: int
    month: int


class AccountCreate(BaseModel):
    code: str
    name: str
    category: str
    nature: Optional[str] = None
    parent: str = ""
