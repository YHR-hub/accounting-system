"""数据可视化与BI仪表盘模块"""
from __future__ import annotations
import io
import base64
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import date
from typing import Optional
from decimal import Decimal
from .database import get_conn
from .accounts import load_accounts_from_db, calc_balances
from .reports import calc_financial_ratios, get_trend_data

_CHINESE_FONT = None
for fname in fm.findSystemFonts():
    if any(k in fname.lower() for k in ('msyh', 'simsun', 'simhei', 'yahei', 'noto', 'wenquanyi')):
        _CHINESE_FONT = fname
        break
if _CHINESE_FONT:
    plt.rcParams['font.family'] = fm.FontProperties(fname=_CHINESE_FONT).get_name()
plt.rcParams['axes.unicode_minus'] = False


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def chart_income_expense(year: int) -> plt.Figure:
    """Monthly income vs expense bar chart."""
    conn = get_conn()
    data = []
    for m in range(1, 13):
        rev = conn.execute(
            "SELECT COALESCE(SUM(je.credit),0) FROM vouchers v "
            "JOIN journal_entries je ON v.id=je.voucher_id "
            "JOIN accounts a ON je.account_code=a.code "
            "WHERE v.fiscal_year=? AND v.fiscal_month=? AND a.category='income'",
            (year, m)).fetchone()[0] or 0
        exp = conn.execute(
            "SELECT COALESCE(SUM(je.debit),0) FROM vouchers v "
            "JOIN journal_entries je ON v.id=je.voucher_id "
            "JOIN accounts a ON je.account_code=a.code "
            "WHERE v.fiscal_year=? AND v.fiscal_month=? AND a.category='expense'",
            (year, m)).fetchone()[0] or 0
        data.append((m, float(rev), float(exp)))
    conn.close()

    fig, ax = plt.subplots(figsize=(10, 5))
    months = [f'{m}月' for m in range(1, 13)]
    revs = [d[1] for d in data]
    exps = [d[2] for d in data]
    x = range(len(months))
    width = 0.35
    bars1 = ax.bar([i - width/2 for i in x], revs, width, label='收入', color='#2E7D32')
    bars2 = ax.bar([i + width/2 for i in x], exps, width, label='支出', color='#C62828')
    ax.set_title(f'{year}年 月度收入与支出', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(months, fontsize=9)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()
    return fig


def chart_balance_pie() -> plt.Figure:
    """Asset / Liability / Equity pie chart."""
    accounts = load_accounts_from_db()
    balances = calc_balances(accounts)
    cats = {'资产': 0, '负债': 0, '所有者权益': 0}
    for a in accounts:
        bal = float(balances.get(a['code'], Decimal('0')))
        if a['category'] == 'asset':
            cats['资产'] += bal
        elif a['category'] == 'liability':
            cats['负债'] += bal
        elif a['category'] == 'equity':
            cats['所有者权益'] += bal

    fig, ax = plt.subplots(figsize=(6, 5))
    colors = ['#2E7D32', '#C62828', '#1565C0']
    wedges, texts, autotexts = ax.pie(
        [max(0, v) for v in cats.values()],
        labels=cats.keys(), autopct='%1.1f%%', colors=colors,
        startangle=90, textprops={'fontsize': 12})
    ax.set_title('资产负债构成', fontsize=14)
    fig.tight_layout()
    return fig


def chart_trend_line(months: int = 12) -> plt.Figure:
    """Revenue/Expense/Profit trend line chart."""
    trend = get_trend_data(months)
    fig, ax = plt.subplots(figsize=(10, 5))
    labels = trend['labels']
    ax.plot(labels, trend['revenue'], 'o-', label='收入', color='#2E7D32', linewidth=2)
    ax.plot(labels, trend['expense'], 's-', label='支出', color='#C62828', linewidth=2)
    ax.plot(labels, trend['profit'], '^-', label='净利润', color='#1565C0', linewidth=2)
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax.set_title('财务趋势分析', fontsize=14)
    ax.set_xticklabels(labels, rotation=45, fontsize=9)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def chart_ratio_radar() -> plt.Figure:
    """Radar chart of financial ratios."""
    ratios = calc_financial_ratios()
    keys = ['流动比率', '速动比率', '毛利率', '净利率', '净资产收益率(ROE)', '总资产报酬率(ROA)']
    max_vals = {'流动比率': 5, '速动比率': 3, '毛利率': 100, '净利率': 100,
                '净资产收益率(ROE)': 50, '总资产报酬率(ROA)': 50}
    values = []
    for k in keys:
        raw = ratios.get(k, 0)
        maximum = max_vals.get(k, 100)
        values.append(min(raw / maximum, 1.0))

    angles = [n / len(keys) * 2 * 3.14159 for n in range(len(keys))]
    angles += angles[:1]
    values += values[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'projection': 'polar'})
    ax.plot(angles, values, 'o-', color='#1565C0', linewidth=2)
    ax.fill(angles, values, alpha=0.25, color='#1565C0')
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(keys, fontsize=9)
    ax.set_ylim(0, 1.2)
    ax.set_title('财务指标雷达图', fontsize=14, pad=20)
    fig.tight_layout()
    return fig


def chart_dashboard(year: Optional[int] = None) -> plt.Figure:
    """Combined dashboard with key metrics."""
    if year is None:
        year = date.today().year
    ratios = calc_financial_ratios()
    conn = get_conn()

    total_v = conn.execute("SELECT COUNT(*) FROM vouchers WHERE fiscal_year=?", (year,)).fetchone()[0]
    total_je = conn.execute(
        "SELECT COUNT(*) FROM journal_entries je "
        "JOIN vouchers v ON je.voucher_id=v.id WHERE v.fiscal_year=?", (year,)).fetchone()[0]
    conn.close()

    fig, axes = plt.subplots(2, 3, figsize=(12, 7))
    fig.suptitle(f'{year}年 商业智能仪表盘', fontsize=16, fontweight='bold')

    ax = axes[0, 0]
    ax.axis('off')
    metrics = [
        f"凭证数: {total_v}",
        f"分录数: {total_je}",
        f"流动比率: {ratios.get('流动比率', 0):.2f}",
        f"资产负债率: {ratios.get('资产负债率', 0):.1f}%",
        f"净利率: {ratios.get('净利率', 0):.1f}%",
        f"ROE: {ratios.get('净资产收益率(ROE)', 0):.1f}%",
    ]
    ax.text(0.1, 0.9, '\n'.join(metrics), transform=ax.transAxes,
            fontsize=11, verticalalignment='top', fontfamily='monospace')

    ax = axes[0, 1]
    income = sum(ratios.get(k, 0) for k in [] if False)
    conn2 = get_conn()
    rev = sum(
        conn2.execute(
            "SELECT COALESCE(SUM(je.credit),0) FROM vouchers v "
            "JOIN journal_entries je ON v.id=je.voucher_id "
            "JOIN accounts a ON je.account_code=a.code "
            "WHERE v.fiscal_year=? AND a.category='income'", (year,)).fetchone()[0] or 0
        for _ in [1])
    exp = sum(
        conn2.execute(
            "SELECT COALESCE(SUM(je.debit),0) FROM vouchers v "
            "JOIN journal_entries je ON v.id=je.voucher_id "
            "JOIN accounts a ON je.account_code=a.code "
            "WHERE v.fiscal_year=? AND a.category='expense'", (year,)).fetchone()[0] or 0
        for _ in [1])
    conn2.close()
    rev, exp = float(rev), float(exp)
    ax.bar(['收入', '支出'], [rev, exp], color=['#2E7D32', '#C62828'])
    ax.set_title('年度汇总', fontsize=11)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/10000:.0f}w'))

    ax = axes[0, 2]
    accounts = load_accounts_from_db()
    balances = calc_balances(accounts)
    cats = {'资产': 0, '负债': 0, '权益': 0}
    for a in accounts:
        bal = float(balances.get(a['code'], Decimal('0')))
        if a['category'] == 'asset':
            cats['资产'] += bal
        elif a['category'] == 'liability':
            cats['负债'] += bal
        elif a['category'] == 'equity':
            cats['权益'] += bal
    vals = [max(0, v) for v in cats.values()]
    if sum(vals) > 0:
        ax.pie(vals, labels=cats.keys(), autopct='%1.0f%%',
               colors=['#2E7D32', '#C62828', '#1565C0'])
    ax.set_title('资产负债结构', fontsize=11)

    ax = axes[1, 0]
    trend = get_trend_data(6)
    ax.plot(trend['labels'], trend['revenue'], 'g-', label='收入')
    ax.plot(trend['labels'], trend['expense'], 'r-', label='支出')
    ax.set_title('6月趋势', fontsize=11)
    ax.tick_params(axis='x', labelsize=7)
    ax.legend(fontsize=8)

    ax = axes[1, 1]
    keys = ['流动比率', '速动比率', '毛利率', '净利率', 'ROE', 'ROA']
    max_v = [5, 3, 100, 100, 50, 50]
    vals_radar = []
    for i, k in enumerate(keys):
        raw = ratios.get(k, 0)
        vals_radar.append(min(raw / max_v[i], 1.0))
    angles = [n / len(keys) * 2 * 3.14159 for n in range(len(keys))] + [0]
    vals_radar += vals_radar[:1]
    ax.remove()
    ax = fig.add_subplot(2, 3, 5, projection='polar')
    ax.plot(angles, vals_radar, 'b-')
    ax.fill(angles, vals_radar, alpha=0.2)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([k[:2] for k in keys], fontsize=7)
    ax.set_title('指标雷达', fontsize=11)

    ax = axes[1, 2]
    ax.axis('off')
    status = '✅ 财务状况良好' if ratios.get('流动比率', 0) > 1.5 else '⚠️ 需要关注流动性'
    ax.text(0.1, 0.8, f"综合评估:\n{status}\n\n收入: {rev:,.0f}\n支出: {exp:,.0f}\n利润: {rev-exp:,.0f}",
            transform=ax.transAxes, fontsize=11, verticalalignment='top')

    for ax_row in axes:
        for ax in ax_row:
            try:
                ax.tick_params(labelsize=8)
            except Exception:
                pass

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    return fig
