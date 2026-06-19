"""Account balance calculation and trial balance for the accounting system."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

from .database import get_conn, load_accounts_from_db, get_account_dict, show_accounts as _show_accounts


def calc_balances(accounts: Optional[List[dict]] = None, as_of: Optional[str] = None, use_opening: bool = True) -> dict:
    if accounts is None:
        accounts = load_accounts_from_db()
    acc_dict = get_account_dict(accounts)

    conn = get_conn()
    query = "SELECT account_code, SUM(debit) as total_debit, SUM(credit) as total_credit FROM journal_entries"
    params: List[Any] = []
    if as_of:
        query += " WHERE voucher_id IN (SELECT id FROM vouchers WHERE date <= ?)"
        params.append(as_of)
    query += " GROUP BY account_code"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    balances: Dict[str, Decimal] = {}
    opening_balances: Dict[str, Decimal] = {}

    if use_opening:
        conn2 = get_conn()
        ob_rows = conn2.execute("SELECT account_code, amount FROM opening_balances WHERE fiscal_year = ?",
                                (datetime.now().year,)).fetchall()
        conn2.close()
        for r in ob_rows:
            opening_balances[r['account_code']] = Decimal(str(r['amount']))

    for a in accounts:
        code = a['code']
        is_contra = a['is_contra']
        nature = a['nature']

        debit_total = Decimal('0')
        credit_total = Decimal('0')
        for r in rows:
            if r['account_code'] == code:
                debit_total = Decimal(str(r['total_debit'] or '0'))
                credit_total = Decimal(str(r['total_credit'] or '0'))
                break

        ob = opening_balances.get(code, Decimal('0'))

        if (nature == 'debit' and not is_contra) or (nature == 'credit' and is_contra):
            balance = ob + debit_total - credit_total
        else:
            balance = ob + credit_total - debit_total

        if abs(balance) < Decimal('0.001'):
            balance = Decimal('0')
        balances[code] = balance

    return balances


def show_trial_balance() -> None:
    accounts = load_accounts_from_db()
    balances = calc_balances(accounts)

    print(f"\n{'='*70}")
    print(f"  试算平衡表 (Trial Balance)  -  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*70}")
    print(f"{'编码':<8} {'科目名称':<14} {'借方余额':>14} {'贷方余额':>14}")
    print("-" * 70)

    total_debit = Decimal('0')
    total_credit = Decimal('0')
    for a in accounts:
        code = a['code']
        balance = balances.get(code, Decimal('0'))
        name = a['name']
        if balance > 0 and a['nature'] == 'debit':
            print(f"{code:<8} {name:<14} {float(balance):>14.2f}")
            total_debit += balance
        elif balance > 0 and a['nature'] == 'credit':
            print(f"{code:<8} {name:<14} {float(balance):>14.2f}")
            total_credit += balance
        elif balance < 0:
            if a['nature'] == 'debit':
                print(f"{code:<8} {name:<14} {float(-balance):>14.2f}")
                total_credit += -balance
            else:
                print(f"{code:<8} {name:<14} {float(-balance):>14.2f}")
                total_debit += -balance
        else:
            print(f"{code:<8} {name:<14} {'':>14} {'':>14}")

    print("-" * 70)
    print(f"{'合计':<22} {float(total_debit):>14.2f} {float(total_credit):>14.2f}")
    if abs(total_debit - total_credit) < Decimal('0.01'):
        print(f"  [OK] 借贷平衡 | 差额: {float(total_debit - total_credit):.2f}")
    else:
        print(f"  [ERR] 借贷不平 | 差额: {float(total_debit - total_credit):.2f}")
    print("=" * 70)


def set_opening_balance() -> None:
    accounts = load_accounts_from_db()
    _show_accounts()
    code = input("\n输入科目编码: ").strip()
    if not any(a['code'] == code for a in accounts):
        print("科目不存在")
        return
    amt = input("期初余额 (借方为正, 贷方为负): ").strip()
    try:
        amount = Decimal(amt)
    except Exception:
        print("无效金额")
        return
    year = datetime.now().year
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO opening_balances (account_code, amount, fiscal_year) VALUES (?, ?, ?)",
        (code, float(amount), year))
    conn.commit()
    conn.close()
    total_debit = sum(a['name'] for a in accounts)
    print(f"[OK] 科目 {code} 期初余额已设置为 {amount:.2f}")


def get_all_accounts() -> list[dict[str, Any]]:
    """Return all account records from database."""
    return load_accounts_from_db()



