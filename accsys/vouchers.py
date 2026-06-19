"""
凭证管理模块 (Vouchers)

提供记账凭证的生成、显示、查询、导入/导出等功能。
"""

from __future__ import annotations

import csv
import sqlite3
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from .database import get_conn
from .accounts import load_accounts_from_db, get_account_dict


def next_voucher_no(year: int, month: int) -> str:
    conn = get_conn()
    row = conn.execute(
        "SELECT voucher_no FROM vouchers WHERE fiscal_year=? AND fiscal_month=? ORDER BY id DESC LIMIT 1",
        (year, month)).fetchone()
    conn.close()
    if row:
        parts = row['voucher_no'].split('-')
        seq = int(parts[-1]) + 1
    else:
        seq = 1
    return f"记-{year}-{month:02d}-{seq:04d}"


def create_voucher() -> None:
    accounts = load_accounts_from_db()
    acc_dict = get_account_dict(accounts)

    print("\n── 录入记账凭证 ──")
    date_str = input("日期 (YYYY-MM-DD, 留空=今天): ").strip()
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print("日期格式错误")
        return
    year, month = dt.year, dt.month

    summary = input("摘要: ").strip()
    if not summary:
        print("摘要不能为空")
        return

    print("\n输入分录 (至少一条借方、一条贷方):")
    print("格式: 科目编码 金额 方向(d/c) [币种] [汇率]")
    print("空行结束输入\n")

    entries: List[dict] = []
    total_debit = Decimal('0')
    total_credit = Decimal('0')

    while True:
        line = input(f"  分录 {len(entries) + 1}: ").strip()
        if not line:
            if len(entries) < 2:
                print("  至少需要两条分录")
                continue
            if total_debit == Decimal('0') or total_credit == Decimal('0'):
                print("  借贷双方不能为零")
                continue
            if total_debit != total_credit:
                print(f"  借贷不平！借={total_debit:.2f} 贷={total_credit:.2f} 差额={total_debit - total_credit:.2f}")
                continue
            break

        parts = line.split()
        if len(parts) < 3:
            print("  格式错误: 科目编码 金额 方向[d/c]")
            continue

        code = parts[0]
        if code not in acc_dict:
            print(f"  科目 {code} 不存在")
            continue

        try:
            amount = Decimal(parts[1])
            if amount <= 0:
                print("  金额必须大于0")
                continue
        except Exception:
            print("  金额无效")
            continue

        direction = parts[2].lower()
        if direction not in ('d', 'c'):
            print("  方向为 d(借方) 或 c(贷方)")
            continue

        currency = 'CNY'
        rate = Decimal('1.0000')
        if len(parts) >= 4:
            currency = parts[3].upper()
        if len(parts) >= 5:
            try:
                rate = Decimal(parts[4])
            except Exception:
                pass

        if direction == 'd':
            total_debit += amount
        else:
            total_credit += amount

        entries.append({
            "account_code": code,
            "debit": float(amount) if direction == 'd' else 0,
            "credit": float(amount) if direction == 'c' else 0,
            "currency": currency,
            "exchange_rate": float(rate),
        })

    voucher_no = next_voucher_no(year, month)

    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO vouchers (voucher_no, date, summary, fiscal_year, fiscal_month) VALUES (?, ?, ?, ?, ?)",
            (voucher_no, date_str, summary, year, month))
        v_id = cur.lastrowid

        for e in entries:
            conn.execute(
                "INSERT INTO journal_entries (voucher_id, account_code, debit, credit, currency, exchange_rate) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (v_id, e['account_code'], e['debit'], e['credit'], e['currency'], e['exchange_rate']))

        conn.commit()
        print(f"\n[OK] 凭证已生成: {voucher_no}")
        show_voucher(v_id, conn)
    except Exception as e:
        conn.rollback()
        print(f"[ERR] 保存失败: {e}")
    conn.close()


def show_voucher(v_id: int, conn: Optional[sqlite3.Connection] = None) -> None:
    close_after = False
    if conn is None:
        conn = get_conn()
        close_after = True

    v = conn.execute("SELECT * FROM vouchers WHERE id=?", (v_id,)).fetchone()
    if not v:
        print("凭证不存在")
        if close_after:
            conn.close()
        return

    entries = conn.execute(
        "SELECT je.*, a.name as account_name FROM journal_entries je "
        "LEFT JOIN accounts a ON je.account_code = a.code "
        "WHERE je.voucher_id=? ORDER BY je.id", (v_id,)).fetchall()

    print(f"\n{'=' * 72}")
    print(f"  记账凭证")
    print(f"{'=' * 72}")
    print(f"  凭证号: {v['voucher_no']}     日期: {v['date']}     附件: {v['attachment_count']}张")
    print(f"  摘要: {v['summary']}")
    print(f"{'=' * 72}")
    print(f"{'科目编码':<10} {'科目名称':<14} {'币种':<6} {'汇率':<8} {'借方金额':>14} {'贷方金额':>14}")
    print("-" * 72)
    for e in entries:
        print(f"{e['account_code']:<10} {str(e['account_name'] or ''):<14}"
              f"{e['currency']:<6} {e['exchange_rate']:<8.4f}"
              f"{e['debit']:>14.2f} {e['credit']:>14.2f}")
    print("-" * 72)
    total_d = sum(e['debit'] for e in entries)
    total_c = sum(e['credit'] for e in entries)
    print(f"{'合计':<38} {total_d:>14.2f} {total_c:>14.2f}")
    if abs(total_d - total_c) < 0.01:
        print(f"  借贷平衡 [OK]")
    else:
        print(f"  借贷不平 [ERR]  差额: {total_d - total_c:.2f}")
    print(f"{'=' * 72}")

    if close_after:
        conn.close()


def list_vouchers(year: Optional[int] = None, month: Optional[int] = None) -> None:
    conn = get_conn()
    query = "SELECT * FROM vouchers"
    params: List[Any] = []
    conditions = []
    if year:
        conditions.append("fiscal_year=?")
        params.append(year)
    if month:
        conditions.append("fiscal_month=?")
        params.append(month)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY voucher_no DESC LIMIT 50"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        print("  暂无凭证")
        return

    print(f"\n{'凭证号':<20} {'日期':<12} {'摘要':<20} {'分录数':<6}")
    print("-" * 60)
    for r in rows:
        conn2 = get_conn()
        cnt = conn2.execute("SELECT COUNT(*) as c FROM journal_entries WHERE voucher_id=?", (r['id'],)).fetchone()['c']
        conn2.close()
        summary = r['summary'] if len(r['summary']) <= 18 else r['summary'][:18] + '..'
        print(f"{r['voucher_no']:<20} {r['date']:<12} {summary:<20} {cnt:<6}")


def view_voucher_detail() -> None:
    no = input("输入凭证号 (如 记-2026-06-0001): ").strip()
    if not no:
        return
    conn = get_conn()
    v = conn.execute("SELECT * FROM vouchers WHERE voucher_no=?", (no,)).fetchone()
    if v:
        show_voucher(v['id'], conn)
    else:
        print("凭证不存在")
    conn.close()


def batch_export_vouchers(filepath: str, fmt: str = 'csv', year: str = '', month: str = '') -> Dict[str, Any]:
    if fmt == 'csv':
        return batch_export_csv(filepath)
    else:
        return {"error": f"暂不支持 {fmt} 格式导出，请使用 CSV"}


def batch_export_csv(filepath: str) -> Dict[str, Any]:
    conn = get_conn()
    rows = conn.execute("""
        SELECT v.voucher_no, v.date, v.summary,
               je.account_code, a.name as account_name, je.debit, je.credit
        FROM vouchers v
        JOIN journal_entries je ON v.id = je.voucher_id
        JOIN accounts a ON je.account_code = a.code
        ORDER BY v.date, v.id, je.id
    """).fetchall()
    conn.close()

    if not rows:
        return {"error": "没有凭证数据可导出"}

    try:
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['凭证号', '日期', '摘要', '科目编码', '科目名称', '借方', '贷方'])
            for r in rows:
                writer.writerow([
                    r['voucher_no'], r['date'], r['summary'],
                    r['account_code'], r['account_name'],
                    f"{r['debit']:.2f}" if r['debit'] else '0.00',
                    f"{r['credit']:.2f}" if r['credit'] else '0.00',
                ])
        return {"message": f"已导出 {len(rows)} 行数据", "count": len(rows)}
    except Exception as e:
        return {"error": f"导出失败: {e}"}


def import_vouchers(filepath: str) -> Dict[str, Any]:
    if filepath.endswith('.csv'):
        return _import_csv(filepath)
    elif filepath.endswith('.xlsx'):
        return {"error": "Excel导入暂不支持，请使用CSV格式"}
    else:
        return {"error": "不支持的文件格式，请使用CSV"}


def _import_csv(filepath: str) -> Dict[str, Any]:
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if not rows:
            return {"error": "文件为空"}

        conn = get_conn()
        count = 0
        current_v_no = None
        v_id = None
        for r in rows:
            v_no = r.get('凭证号', '').strip()
            if v_no != current_v_no:
                current_v_no = v_no
                date_str = r.get('日期', date.today().isoformat())
                summary = r.get('摘要', '导入凭证')
                parts = v_no.split('-') if '-' in v_no else ['0000', '00', '0000']
                y = int(parts[0]) if parts[0].isdigit() else date.today().year
                m = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else date.today().month
                cur = conn.execute(
                    "INSERT INTO vouchers (voucher_no, date, summary, fiscal_year, fiscal_month) VALUES (?,?,?,?,?)",
                    (v_no, date_str, summary, y, m))
                v_id = cur.lastrowid
                count += 1

            code = r.get('科目编码', '').strip()
            debit = float(r.get('借方', 0) or 0)
            credit = float(r.get('贷方', 0) or 0)
            if code and v_id:
                conn.execute(
                    "INSERT INTO journal_entries (voucher_id, account_code, debit, credit) VALUES (?,?,?,?)",
                    (v_id, code, debit, credit))

        conn.commit()
        conn.close()
        return {"count": count, "message": f"成功导入 {count} 张凭证"}
    except Exception as e:
        return {"error": f"导入失败: {e}"}
