"""
种子数据脚本 - 用真实感数据填充数据库，供演示和截图使用。
运行: python seed_data.py
"""
from __future__ import annotations

import sys, os, random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import accsys as acc

acc.init_db()
acc.ensure_accounts()
acc.init_users()
acc.init_attachment_dir()

COMPANY = "星辰科技有限公司"
YEARS = [2026]
MONTHS = [1, 2, 3, 4, 5, 6]

sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
print(f"[开始] 填充种子数据 ({COMPANY})...")

# ── 1. 凭证 ────────────────────────────────────────────────
def quick_v(year: int, month: int, day: int, summary: str, entries: list[tuple[str, str, float]]):
    """简化版创建凭证，直接写 SQL。"""
    import sqlite3
    conn = acc.get_conn()
    vno = acc.next_voucher_no(year, month)
    date_str = f"{year}-{month:02d}-{day:02d}"
    cur = conn.execute(
        "INSERT INTO vouchers (voucher_no, date, summary, fiscal_year, fiscal_month) VALUES (?,?,?,?,?)",
        (vno, date_str, summary, year, month),
    )
    vid = cur.lastrowid
    for code, direction, amount in entries:
        debit = amount if direction == "d" else 0
        credit = amount if direction == "c" else 0
        conn.execute(
            "INSERT INTO journal_entries (voucher_id, account_code, debit, credit) VALUES (?,?,?,?)",
            (vid, code, debit, credit),
        )
    conn.commit()
    conn.close()
    return vno

# ── 2026年1月 ──
print("  1月...")
quick_v(2026, 1, 5,  "股东注资 - 张三",        [("1002","d",1000000), ("4001","c",1000000)])
quick_v(2026, 1, 6,  "购置办公设备",           [("1601","d",80000),   ("1002","c",80000)])
quick_v(2026, 1, 8,  "预付一季度房租",         [("1123","d",45000),   ("1002","c",45000)])
quick_v(2026, 1, 10, "采购原材料一批",         [("1403","d",120000),  ("2202","c",120000)])
quick_v(2026, 1, 15, "销售商品 - A客户",       [("1122","d",200000),  ("6001","c",180000), ("2221","c",20000)])
quick_v(2026, 1, 20, "支付员工工资",           [("2211","d",85000),   ("1002","c",72000), ("2221","c",8000), ("2241","c",5000)])
quick_v(2026, 1, 25, "收到A客户货款",          [("1002","d",200000),  ("1122","c",200000)])
quick_v(2026, 1, 28, "计提1月折旧",            [("6602","d",1200),    ("1602","c",1200)])
quick_v(2026, 1, 30, "支付电费",               [("6602","d",3200),    ("1002","c",3200)])
quick_v(2026, 1, 31, "结转销售成本",           [("6401","d",120000),  ("1405","c",120000)])

# ── 2026年2月 ──
print("   2月...")
quick_v(2026, 2, 2,  "购入专利使用权",         [("1701","d",50000),   ("1002","c",50000)])
quick_v(2026, 2, 5,  "采购原材料",             [("1403","d",95000),   ("2202","c",95000)])
quick_v(2026, 2, 10, "销售商品 - B客户",       [("1122","d",250000),  ("6001","c",225000), ("2221","c",25000)])
quick_v(2026, 2, 15, "销售商品 - C客户",       [("1122","d",150000),  ("6001","c",135000), ("2221","c",15000)])
quick_v(2026, 2, 20, "支付员工工资",           [("2211","d",85000),   ("1002","c",72000), ("2221","c",8000), ("2241","c",5000)])
quick_v(2026, 2, 22, "收到B客户货款",          [("1002","d",250000),  ("1122","c",250000)])
quick_v(2026, 2, 25, "支付供应商货款",         [("2202","d",80000),   ("1002","c",80000)])
quick_v(2026, 2, 28, "计提2月折旧",            [("6602","d",1200),    ("1602","c",1200)])
quick_v(2026, 2, 28, "支付网络推广费",         [("6601","d",15000),   ("1002","c",15000)])
quick_v(2026, 2, 28, "结转销售成本",           [("6401","d",100000),  ("1405","c",100000)])

# ── 2026年3月 ──
print("   3月...")
quick_v(2026, 3, 3,  "采购原材料",             [("1403","d",110000),  ("2202","c",110000)])
quick_v(2026, 3, 8,  "销售商品 - A客户",       [("1122","d",280000),  ("6001","c",252000), ("2221","c",28000)])
quick_v(2026, 3, 12, "销售商品 - D客户",       [("1122","d",180000),  ("6001","c",162000), ("2221","c",18000)])
quick_v(2026, 3, 15, "收到C客户货款",          [("1002","d",150000),  ("1122","c",150000)])
quick_v(2026, 3, 20, "支付员工工资",           [("2211","d",85000),   ("1002","c",72000), ("2221","c",8000), ("2241","c",5000)])
quick_v(2026, 3, 25, "购入运输车辆",           [("1601","d",120000),  ("1002","c",120000)])
quick_v(2026, 3, 28, "计提3月折旧",            [("6602","d",2200),    ("1602","c",2200)])
quick_v(2026, 3, 28, "支付一季度房租分摊",     [("6602","d",15000),   ("1123","c",15000)])
quick_v(2026, 3, 30, "收到D客户50%货款",       [("1002","d",90000),   ("1122","c",90000)])
quick_v(2026, 3, 31, "结转销售成本",           [("6401","d",140000),  ("1405","c",140000)])

# ── 2026年4月 ──
print("   4月...")
quick_v(2026, 4, 1,  "预付二季度房租",         [("1123","d",45000),   ("1002","c",45000)])
quick_v(2026, 4, 5,  "采购原材料",             [("1403","d",130000),  ("2202","c",130000)])
quick_v(2026, 4, 10, "销售商品 - A客户",       [("1122","d",320000),  ("6001","c",288000), ("2221","c",32000)])
quick_v(2026, 4, 15, "销售商品 - E客户",       [("1122","d",200000),  ("6001","c",180000), ("2221","c",20000)])
quick_v(2026, 4, 18, "收到A客户货款",          [("1002","d",280000),  ("1122","c",280000)])
quick_v(2026, 4, 20, "支付员工工资",           [("2211","d",88000),   ("1002","c",74000), ("2221","c",8500), ("2241","c",5500)])
quick_v(2026, 4, 25, "支付税款",               [("2221","d",45000),   ("1002","c",45000)])
quick_v(2026, 4, 28, "计提4月折旧",            [("6602","d",2200),    ("1602","c",2200)])
quick_v(2026, 4, 28, "销售商品 - B客户",       [("1122","d",220000),  ("6001","c",198000), ("2221","c",22000)])
quick_v(2026, 4, 30, "结转销售成本",           [("6401","d",150000),  ("1405","c",150000)])

# ── 2026年5月 ──
print("   5月...")
quick_v(2026, 5, 5,  "采购原材料",             [("1403","d",150000),  ("2202","c",150000)])
quick_v(2026, 5, 8,  "销售商品 - A客户",       [("1122","d",350000),  ("6001","c",315000), ("2221","c",35000)])
quick_v(2026, 5, 12, "收到E客户货款",          [("1002","d",200000),  ("1122","c",200000)])
quick_v(2026, 5, 15, "收到B客户货款",          [("1002","d",220000),  ("1122","c",220000)])
quick_v(2026, 5, 20, "支付员工工资",           [("2211","d",88000),   ("1002","c",74000), ("2221","c",8500), ("2241","c",5500)])
quick_v(2026, 5, 25, "销售商品 - C客户",       [("1122","d",260000),  ("6001","c",234000), ("2221","c",26000)])
quick_v(2026, 5, 28, "计提5月折旧",            [("6602","d",2200),    ("1602","c",2200)])
quick_v(2026, 5, 28, "支付供应商部分货款",     [("2202","d",100000),  ("1002","c",100000)])
quick_v(2026, 5, 31, "结转销售成本",           [("6401","d",160000),  ("1405","c",160000)])

# ── 2026年6月 ──
print("   6月...")
quick_v(2026, 6, 2,  "采购原材料",             [("1403","d",140000),  ("2202","c",140000)])
quick_v(2026, 6, 5,  "销售商品 - A客户",       [("1122","d",300000),  ("6001","c",270000), ("2221","c",30000)])
quick_v(2026, 6, 10, "销售商品 - D客户",       [("1122","d",240000),  ("6001","c",216000), ("2221","c",24000)])
quick_v(2026, 6, 15, "收到A客户货款",          [("1002","d",350000),  ("1122","c",350000)])
quick_v(2026, 6, 18, "收到C客户货款",          [("1002","d",260000),  ("1122","c",260000)])
quick_v(2026, 6, 20, "支付员工工资",           [("2211","d",88000),   ("1002","c",74000), ("2221","c",8500), ("2241","c",5500)])
quick_v(2026, 6, 25, "支付半年物业费",         [("6602","d",12000),   ("1002","c",12000)])
quick_v(2026, 6, 28, "计提6月折旧",            [("6602","d",2200),    ("1602","c",2200)])
quick_v(2026, 6, 30, "支付税款",               [("2221","d",52000),   ("1002","c",52000)])
quick_v(2026, 6, 30, "结转销售成本",           [("6401","d",170000),  ("1405","c",170000)])

# ── 2. 固定资产登记 ─────────────────────────────────────
print("   登记固定资产...")
conn = acc.get_conn()
conn.execute("INSERT OR REPLACE INTO fixed_assets (name, asset_account, deprec_account, original_value, residual_value, useful_life_months, depreciation_method, purchase_date, accumulated_deprec) VALUES (?,?,?,?,?,?,?,?,?)",
    ("办公电脑及设备", "1601", "1602", 80000, 8000, 60, "straight", "2026-01-06", 6000))
conn.execute("INSERT OR REPLACE INTO fixed_assets (name, asset_account, deprec_account, original_value, residual_value, useful_life_months, depreciation_method, purchase_date, accumulated_deprec) VALUES (?,?,?,?,?,?,?,?,?)",
    ("运输车辆", "1601", "1602", 120000, 12000, 96, "straight", "2026-03-25", 3375))
conn.commit()
conn.close()

# ── 3. 库存管理 ─────────────────────────────────────────
print("   登记库存...")
acc.add_product("P001", "电子芯片A型", "原材料", "个", 15.0)
acc.add_product("P002", "电子芯片B型", "原材料", "个", 25.0)
acc.add_product("P003", "智能传感器", "产成品", "台", 120.0, 10)
acc.add_product("P004", "数据采集模块", "产成品", "台", 85.0, 15)
acc.add_product("P005", "包装材料", "辅料", "套", 3.5)

# 入库记录
acc.inventory_in(1, 8000, 15.0, "2026年1月首批采购")
acc.inventory_in(2, 5000, 25.0, "2026年1月首批采购")
acc.inventory_in(1, 3000, 16.0, "2026年3月补货")
acc.inventory_in(2, 2500, 26.0, "2026年4月补货")
acc.inventory_in(3, 1500, 120.0, "2026年1月首产")
acc.inventory_in(4, 1200, 85.0, "2026年2月首产")
acc.inventory_in(5, 2000, 3.5, "2026年1月采购")

# 出库记录（产成品领用原材料）
acc.inventory_out(1, 6000, "2026年1月生产领用")
acc.inventory_out(2, 3500, "2026年2月生产领用")
acc.inventory_out(3, 800, "2026年1月销售出库")
acc.inventory_out(4, 500, "2026年2月销售出库")

# ── 4. 员工与薪资 ───────────────────────────────────────
print("   登记员工...")
acc.add_employee("EMP001", "张伟", "技术部", "高级工程师", 25000, 2500, 2000)
acc.add_employee("EMP002", "李娜", "销售部", "销售经理", 20000, 2000, 1600)
acc.add_employee("EMP003", "王磊", "财务部", "会计主管", 18000, 1800, 1500)
acc.add_employee("EMP004", "赵敏", "人事部", "HR经理", 16000, 1600, 1200)
acc.add_employee("EMP005", "陈强", "技术部", "工程师", 15000, 1500, 1000)
acc.add_employee("EMP006", "刘洋", "市场部", "市场专员", 12000, 1200, 800)
acc.add_employee("EMP007", "黄丽", "行政部", "行政专员", 10000, 1000, 700)

# 计算1-6月工资
for m in [1,2,3,4,5,6]:
    acc.calculate_payroll(2026, m)

# ── 5. 银行流水 ─────────────────────────────────────────
print("   导入银行流水...")
acc.import_bank_statement([
    {"transaction_date":"2026-01-05","description":"股东注资-张三","amount":1000000,"balance":1000000,"ref_no":"B001"},
    {"transaction_date":"2026-01-06","description":"购置办公设备","amount":-80000,"balance":920000,"ref_no":"B002"},
    {"transaction_date":"2026-01-08","description":"预付一季度房租","amount":-45000,"balance":875000,"ref_no":"B003"},
    {"transaction_date":"2026-01-20","description":"支付员工工资","amount":-72000,"balance":803000,"ref_no":"B004"},
    {"transaction_date":"2026-01-25","description":"收到A客户货款","amount":200000,"balance":1003000,"ref_no":"B005"},
    {"transaction_date":"2026-01-30","description":"支付电费","amount":-3200,"balance":999800,"ref_no":"B006"},
    {"transaction_date":"2026-02-02","description":"购入专利","amount":-50000,"balance":949800,"ref_no":"B007"},
    {"transaction_date":"2026-02-20","description":"支付员工工资","amount":-72000,"balance":877800,"ref_no":"B008"},
    {"transaction_date":"2026-02-22","description":"收到B客户货款","amount":250000,"balance":1127800,"ref_no":"B009"},
    {"transaction_date":"2026-02-28","description":"支付网络推广费","amount":-15000,"balance":1112800,"ref_no":"B010"},
    {"transaction_date":"2026-02-28","description":"支付供应商货款","amount":-80000,"balance":1032800,"ref_no":"B011"},
    {"transaction_date":"2026-03-15","description":"收到C客户货款","amount":150000,"balance":1182800,"ref_no":"B012"},
    {"transaction_date":"2026-03-20","description":"支付员工工资","amount":-72000,"balance":1110800,"ref_no":"B013"},
    {"transaction_date":"2026-03-25","description":"购入运输车辆","amount":-120000,"balance":990800,"ref_no":"B014"},
    {"transaction_date":"2026-03-30","description":"收到D客户50%货款","amount":90000,"balance":1080800,"ref_no":"B015"},
    {"transaction_date":"2026-04-01","description":"预付二季度房租","amount":-45000,"balance":1035800,"ref_no":"B016"},
    {"transaction_date":"2026-04-18","description":"收到A客户货款","amount":280000,"balance":1315800,"ref_no":"B017"},
    {"transaction_date":"2026-04-20","description":"支付员工工资","amount":-74000,"balance":1241800,"ref_no":"B018"},
    {"transaction_date":"2026-04-25","description":"支付税款","amount":-45000,"balance":1196800,"ref_no":"B019"},
    {"transaction_date":"2026-05-12","description":"收到E客户货款","amount":200000,"balance":1396800,"ref_no":"B020"},
    {"transaction_date":"2026-05-15","description":"收到B客户货款","amount":220000,"balance":1616800,"ref_no":"B021"},
    {"transaction_date":"2026-05-20","description":"支付员工工资","amount":-74000,"balance":1542800,"ref_no":"B022"},
    {"transaction_date":"2026-05-28","description":"支付供应商","amount":-100000,"balance":1442800,"ref_no":"B023"},
    {"transaction_date":"2026-06-15","description":"收到A客户货款","amount":350000,"balance":1792800,"ref_no":"B024"},
    {"transaction_date":"2026-06-18","description":"收到C客户货款","amount":260000,"balance":2052800,"ref_no":"B025"},
    {"transaction_date":"2026-06-20","description":"支付员工工资","amount":-74000,"balance":1978800,"ref_no":"B026"},
    {"transaction_date":"2026-06-25","description":"支付物业费","amount":-12000,"balance":1966800,"ref_no":"B027"},
    {"transaction_date":"2026-06-30","description":"支付税款","amount":-52000,"balance":1914800,"ref_no":"B028"},
])

# ── 6. 项目 ─────────────────────────────────────────────
print("   登记项目...")
acc.add_project("PRJ-001", "智能传感器V2研发", 300000, "2026-01-01", "2026-09-30")
acc.add_project("PRJ-002", "数据平台升级", 500000, "2026-03-01", "2026-12-31")
acc.add_project("PRJ-003", "办公系统改造", 80000, "2026-05-01", "2026-08-31")

# ── 7. ESG数据 ─────────────────────────────────────────
print("   录入ESG数据...")
esg_env = [("carbon","碳排放总量(tCO2e)","80","2026"), ("energy","能源消耗(MWh)","150","2026"),
           ("water","用水量(吨)","5000","2026"), ("waste","废弃物回收率","0.65","2026"),
           ("renewable","可再生能源占比","0.25","2026")]
esg_soc = [("employees","员工总数","7","2026"), ("female_ratio","女性员工占比","0.43","2026"),
           ("training","人均培训(小时)","32","2026"), ("safety","工伤事故","0","2026"),
           ("satisfaction","客户满意度","0.92","2026")]
esg_gov = [("board_size","董事会人数","5","2026"), ("independent","独董占比","0.4","2026"),
           ("compliance","合规事件","0","2026"), ("audit","外部审计","通过","2026"),
           ("privacy","数据安全事件","0","2026")]
for cat, items in [("environment",esg_env),("social",esg_soc),("governance",esg_gov)]:
    for code, name, val, yr in items:
        acc.upsert_esg_data(cat, code, name, str(val), int(yr))

print(f"\n 种子数据填充完成!")
print(f"   公司: {COMPANY}")
print(f"   凭证: 6个月 x 约10笔/月")
print(f"   固定资产: 2项")
print(f"   库存: 5种产品, 10笔出入库")
print(f"   员工: 7人, 6个月工资")
print(f"   银行流水: 28笔")
print(f"   项目: 3个")
print(f"    ESG: 15项指标")
print(f"\n   现在可以截图了!")
