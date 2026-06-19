"""
Flask Web 版 - 基于 accsys 包，复用全部后端逻辑。
运行: python webapp.py    然后打开 http://localhost:5000
"""
from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify
import accsys as acc

app = Flask(__name__)

# ── 页面框架 ────────────────────────────────────────
STYLE = """
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Microsoft YaHei','PingFang SC',sans-serif;background:#f5f6fa;color:#2d3436}
nav{background:#6c5ce7;padding:12px 24px;display:flex;gap:24px;align-items:center}
nav a{color:#dfe6e9;text-decoration:none;font-size:14px}
nav a:hover{color:#fff}
main{max-width:1240px;margin:0 auto;padding:20px}
.card{background:#fff;border-radius:8px;padding:20px;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,.06)}
h1{font-size:22px;margin-bottom:16px;color:#6c5ce7}
h2{font-size:16px;margin-bottom:10px;color:#5a4bd1}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:8px 12px;text-align:left;border-bottom:1px solid #eee}
th{background:#f8f9fa;font-weight:600;color:#636e72}
tr:hover{background:#f8f9fa}
.tag{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600}
.tg{background:#d4edda;color:#155724}.tr{background:#f8d7da;color:#721c24}.tb{background:#d6e4f0;color:#0c5460}
.row{display:flex;gap:16px;flex-wrap:wrap}
.col{flex:1;min-width:300px}
input,select,button{padding:8px 12px;border:1px solid #ddd;border-radius:4px;font-size:14px}
button{background:#6c5ce7;color:#fff;border:none;cursor:pointer}
button:hover{background:#5a4bd1}
.mono{font-family:'Consolas','Courier New',monospace;text-align:right!important}
.big{font-size:28px;font-weight:bold;margin:8px 0}
.purple{color:#6c5ce7}.red{color:#d63031}.green{color:#00b894}.yellow{color:#fdcb6e}
</style>
"""

def page(title: str, body: str) -> str:
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{title}</title>{STYLE}</head><body>
<nav><b style="font-size:16px;color:#fff">会计系统 Web 版</b>
<a href="/">仪表盘</a><a href="/vouchers">凭证</a><a href="/accounts">科目</a><a href="/reports">报表</a></nav>
<main>{body}</main></body></html>"""


# ── 仪表盘 ──────────────────────────────────────────
@app.route("/")
def index():
    acc.init_db()
    acc.ensure_accounts()
    ratios = acc.calc_financial_ratios()
    accts = acc.load_accounts_from_db()
    balances = acc.calc_balances(accts)
    vouchers = _list_vouchers(2026, 0)
    alerts = acc.check_alerts() or []
    total_assets = sum(float(balances.get(a["code"], 0)) for a in accts if a["category"] == "asset")
    total_liab = sum(float(balances.get(a["code"], 0)) for a in accts if a["category"] == "liability")
    equity = total_assets - total_liab

    # KPI cards
    cards = f"""<div class="row">
<div class="col card"><h2>总资产</h2><p class="big purple">{total_assets:,.0f}</p></div>
<div class="col card"><h2>总负债</h2><p class="big red">{total_liab:,.0f}</p></div>
<div class="col card"><h2>净资产</h2><p class="big green">{equity:,.0f}</p></div>
<div class="col card"><h2>凭证数 / 预警</h2><p class="big">{len(vouchers)} <span class="yellow" style="font-size:18px">/ {len(alerts)}</span></p></div>
</div>"""

    # Ratio table
    ratio_rows = "".join(f'<tr><td>{k}</td><td class="mono">{v:.2f}</td></tr>' for k,v in ratios.items())
    ratio_card = f'<div class="col card"><h2>财务比率</h2><table><tr><th>指标</th><th>值</th></tr>{ratio_rows}</table></div>'

    # Alerts
    if alerts:
        alert_items = "".join(
            f"<p><span class='tag tr'>{a['rule']}</span> {a['message']}</p>" for a in alerts
        )
        alert_html = f'<div class="col card"><h2>预警 ({len(alerts)})</h2>{alert_items}</div>'
    else:
        alert_html = '<div class="col card"><h2>预警</h2><p style="color:#636e72">正常</p></div>'

    body = f"<h1>星辰科技有限公司 - 财务仪表盘</h1>{cards}<div class='row'>{ratio_card}{alert_html}</div>"
    return page("仪表盘", body)


# ── 凭证列表 ────────────────────────────────────────
def _list_vouchers(year: int, month: int = 0):
    conn = acc.get_conn()
    if month > 0:
        rows = conn.execute(
            "SELECT v.*, COUNT(je.id) as entry_count, COALESCE(SUM(je.debit),0) as total"
            " FROM vouchers v LEFT JOIN journal_entries je ON v.id=je.voucher_id"
            " WHERE v.fiscal_year=? AND v.fiscal_month=? GROUP BY v.id ORDER BY v.id DESC",
            (year, month)).fetchall()
    else:
        rows = conn.execute(
            "SELECT v.*, COUNT(je.id) as entry_count, COALESCE(SUM(je.debit),0) as total"
            " FROM vouchers v LEFT JOIN journal_entries je ON v.id=je.voucher_id"
            " WHERE v.fiscal_year=? GROUP BY v.id ORDER BY v.id DESC",
            (year,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.route("/vouchers")
def vouchers():
    year = int(request.args.get("year", 2026))
    month = int(request.args.get("month", 0))
    rows = _list_vouchers(year, month)
    row_html = "".join(
        f'<tr><td>{r["voucher_no"]}</td><td>{r["date"]}</td><td>{r["summary"]}</td><td class="mono">{r["total"]:,.2f}</td></tr>'
        for r in rows)
    body = f"""<h1>凭证列表</h1>
<form style="margin-bottom:16px"><input name="year" value="{year}" style="width:100px;display:inline" placeholder="年份">
<input name="month" value="{month}" style="width:80px;display:inline" placeholder="月(0=全年)">
<button>查询</button></form>
<table><tr><th>凭证号</th><th>日期</th><th>摘要</th><th>金额</th></tr>{row_html}</table>"""
    return page("凭证管理", body)


# ── 科目余额 ────────────────────────────────────────
def _movements():
    """返回 {account_code: (借方发生额, 贷方发生额)}。"""
    conn = acc.get_conn()
    rows = conn.execute(
        "SELECT account_code, COALESCE(SUM(debit),0) d, COALESCE(SUM(credit),0) c"
        " FROM journal_entries GROUP BY account_code"
    ).fetchall()
    conn.close()
    return {r["account_code"]: (float(r["d"]), float(r["c"])) for r in rows}


@app.route("/accounts")
def accounts():
    accts = acc.load_accounts_from_db()
    balances = acc.calc_balances(accts)
    mv = _movements()
    cat_map = {"asset":"资产","liability":"负债","equity":"权益","income":"收入","expense":"费用"}
    rows = []
    for a in accts:
        dt, ct = mv.get(a["code"], (0.0, 0.0))
        rows.append((a["code"], a["name"], a["category"],
                     dt, ct, float(balances.get(a["code"], 0))))
    row_html = "".join(
        f'<tr><td>{c}</td><td>{n}</td><td><span class="tag tb">{cat_map.get(cat,cat)}</span></td>'
        f'<td class="mono">{dt:,.2f}</td><td class="mono">{ct:,.2f}</td><td class="mono">{bal:,.2f}</td></tr>'
        for c,n,cat,dt,ct,bal in rows)
    body = f"""<h1>科目余额表</h1>
<table><tr><th>编码</th><th>名称</th><th>类别</th><th>借方发生</th><th>贷方发生</th><th>期末余额</th></tr>{row_html}</table>"""
    return page("科目余额", body)


# ── 报表 ───────────────────────────────────────────
@app.route("/reports")
def reports():
    bs = acc.balance_sheet_data()
    inc = acc.income_statement_data()
    cf = acc.cash_flow_statement_data()

    def tbl(rows):
        return "".join(f'<tr><td>{r["label"]}</td><td class="mono">{r["amount"]:,.2f}</td></tr>' for r in rows)

    body = f"""<h1>财务报表</h1>
<div class="row"><div class="col card"><h2>资产负债表</h2><table><tr><th>项目</th><th>金额</th></tr>{tbl(bs)}</table></div>
<div class="col card"><h2>利润表</h2><table><tr><th>项目</th><th>金额</th></tr>{tbl(inc)}</table></div></div>
<div class="card"><h2>现金流量表 (间接法)</h2><table><tr><th>项目</th><th>金额</th></tr>{tbl(cf)}</table></div>"""
    return page("财务报表", body)


# ── API ────────────────────────────────────────────
@app.route("/api/ratios")
def api_ratios():
    return jsonify(acc.calc_financial_ratios())

@app.route("/api/vouchers")
def api_vouchers():
    year = int(request.args.get("year", 2026))
    month = int(request.args.get("month", 0))
    return jsonify(_list_vouchers(year, month))

@app.route("/api/accounts")
def api_accounts():
    accts = acc.load_accounts_from_db()
    balances = acc.calc_balances(accts)
    mv = _movements()
    result = []
    for a in accts:
        dt, ct = mv.get(a["code"], (0.0, 0.0))
        result.append({
            "code": a["code"], "name": a["name"], "category": a["category"],
            "debit": dt, "credit": ct,
            "balance": float(balances.get(a["code"], 0))
        })
    return jsonify(result)

@app.route("/api/reports/balance")
def api_balance():
    return jsonify(acc.balance_sheet_data())

@app.route("/api/reports/income")
def api_income():
    return jsonify(acc.income_statement_data())

@app.route("/api/reports/cashflow")
def api_cashflow():
    return jsonify(acc.cash_flow_statement_data())


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
