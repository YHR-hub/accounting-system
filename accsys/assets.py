"""固定资产折旧模块"""
from __future__ import annotations
from decimal import Decimal
from datetime import datetime
from typing import Optional
from .database import get_conn
from .vouchers import next_voucher_no


def add_fixed_asset():
    print("\n── 新增固定资产 ──")
    name = input("资产名称: ").strip()
    if not name:
        return
    try:
        original = Decimal(input("原值: ").strip())
        residual = Decimal(input("残值 (留空=0): ").strip() or "0")
        months = int(input("使用年限(月): ").strip())
        if original <= 0 or months <= 0:
            print("原值和年限必须大于0")
            return
        if residual >= original:
            print("残值不能大于等于原值")
            return
    except ValueError:
        print("输入数值无效")
        return

    print("折旧方法: 1=直线法  2=双倍余额递减法  3=年数总和法")
    method_map = {"1": "straight", "2": "double", "3": "sum-of-years"}
    m = input("选择: ").strip()
    method = method_map.get(m)
    if not method:
        print("无效选择")
        return

    purchase_date = input("购入日期 (YYYY-MM-DD, 留空=今天): ").strip()
    if not purchase_date:
        purchase_date = datetime.now().strftime("%Y-%m-%d")

    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO fixed_assets (name, original_value, residual_value, useful_life_months, depreciation_method, purchase_date) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (name, float(original), float(residual), months, method, purchase_date))
    conn.commit()
    aid = cur.lastrowid
    conn.close()

    months_depr = calc_depreciation(float(original), float(residual), months, method)
    print(f"\n[OK] 资产已添加 (ID={aid})")
    print(f"  原值: {original:.2f}  残值: {residual:.2f}  年限: {months}月")
    print(f"  折旧方法: {method}")
    print(f"  月折旧额: {months_depr:.2f}")


def calc_depreciation(original: float, residual: float, months: int, method: str) -> float:
    depreciable = original - residual
    if method == "straight":
        return round(depreciable / months, 2)
    elif method == "double":
        rate = 2.0 / (months / 12)
        month_rate = rate / 12
        depr = original * month_rate
        return round(depr, 2)
    elif method == "sum-of-years":
        total_years = months / 12
        years_sum = total_years * (total_years + 1) / 2
        month_depr = depreciable / years_sum / 12
        return round(month_depr, 2)
    return 0.0


def list_fixed_assets():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM fixed_assets WHERE is_active=1 ORDER BY id").fetchall()
    conn.close()

    if not rows:
        print("  暂无固定资产")
        return

    method_names = {"straight": "直线法", "double": "双倍余额递减法", "sum-of-years": "年数总和法"}
    print(f"\n{'ID':<4} {'名称':<14} {'原值':>10} {'残值':>8} {'年限(月)':<8} {'方法':<14} {'累计折旧':>10}")
    print("-" * 72)
    for r in rows:
        print(f"{r['id']:<4} {r['name']:<14} {r['original_value']:>10.2f} {r['residual_value']:>8.2f} "
              f"{r['useful_life_months']:<8} {method_names.get(r['depreciation_method'], r['depreciation_method']):<14} "
              f"{r['accumulated_deprec']:>10.2f}")


def run_depreciation(year: Optional[int] = None, month: Optional[int] = None):
    conn = get_conn()
    assets = conn.execute("SELECT * FROM fixed_assets WHERE is_active=1").fetchall()
    if not assets:
        print("  暂无固定资产")
        conn.close()
        return 0

    if year is not None and month is not None:
        period = f"{year:04d}-{month:02d}"
    else:
        period = input("计提期间 (YYYY-MM, 留空=本月): ").strip()
        if not period:
            period = datetime.now().strftime("%Y-%m")
    period_date = period + "-01"

    count = 0
    total_depr = Decimal('0')
    for a in assets:
        remained = a['useful_life_months'] - (a['accumulated_deprec'] / (
            calc_depreciation(a['original_value'], a['residual_value'], a['useful_life_months'], a['depreciation_method'])
            if calc_depreciation(a['original_value'], a['residual_value'], a['useful_life_months'], a['depreciation_method']) > 0 else 1
        ))
        if remained <= 0:
            continue

        depr = Decimal(str(calc_depreciation(
            a['original_value'], a['residual_value'], a['useful_life_months'], a['depreciation_method'])))
        if depr <= 0:
            continue

        conn.execute("UPDATE fixed_assets SET accumulated_deprec = accumulated_deprec + ? WHERE id=?",
                     (float(depr), a['id']))
        total_depr += depr
        count += 1

        year, month = map(int, period.split('-'))
        v_no = next_voucher_no(year, month)

        cur_v = conn.execute(
            "INSERT INTO vouchers (voucher_no, date, summary, fiscal_year, fiscal_month) VALUES (?, ?, ?, ?, ?)",
            (v_no, period_date, f"计提{a['name']}折旧", year, month))
        v_id = cur_v.lastrowid

        conn.execute(
            "INSERT INTO journal_entries (voucher_id, account_code, debit, credit) VALUES (?, ?, ?, ?)",
            (v_id, '6602', float(depr), 0))
        conn.execute(
            "INSERT INTO journal_entries (voucher_id, account_code, debit, credit) VALUES (?, ?, ?, ?)",
            (v_id, '1602', 0, float(depr)))

    conn.commit()
    conn.close()
    print(f"\n[OK] 折旧计提完成: {count}项资产, 总折旧额 {float(total_depr):.2f}")
    return count
