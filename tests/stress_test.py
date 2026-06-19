"""
高压测试 - 大量数据下验证系统稳定性和性能
"""
from __future__ import annotations

import sys, os, time, tempfile, random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

import accsys as acc

tmp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
tmp_db.close()
acc.database.get_db_path = lambda: tmp_db.name
acc.database.get_accounts_path = lambda: tempfile.NamedTemporaryFile(suffix='.json', delete=False).name
for mod in [acc.backup, acc.attachments]:
    if hasattr(mod, 'get_db_path'):
        mod.get_db_path = lambda pt=tmp_db.name: pt

acc.init_db()
acc.ensure_accounts()
acc.init_users()
acc.init_alert_rules()
acc.init_attachment_dir()
acc.CURRENT_USER = {'username': 'admin', 'display_name': 'admin', 'role': 'admin'}

results = {}
BATCH = 200  # vouchers per month
MONTHS = 12

# ── 1. 批量凭证创建 ──────────────────────────
def quick_v(year, month, day, summary, entries):
    conn = acc.get_conn()
    vno = acc.next_voucher_no(year, month)
    cur = conn.execute(
        "INSERT INTO vouchers (voucher_no, date, summary, fiscal_year, fiscal_month) VALUES (?,?,?,?,?)",
        (vno, f"{year}-{month:02d}-{day:02d}", summary, year, month))
    vid = cur.lastrowid
    for code, direction, amount in entries:
        conn.execute(
            "INSERT INTO journal_entries (voucher_id, account_code, debit, credit) VALUES (?,?,?,?)",
            (vid, code, amount if direction == 'd' else 0, amount if direction == 'c' else 0))
    conn.commit()
    conn.close()

print("=" * 60)
print("高压测试开始")
print(f"  批次数: {BATCH} 凭证/月 × {MONTHS} 个月 = {BATCH * MONTHS} 总凭证")
print(f"  预计分录: ~{BATCH * MONTHS * 2} 条")
print("=" * 60)

t0 = time.time()
total_vouchers = 0
entries_list = [
    ("1002", "d"), ("6001", "c"), ("2221", "c"),
    ("6401", "d"), ("1002", "c"),
    ("2211", "d"), ("1002", "c"),
    ("1122", "d"), ("1002", "c"),
    ("6602", "d"), ("1002", "c"),
]
templates = [
    ("销售商品", [("1122","d",0), ("6001","c",0), ("2221","c",0)]),
    ("采购原料", [("1403","d",0), ("2202","c",0)]),
    ("支付费用", [("6602","d",0), ("1002","c",0)]),
    ("收到货款", [("1002","d",0), ("1122","c",0)]),
    ("支付工资", [("2211","d",0), ("1002","c",0), ("2221","c",0)]),
]

for year in [2025, 2026]:
    for month in range(1, 13):
        base = month * 1000
        for i in range(BATCH):
            tpl = random.choice(templates)
            summary = f"{tpl[0]}-{year}{month:02d}-{i:04d}"
            entries = []
            for code, direction, _ in tpl[1]:
                amt = round(random.uniform(100, 50000), 2)
                entries.append((code, direction, amt))
            quick_v(year, month, random.randint(1, 28), summary, entries)
            total_vouchers += 1
    print(f"  {year}年完成")

elapsed = time.time() - t0
results['批量创建'] = f"{total_vouchers}条凭证 / {elapsed:.2f}s = {total_vouchers/elapsed:.0f} 条/秒"

# ── 2. 科目余额计算 ──────────────────────────
t0 = time.time()
for _ in range(10):
    accts = acc.load_accounts_from_db()
    balances = acc.calc_balances(accts)
elapsed = time.time() - t0
results['科目余额(×10)'] = f"{elapsed:.3f}s"

# ── 3. 三张报表 ──────────────────────────────
t0 = time.time()
for _ in range(5):
    bs = acc.balance_sheet()
    inc = acc.income_statement()
    cf = acc.cash_flow_statement()
elapsed = time.time() - t0
results['三张报表(×5)'] = f"{elapsed:.3f}s"

# ── 4. 财务比率 ──────────────────────────────
t0 = time.time()
for _ in range(20):
    ratios = acc.calc_financial_ratios()
elapsed = time.time() - t0
results['财务比率(×20)'] = f"{elapsed:.3f}s"

# ── 5. 凭证查询 ──────────────────────────────
t0 = time.time()
for year in [2025, 2026]:
    for month in [0, 3, 6, 9, 12]:
        conn = acc.get_conn()
        if month > 0:
            rows = conn.execute("SELECT COUNT(*) FROM vouchers WHERE fiscal_year=? AND fiscal_month=?", (year, month)).fetchone()[0]
        else:
            rows = conn.execute("SELECT COUNT(*) FROM vouchers WHERE fiscal_year=?", (year,)).fetchone()[0]
        conn.close()
elapsed = time.time() - t0
results['凭证查询(×10)'] = f"{elapsed:.3f}s"

# ── 6. 异常检测 ──────────────────────────────
t0 = time.time()
anomalies = acc.detect_anomalies()
elapsed = time.time() - t0
results['异常检测'] = f"{elapsed:.3f}s ({len(anomalies)} 条异常)"

# ── 7. 期末结账 ──────────────────────────────
t0 = time.time()
result = acc.auto_close_period(2025, 12)
elapsed = time.time() - t0
close_msg = result.get('status', result.get('error', 'unknown'))
results['期末结账'] = f"{elapsed:.3f}s ({close_msg})"

# ── 8. 数据库大小 ────────────────────────────
db_size = os.path.getsize(tmp_db.name)
results['数据库大小'] = f"{db_size/1024/1024:.1f} MB"

# ── 9. 高压批量操作 ──────────────────────────
t0 = time.time()
for i in range(500):
    conn = acc.get_conn()
    conn.execute("SELECT COUNT(*) FROM journal_entries").fetchone()
    conn.close()
elapsed = time.time() - t0
results['500次DB连接'] = f"{elapsed:.3f}s"

# ── 10. 预警检查 ─────────────────────────────
t0 = time.time()
alerts = acc.check_alerts()
elapsed = time.time() - t0
results['预警检查'] = f"{elapsed:.3f}s ({len(alerts)} 条预警)"

# ── 11. 库存管理 ─────────────────────────────
acc.add_product("P999", "高压测试品", "原材料", "个", 10.0)
t0 = time.time()
for i in range(100):
    acc.inventory_in(1, random.randint(10, 100), round(random.uniform(8, 12), 2), f"高压入库-{i}")
    acc.inventory_out(1, random.randint(5, 20), f"高压出库-{i}")
elapsed = time.time() - t0
results['库存200笔操作'] = f"{elapsed:.3f}s"

# ── 总结 ─────────────────────────────────────
print("\n" + "=" * 60)
print("高压测试结果")
print("=" * 60)
all_pass = True
for k, v in results.items():
    # 提取秒数判定
    if 's' in v:
        try:
            sec = float(v.split('s')[0])
            status = "PASS" if sec < 10 else ("SLOW" if sec < 30 else "FAIL")
            if status == "FAIL":
                all_pass = False
        except:
            status = "  - "
    else:
        status = "    "
    print(f"  [{status}] {k}: {v}")

print("=" * 60)
print(f"最终判定: {'全部通过' if all_pass else '有性能问题'}")
print(f"总耗时: {sum(float(v.split('s')[0]) for v in results.values() if 's' in v and '(' not in v.split('s')[0]):.1f}s")
print(f"数据库: {db_size/1024/1024:.1f} MB")

# 清理
os.unlink(tmp_db.name)
try:
    os.unlink(tmp_db.name + '-journal')
    os.unlink(tmp_db.name + '-wal')
    os.unlink(tmp_db.name + '-shm')
except:
    pass
print("清理完成")
