"""SQLAlchemy ORM 模型，镜像现有 accounting.db 架构。

阶段2并行数据层：供未来 FastAPI / Postgres 使用，不影响现有 sqlite3 代码。
列定义与 accsys/database.py 的建表语句保持一致。
"""
from __future__ import annotations

from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    TIMESTAMP,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base

MONEY = Numeric(18, 2)
RATE = Numeric(10, 4)


class Account(Base):
    __tablename__ = "accounts"
    code: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    nature: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1)
    parent: Mapped[str] = mapped_column(Text, default="")
    is_contra: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[int] = mapped_column(Integer, default=1)


class Voucher(Base):
    __tablename__ = "vouchers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    voucher_no: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    date: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    attachment_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_month: Mapped[int] = mapped_column(Integer, nullable=False)


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    voucher_id: Mapped[int] = mapped_column(ForeignKey("vouchers.id", ondelete="CASCADE"), nullable=False)
    account_code: Mapped[str] = mapped_column(ForeignKey("accounts.code"), nullable=False)
    debit: Mapped[object] = mapped_column(MONEY, default=0)
    credit: Mapped[object] = mapped_column(MONEY, default=0)
    currency: Mapped[str] = mapped_column(Text, default="CNY")
    exchange_rate: Mapped[object] = mapped_column(RATE, default=1)


class FixedAsset(Base):
    __tablename__ = "fixed_assets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    asset_account: Mapped[str] = mapped_column(ForeignKey("accounts.code"), nullable=False, default="1601")
    deprec_account: Mapped[str] = mapped_column(ForeignKey("accounts.code"), nullable=False, default="1602")
    original_value: Mapped[object] = mapped_column(MONEY, nullable=False)
    residual_value: Mapped[object] = mapped_column(MONEY, default=0)
    useful_life_months: Mapped[int] = mapped_column(Integer, nullable=False)
    depreciation_method: Mapped[str] = mapped_column(Text, nullable=False)
    purchase_date: Mapped[str] = mapped_column(Text, nullable=False)
    accumulated_deprec: Mapped[object] = mapped_column(MONEY, default=0)
    is_active: Mapped[int] = mapped_column(Integer, default=1)


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    currency: Mapped[str] = mapped_column(Text, primary_key=True)
    date: Mapped[str] = mapped_column(Text, primary_key=True)
    rate: Mapped[object] = mapped_column(RATE, nullable=False)


class OpeningBalance(Base):
    __tablename__ = "opening_balances"
    account_code: Mapped[str] = mapped_column(ForeignKey("accounts.code"), primary_key=True)
    amount: Mapped[object] = mapped_column(MONEY, default=0)
    fiscal_year: Mapped[int] = mapped_column(Integer, default=2026)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False, default="viewer")
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (UniqueConstraint("account_code", "fiscal_year", "fiscal_month"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_code: Mapped[str] = mapped_column(ForeignKey("accounts.code"), nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_month: Mapped[int] = mapped_column(Integer, nullable=False)
    budget_amount: Mapped[object] = mapped_column(MONEY, nullable=False, default=0)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, default="")
    unit: Mapped[str] = mapped_column(Text, default="个")
    unit_price: Mapped[object] = mapped_column(MONEY, default=0)
    quantity: Mapped[object] = mapped_column(MONEY, default=0)
    min_stock: Mapped[object] = mapped_column(MONEY, default=0)
    location: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    trans_type: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[object] = mapped_column(MONEY, nullable=False)
    unit_price: Mapped[object] = mapped_column(MONEY, default=0)
    ref_type: Mapped[str] = mapped_column(Text, default="")
    ref_id: Mapped[str] = mapped_column(Text, default="")
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())


class InventoryWarehouse(Base):
    __tablename__ = "inventory_warehouse"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    location: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[int] = mapped_column(Integer, default=1)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    target_type: Mapped[str] = mapped_column(Text, default="")
    target_id: Mapped[str] = mapped_column(Text, default="")
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())


class AlertRule(Base):
    __tablename__ = "alert_rules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    indicator: Mapped[str] = mapped_column(Text, nullable=False)
    operator: Mapped[str] = mapped_column(Text, nullable=False)
    threshold: Mapped[object] = mapped_column(MONEY, nullable=False)
    enabled: Mapped[int] = mapped_column(Integer, default=1)
    level: Mapped[str] = mapped_column(Text, default="warning")
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())


class AlertHistory(Base):
    __tablename__ = "alert_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("alert_rules.id"), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[str] = mapped_column(Text, default="warning")
    resolved: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())


class BankStatement(Base):
    __tablename__ = "bank_statements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_date: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[object] = mapped_column(MONEY, nullable=False)
    balance: Mapped[object] = mapped_column(MONEY, default=0)
    ref_no: Mapped[str] = mapped_column(Text, default="")
    is_reconciled: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())


class Reconciliation(Base):
    __tablename__ = "reconciliation"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    statement_id: Mapped[int] = mapped_column(ForeignKey("bank_statements.id"), nullable=False)
    voucher_id: Mapped[int | None] = mapped_column(ForeignKey("vouchers.id"), nullable=True)
    match_type: Mapped[str] = mapped_column(Text, default="auto")
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())


class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    department: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[str] = mapped_column(Text, default="")
    base_salary: Mapped[object] = mapped_column(MONEY, default=0)
    insurance: Mapped[object] = mapped_column(MONEY, default=0)
    housing_fund: Mapped[object] = mapped_column(MONEY, default=0)
    tax_threshold: Mapped[object] = mapped_column(MONEY, default=5000)
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())


class PayrollRecord(Base):
    __tablename__ = "payroll_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    gross_pay: Mapped[object] = mapped_column(MONEY, default=0)
    insurance: Mapped[object] = mapped_column(MONEY, default=0)
    housing_fund: Mapped[object] = mapped_column(MONEY, default=0)
    taxable_income: Mapped[object] = mapped_column(MONEY, default=0)
    income_tax: Mapped[object] = mapped_column(MONEY, default=0)
    deductions: Mapped[object] = mapped_column(MONEY, default=0)
    net_pay: Mapped[object] = mapped_column(MONEY, default=0)
    status: Mapped[str] = mapped_column(Text, default="draft")
    voucher_id: Mapped[int | None] = mapped_column(ForeignKey("vouchers.id"), nullable=True)


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    budget: Mapped[object] = mapped_column(MONEY, default=0)
    start_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    end_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, default="active")
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())


class Attachment(Base):
    __tablename__ = "attachments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    voucher_id: Mapped[int | None] = mapped_column(ForeignKey("vouchers.id", ondelete="CASCADE"), nullable=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    filepath: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    file_type: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())


class PeriodClose(Base):
    __tablename__ = "period_close"
    __table_args__ = (UniqueConstraint("year", "month"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    closed_at: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, default="open")
    action: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class BlockchainBlock(Base):
    __tablename__ = "blockchain"
    __table_args__ = (UniqueConstraint("index_no"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    index_no: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[str] = mapped_column(Text, nullable=False)
    previous_hash: Mapped[str] = mapped_column(Text, nullable=False, default="")
    hash: Mapped[str] = mapped_column(Text, nullable=False)
    nonce: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    data: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    voucher_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    voucher_no: Mapped[str | None] = mapped_column(Text, nullable=True)


class EsgData(Base):
    __tablename__ = "esg_data"
    __table_args__ = (UniqueConstraint("category", "year", "month", "indicator"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, default=0)
    indicator: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    unit: Mapped[str] = mapped_column(Text, default="")
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str | None] = mapped_column(Text, nullable=True)


class MicroLedger(Base):
    __tablename__ = "micro_ledger"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str | None] = mapped_column(Text, nullable=True)
