"""Database connection and initialization for the accounting system."""

from __future__ import annotations

import sqlite3
import json
import os
import sys
import csv
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Tuple, Any
import urllib.request
import urllib.error
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

from .constants import DB_FILE, EXCEL_FILE, ACCOUNTS_FILE, DEFAULT_ACCOUNTS, CATEGORY_LABELS, NATURE_LABELS


def _base_dir() -> str:
    """数据文件基目录：打包(exe)时用 exe 所在目录，开发时用包目录。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_db_path() -> str:
    override = os.environ.get("ACCSYS_DB_PATH")
    if override:
        return override
    return os.path.join(_base_dir(), DB_FILE)


def get_excel_path() -> str:
    return os.path.join(_base_dir(), EXCEL_FILE)


def get_accounts_path() -> str:
    return os.path.join(_base_dir(), ACCOUNTS_FILE)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_conn()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS accounts (
            code        TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            category    TEXT NOT NULL CHECK(category IN ('asset','liability','equity','income','expense')),
            nature      TEXT NOT NULL CHECK(nature IN ('debit','credit')),
            level       INTEGER DEFAULT 1,
            parent      TEXT DEFAULT '',
            is_contra   INTEGER DEFAULT 0,
            is_active   INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS vouchers (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            voucher_no      TEXT NOT NULL UNIQUE,
            date            TEXT NOT NULL,
            summary         TEXT NOT NULL,
            attachment_count INTEGER DEFAULT 0,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fiscal_year     INTEGER NOT NULL,
            fiscal_month    INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS journal_entries (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            voucher_id      INTEGER NOT NULL,
            account_code    TEXT NOT NULL,
            debit           DECIMAL(18,2) DEFAULT 0,
            credit          DECIMAL(18,2) DEFAULT 0,
            currency        TEXT DEFAULT 'CNY',
            exchange_rate   DECIMAL(10,4) DEFAULT 1.0000,
            FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
            FOREIGN KEY (account_code) REFERENCES accounts(code)
        );

        CREATE TABLE IF NOT EXISTS fixed_assets (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            name                TEXT NOT NULL,
            asset_account       TEXT NOT NULL DEFAULT '1601',
            deprec_account      TEXT NOT NULL DEFAULT '1602',
            original_value      DECIMAL(18,2) NOT NULL,
            residual_value      DECIMAL(18,2) DEFAULT 0,
            useful_life_months  INTEGER NOT NULL,
            depreciation_method TEXT NOT NULL CHECK(depreciation_method IN ('straight','double','sum-of-years')),
            purchase_date       TEXT NOT NULL,
            accumulated_deprec  DECIMAL(18,2) DEFAULT 0,
            is_active           INTEGER DEFAULT 1,
            FOREIGN KEY (asset_account) REFERENCES accounts(code),
            FOREIGN KEY (deprec_account) REFERENCES accounts(code)
        );

        CREATE TABLE IF NOT EXISTS exchange_rates (
            currency    TEXT NOT NULL,
            date        TEXT NOT NULL,
            rate        DECIMAL(10,4) NOT NULL,
            PRIMARY KEY (currency, date)
        );

        CREATE TABLE IF NOT EXISTS opening_balances (
            account_code    TEXT PRIMARY KEY,
            amount          DECIMAL(18,2) DEFAULT 0,
            fiscal_year     INTEGER DEFAULT 2026,
            FOREIGN KEY (account_code) REFERENCES accounts(code)
        );
    ''')
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'viewer' CHECK(role IN ('admin','accountant','viewer')),
            display_name TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_code TEXT NOT NULL,
            fiscal_year INTEGER NOT NULL,
            fiscal_month INTEGER NOT NULL,
            budget_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
            note TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(account_code, fiscal_year, fiscal_month),
            FOREIGN KEY (account_code) REFERENCES accounts(code)
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT DEFAULT '',
            unit TEXT DEFAULT '个',
            unit_price DECIMAL(18,2) DEFAULT 0,
            quantity DECIMAL(18,2) DEFAULT 0,
            min_stock DECIMAL(18,2) DEFAULT 0,
            location TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS inventory_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            trans_type TEXT NOT NULL CHECK(trans_type IN ('in','out','adjust')),
            quantity DECIMAL(18,2) NOT NULL,
            unit_price DECIMAL(18,2) DEFAULT 0,
            ref_type TEXT DEFAULT '',
            ref_id TEXT DEFAULT '',
            note TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS inventory_warehouse (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            location TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            target_type TEXT DEFAULT '',
            target_id TEXT DEFAULT '',
            detail TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alert_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            indicator TEXT NOT NULL,
            operator TEXT NOT NULL CHECK(operator IN ('gt','lt','gte','lte','eq')),
            threshold DECIMAL(18,2) NOT NULL,
            enabled INTEGER DEFAULT 1,
            level TEXT DEFAULT 'warning' CHECK(level IN ('info','warning','critical')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alert_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id INTEGER,
            message TEXT NOT NULL,
            level TEXT DEFAULT 'warning',
            resolved INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (rule_id) REFERENCES alert_rules(id)
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bank_statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount DECIMAL(18,2) NOT NULL,
            balance DECIMAL(18,2) DEFAULT 0,
            ref_no TEXT DEFAULT '',
            is_reconciled INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reconciliation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            statement_id INTEGER NOT NULL,
            voucher_id INTEGER,
            match_type TEXT DEFAULT 'auto' CHECK(match_type IN ('auto','manual','unmatched')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (statement_id) REFERENCES bank_statements(id),
            FOREIGN KEY (voucher_id) REFERENCES vouchers(id)
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            department TEXT DEFAULT '',
            position TEXT DEFAULT '',
            base_salary DECIMAL(18,2) DEFAULT 0,
            insurance DECIMAL(18,2) DEFAULT 0,
            housing_fund DECIMAL(18,2) DEFAULT 0,
            tax_threshold DECIMAL(18,2) DEFAULT 5000,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS payroll_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            gross_pay DECIMAL(18,2) DEFAULT 0,
            insurance DECIMAL(18,2) DEFAULT 0,
            housing_fund DECIMAL(18,2) DEFAULT 0,
            taxable_income DECIMAL(18,2) DEFAULT 0,
            income_tax DECIMAL(18,2) DEFAULT 0,
            deductions DECIMAL(18,2) DEFAULT 0,
            net_pay DECIMAL(18,2) DEFAULT 0,
            status TEXT DEFAULT 'draft' CHECK(status IN ('draft','confirmed','paid')),
            voucher_id INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (voucher_id) REFERENCES vouchers(id)
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            budget DECIMAL(18,2) DEFAULT 0,
            start_date TEXT,
            end_date TEXT,
            status TEXT DEFAULT 'active' CHECK(status IN ('active','completed','suspended')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voucher_id INTEGER,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            file_type TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS period_close (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            closed_at TEXT,
            status TEXT DEFAULT 'open',
            action TEXT,
            note TEXT,
            UNIQUE(year, month)
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS blockchain (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            index_no INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            previous_hash TEXT NOT NULL DEFAULT '',
            hash TEXT NOT NULL,
            nonce INTEGER NOT NULL DEFAULT 0,
            data TEXT NOT NULL DEFAULT '{}',
            voucher_id INTEGER,
            voucher_no TEXT,
            UNIQUE(index_no)
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS esg_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER DEFAULT 0,
            indicator TEXT NOT NULL,
            value REAL NOT NULL DEFAULT 0,
            unit TEXT DEFAULT '',
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(category, year, month, indicator)
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS micro_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income','expense')),
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
    """)
    conn.commit()
    init_alert_rules()
    conn.close()


def ensure_accounts() -> None:
    path = get_accounts_path()
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_ACCOUNTS, f, ensure_ascii=False, indent=2)

    conn = get_conn()
    existing = conn.execute("SELECT COUNT(*) as cnt FROM accounts").fetchone()
    if existing['cnt'] == 0:
        for code, info in DEFAULT_ACCOUNTS.items():
            conn.execute(
                "INSERT OR IGNORE INTO accounts (code, name, category, nature, level, parent, is_contra) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (code, info['name'], info['category'], info['nature'],
                 info['level'], info['parent'], 1 if info.get('contra') else 0)
            )
        conn.commit()
    conn.close()


def load_accounts_from_db() -> List[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM accounts WHERE is_active=1 ORDER BY code").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_account_dict(accounts: List[dict]) -> dict:
    return {a['code']: a for a in accounts}


def show_accounts() -> None:
    accounts = load_accounts_from_db()
    if not accounts:
        print("  暂无科目数据")
        return
    acc_dict = get_account_dict(accounts)
    print(f"\n{'编码':<8} {'科目名称':<14} {'类别':<10} {'余额方向':<8} {'层级':<4}")
    print("-" * 54)
    for a in accounts:
        prefix = "  " * (a['level'] - 1)
        cat = CATEGORY_LABELS.get(a['category'], a['category'])
        nat = NATURE_LABELS.get(a['nature'], a['nature'])
        contra = " (备抵)" if a['is_contra'] else ""
        name = a['name']
        has_children = any(a2['parent'] == a['code'] for a2 in accounts)
        icon = "[+] " if has_children else "    "
        print(f"{icon}{prefix}{a['code']:<8} {name:<12} {cat:<10} {nat:<8} {a['level']:<4}{contra}")


def add_account() -> None:
    code = input("科目编码 (如 100101): ").strip()
    if not code:
        print("科目编码不能为空")
        return
    name = input("科目名称: ").strip()
    if not name:
        print("科目名称不能为空")
        return
    print("类别: 1=资产 2=负债 3=权益 4=收入 5=费用")
    cat_map = {"1": "asset", "2": "liability", "3": "equity", "4": "income", "5": "expense"}
    cat_key = input("选择类别编号: ").strip()
    category = cat_map.get(cat_key)
    if not category:
        print("无效类别")
        return
    nature = "debit" if category in ("asset", "expense") else "credit"
    parent = input("上级科目编码 (留空无上级): ").strip()
    level = 1
    if parent:
        conn = get_conn()
        p = conn.execute("SELECT level FROM accounts WHERE code=?", (parent,)).fetchone()
        conn.close()
        if p:
            level = p['level'] + 1
        else:
            print("上级科目不存在，按一级科目处理")
            parent = ""
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO accounts (code, name, category, nature, level, parent) VALUES (?, ?, ?, ?, ?, ?)",
            (code, name, category, nature, level, parent))
        conn.commit()
        print(f"[OK] 科目 {code}-{name} 添加成功")
    except sqlite3.IntegrityError:
        print(f"[ERR] 科目编码 {code} 已存在")
    conn.close()
    _sync_accounts_to_json()


def _sync_accounts_to_json() -> None:
    accounts = load_accounts_from_db()
    data = {}
    for a in accounts:
        info = {
            "name": a['name'], "category": a['category'], "nature": a['nature'],
            "level": a['level'], "parent": a['parent'],
        }
        if a['is_contra']:
            info["contra"] = True
        data[a['code']] = info
    with open(get_accounts_path(), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def init_alert_rules() -> None:
    from .constants import DEFAULT_ALERT_RULES
    conn = get_conn()
    if conn.execute("SELECT COUNT(*) FROM alert_rules").fetchone()[0] == 0:
        for name, indicator, op, threshold, level in DEFAULT_ALERT_RULES:
            conn.execute("INSERT INTO alert_rules (name, indicator, operator, threshold, level) VALUES (?,?,?,?,?)",
                        (name, indicator, op, threshold, level))
        conn.commit()
    conn.close()
