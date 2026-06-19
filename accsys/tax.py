"""税务计算模块"""
from __future__ import annotations
from decimal import Decimal
from datetime import datetime
from .database import get_conn
from .vouchers import next_voucher_no

PIT_RATES = [
    (0, 36000, 0.03, 0),
    (36000, 144000, 0.10, 2520),
    (144000, 300000, 0.20, 16920),
    (300000, 420000, 0.25, 31920),
    (420000, 660000, 0.30, 52920),
    (660000, 960000, 0.35, 85920),
    (960000, float('inf'), 0.45, 181920),
]


def compute_vat(revenue, rate) -> dict:
    """纯计算：根据含税销售额与税率，返回增值税明细。

    返回 {rate, revenue, tax_exclusive, tax_amount}。
    """
    revenue_d = Decimal(str(revenue))
    rate_d = Decimal(str(rate))
    tax_exclusive = revenue_d / (Decimal('1') + rate_d)
    tax_amount = revenue_d - tax_exclusive
    return {
        'rate': float(rate_d),
        'revenue': float(revenue_d),
        'tax_exclusive': round(float(tax_exclusive), 2),
        'tax_amount': round(float(tax_amount), 2),
    }


def compute_pit(income) -> dict:
    """纯计算：根据月应纳税所得额，按七级超额累进返回个税明细。

    返回 {income, total_tax, after_tax, brackets:[{lower,upper,rate,taxable,tax}]}。
    """
    income_d = Decimal(str(income))
    if income_d <= 0:
        return {
            'income': float(income_d),
            'total_tax': 0.0,
            'after_tax': float(income_d),
            'brackets': [],
        }

    tax = Decimal('0')
    brackets = []
    for lower, upper, rate, _quick in PIT_RATES:
        if income_d > lower:
            taxable = min(income_d, Decimal(str(upper))) - Decimal(str(lower))
            level_tax = taxable * Decimal(str(rate))
            tax += level_tax
            brackets.append({
                'lower': lower,
                'upper': upper,
                'rate': rate,
                'taxable': float(taxable),
                'tax': float(level_tax),
            })

    total_tax = round(float(tax), 2)
    return {
        'income': float(income_d),
        'total_tax': total_tax,
        'after_tax': round(float(income_d) - total_tax, 2),
        'brackets': brackets,
    }


def calc_vat():
    print("\n── 增值税计算 ──")
    print("纳税人类型 / 适用税率:")
    print("  1 = 一般纳税人 13% — 销售货物 / 加工修理修配 / 有形动产租赁 / 进口货物")
    print("  2 = 一般纳税人 9%  — 交通运输 / 邮政 / 建筑 / 不动产租赁销售 / 农产品")
    print("  3 = 一般纳税人 6%  — 现代服务 / 金融服务 / 生活服务 / 销售无形资产")
    print("  4 = 小规模纳税人 3% — 标准征收率")
    print("  5 = 小规模纳税人 1% — 现行优惠征收率")
    type_map = {"1": 0.13, "2": 0.09, "3": 0.06, "4": 0.03, "5": 0.01}
    t = input("选择: ").strip()
    rate = type_map.get(t)
    if not rate:
        print("无效选择")
        return

    rev_str = input("含税销售额: ").strip()
    try:
        revenue = Decimal(rev_str)
        if revenue <= 0:
            print("销售额必须大于0")
            return
    except Exception:
        print("无效金额")
        return

    r = compute_vat(revenue, rate)
    tax_exclusive = r['tax_exclusive']
    tax_amount = r['tax_amount']

    print(f"\n{'─' * 40}")
    print(f"  增值税计算明细")
    print(f"{'─' * 40}")
    print(f"  税率:                  {r['rate'] * 100:.0f}%")
    print(f"  含税销售额:            {r['revenue']:>12.2f}")
    print(f"  不含税销售额:          {tax_exclusive:>12.2f}")
    print(f"  增值税额:              {tax_amount:>12.2f}")
    print(f"{'─' * 40}")

    if input("\n是否生成凭证? (y/n): ").strip().lower() == 'y':
        date_str = input("日期 (YYYY-MM-DD, 留空=今天): ").strip()
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        year, month = dt.year, dt.month

        conn = get_conn()
        v_no = next_voucher_no(year, month)
        cur_v = conn.execute(
            "INSERT INTO vouchers (voucher_no, date, summary, fiscal_year, fiscal_month) VALUES (?, ?, ?, ?, ?)",
            (v_no, date_str, "确认增值税", year, month))
        v_id = cur_v.lastrowid
        conn.execute(
            "INSERT INTO journal_entries (voucher_id, account_code, debit, credit) VALUES (?, ?, ?, ?)",
            (v_id, '1002', float(revenue), 0))
        conn.execute(
            "INSERT INTO journal_entries (voucher_id, account_code, debit, credit) VALUES (?, ?, ?, ?)",
            (v_id, '6001', 0, float(tax_exclusive)))
        conn.execute(
            "INSERT INTO journal_entries (voucher_id, account_code, debit, credit) VALUES (?, ?, ?, ?)",
            (v_id, '2221', 0, float(tax_amount)))
        conn.commit()
        conn.close()
        print(f"[OK] 凭证 {v_no} 已生成")


def calc_pit():
    print("\n── 个人所得税计算 ──")
    inc_str = input("月应纳税所得额 (税前收入-五险一金-5000): ").strip()
    try:
        income = Decimal(inc_str)
    except Exception:
        print("无效金额")
        return

    if income <= 0:
        print("应纳税所得额 <= 0，无需缴纳个人所得税")
        return

    r = compute_pit(income)
    total_tax = r['total_tax']

    print(f"\n{'─' * 56}")
    print(f"  个人所得税计算明细")
    print(f"{'─' * 56}")
    print(f"  应纳税所得额:          {r['income']:>12.2f}")
    print(f"{'─' * 56}")
    print(f"{'级距':<16} {'税率':<8} {'应纳税额':<14} {'税款':<12}")
    for b in r['brackets']:
        amt = b['taxable']
        if amt > 0:
            lower_label = f"{b['lower']:,}" if b['lower'] > 0 else "0"
            upper_label = "以上" if b['upper'] == float('inf') else f"{b['upper']:,}"
            level = f"{lower_label}-{upper_label}"
            print(f"  {level:<14} {b['rate']*100:.0f}%{'':<4} {amt:>10.2f} {'':>2} {b['tax']:>8.2f}")
    print(f"{'─' * 56}")
    print(f"{'应缴个人所得税':<28} {total_tax:>12.2f}")
    print(f"  税后收入:              {r['after_tax']:>12.2f}")
    print(f"{'─' * 56}")

    if input("\n是否生成凭证? (y/n): ").strip().lower() == 'y':
        date_str = input("日期 (YYYY-MM-DD, 留空=今天): ").strip()
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        year, month = dt.year, dt.month

        conn = get_conn()
        v_no = next_voucher_no(year, month)
        cur_v = conn.execute(
            "INSERT INTO vouchers (voucher_no, date, summary, fiscal_year, fiscal_month) VALUES (?, ?, ?, ?, ?)",
            (v_no, date_str, "代扣代缴个人所得税", year, month))
        v_id = cur_v.lastrowid
        conn.execute(
            "INSERT INTO journal_entries (voucher_id, account_code, debit, credit) VALUES (?, ?, ?, ?)",
            (v_id, '2211', float(total_tax), 0))
        conn.execute(
            "INSERT INTO journal_entries (voucher_id, account_code, debit, credit) VALUES (?, ?, ?, ?)",
            (v_id, '2221', 0, float(total_tax)))
        conn.commit()
        conn.close()
        print(f"[OK] 凭证 {v_no} 已生成")
