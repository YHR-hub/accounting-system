from __future__ import annotations

"""ESG (Environmental, Social, Governance) reporting module."""

from datetime import datetime, date
from typing import Optional

import matplotlib.pyplot as plt

from .database import get_conn
from .constants import ESG_INDICATORS, ESG_SCORE_DIRECTION


ESG_TABLE_SQL = '''
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
)
'''


def init_esg_tables():
    conn = get_conn()
    conn.execute(ESG_TABLE_SQL)
    conn.commit()
    conn.close()


def get_esg_indicators(category: str = "") -> list:
    if category:
        cat = ESG_INDICATORS.get(category)
        return cat["metrics"] if cat else []
    result = []
    for cat_key in ESG_INDICATORS:
        result.extend(ESG_INDICATORS[cat_key]["metrics"])
    return result


def get_esg_categories() -> list:
    return list(ESG_INDICATORS.keys())


def upsert_esg_data(category: str, year: int, indicator: str, value: float,
                    month: int = 0, unit: str = "", note: str = "") -> bool:
    init_esg_tables()
    conn = get_conn()
    try:
        if not unit:
            for cat_key in ESG_INDICATORS:
                for m_key, m_label, m_unit, _ in ESG_INDICATORS[cat_key]["metrics"]:
                    if m_key == indicator:
                        unit = m_unit
                        break
        conn.execute(
            """INSERT OR REPLACE INTO esg_data (category, year, month, indicator, value, unit, note)
               VALUES (?,?,?,?,?,?,?)""",
            (category, year, month, indicator, value, unit, note))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"[ERR] upsert_esg_data: {e}")
        return False
    finally:
        conn.close()


def delete_esg_data(category: str, year: int, indicator: str, month: int = 0) -> bool:
    init_esg_tables()
    conn = get_conn()
    try:
        conn.execute(
            "DELETE FROM esg_data WHERE category=? AND year=? AND indicator=? AND month=?",
            (category, year, indicator, month))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


def get_esg_data(category: str = "", year: int = 0, indicator: str = "") -> list:
    init_esg_tables()
    conn = get_conn()
    conditions = []
    params = []
    if category:
        conditions.append("category=?")
        params.append(category)
    if year:
        conditions.append("year=?")
        params.append(year)
    if indicator:
        conditions.append("indicator=?")
        params.append(indicator)
    where = " AND ".join(conditions) if conditions else "1"
    rows = conn.execute(
        f"SELECT * FROM esg_data WHERE {where} ORDER BY year, category, indicator", params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_esg_data_map(category: str, year: int) -> dict:
    rows = get_esg_data(category, year)
    return {r["indicator"]: r["value"] for r in rows if r["month"] == 0}


def calc_esg_score_for_indicator(indicator: str, value: float, all_values: list) -> float:
    direction = ESG_SCORE_DIRECTION.get(indicator, True)
    if direction is None:
        return 70.0
    if len(all_values) < 2:
        return 50.0
    mn = min(all_values)
    mx = max(all_values)
    if mx == mn:
        return 50.0
    normalized = (value - mn) / (mx - mn) * 100
    return normalized if direction else 100 - normalized


def calc_esg_scores(year: int) -> dict:
    init_esg_tables()
    result = {"year": year, "categories": {}, "overall": 0.0, "rating": ""}
    conn = get_conn()
    all_rows = conn.execute(
        "SELECT indicator, value FROM esg_data WHERE month=0 ORDER BY year").fetchall()
    conn.close()
    historical = {}
    for r in all_rows:
        ind = r["indicator"]
        if ind not in historical:
            historical[ind] = []
        historical[ind].append(r["value"])
    total_weight = 0
    weighted_sum = 0
    for cat_key, cat_info in ESG_INDICATORS.items():
        data_map = get_esg_data_map(cat_key, year)
        scores = {}
        count = 0
        for ind_key, ind_label, ind_unit, ind_note in cat_info["metrics"]:
            if ind_key in data_map:
                all_vals = historical.get(ind_key, [data_map[ind_key]])
                score = calc_esg_score_for_indicator(ind_key, data_map[ind_key], all_vals)
                scores[ind_key] = {
                    "label": ind_label,
                    "value": data_map[ind_key],
                    "unit": ind_unit,
                    "score": round(score, 1),
                }
                count += 1
        cat_score = round(sum(s["score"] for s in scores.values()) / count, 1) if scores and count else 0
        result["categories"][cat_key] = {
            "label": cat_info["label"],
            "score": cat_score,
            "metrics": scores,
        }
        if cat_score > 0:
            weighted_sum += cat_score
            total_weight += 1
    result["overall"] = round(weighted_sum / total_weight, 1) if total_weight else 0
    avg = result["overall"]
    if avg >= 80:
        result["rating"] = "AAA (卓越)"
    elif avg >= 65:
        result["rating"] = "AA (优秀)"
    elif avg >= 50:
        result["rating"] = "A (良好)"
    elif avg >= 35:
        result["rating"] = "BBB (中等)"
    elif avg >= 20:
        result["rating"] = "BB (待提升)"
    else:
        result["rating"] = "B (需改善)"
    return result


def generate_esg_report(year: int) -> str:
    scores = calc_esg_scores(year)
    lines = []
    lines.append("=" * 60)
    lines.append(f"  ESG Ke Chi Xu Fa Zhan Bao Gao - {year} Nian Du")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Zong He ESG Ping Fen: {scores['overall']} | Ping Ji: {scores['rating']}")
    lines.append("")
    for cat_key in ["environment", "social", "governance"]:
        cat = scores["categories"].get(cat_key)
        if not cat or not cat["metrics"]:
            continue
        lines.append(f"-- {cat['label']} -- Ping Fen: {cat['score']}")
        for ind_key, info in cat["metrics"].items():
            bar_len = int(info["score"] / 5)
            bar = "#" * bar_len + "-" * (20 - bar_len)
            lines.append(f"  {info['label']:12s} {info['value']:>10.2f} {info['unit']:8s} "
                         f"{info['score']:5.1f} Fen [{bar}]")
        lines.append("")
    lines.append("=" * 60)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lines.append(f"Bao Gao Sheng Cheng Shi Jian: {now_str}")
    lines.append("=" * 60)
    return "\n".join(lines)


def export_esg_report_to_file(year: int, filepath: str) -> dict:
    try:
        report = generate_esg_report(year)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        return {"message": f"ESG报告已导出到 {filepath}"}
    except Exception as e:
        return {"error": f"导出失败: {e}"}


def chart_esg_radar(year: int) -> plt.Figure:
    scores = calc_esg_scores(year)
    categories = ["环境(E)", "社会(S)", "治理(G)"]
    cat_keys = ["environment", "social", "governance"]
    values = [scores["categories"].get(k, {}).get("score", 0) for k in cat_keys]
    angles = [n / 3 * 2 * 3.14159 for n in range(3)]
    angles += angles[:1]
    values += values[:1]
    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw={'projection': 'polar'})
    ax.plot(angles, values, 'o-', color='#2E7D32', linewidth=2, markersize=8)
    ax.fill(angles, values, alpha=0.25, color='#2E7D32')
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=12)
    ax.set_ylim(0, 100)
    ax.set_title(f'{year}年 ESG评分 ({scores["overall"]})', fontsize=14, pad=20)
    for a, v, label in zip(angles[:-1], values[:-1], categories):
        ax.annotate(f'{v:.1f}', (a, v), textcoords="offset points",
                    xytext=(0, 10), ha='center', fontsize=10, fontweight='bold')
    fig.tight_layout()
    return fig


def chart_esg_trend(years: Optional[list] = None) -> plt.Figure:
    if years is None:
        conn = get_conn()
        rows = conn.execute("SELECT DISTINCT year FROM esg_data ORDER BY year").fetchall()
        conn.close()
        years = [r['year'] for r in rows] if rows else [date.today().year]
        if len(years) < 2 and years:
            years = [years[0] - 1, years[0]]
    fig, ax = plt.subplots(figsize=(10, 5))
    cat_config = [
        ("environment", "环境(E)", '#2E7D32'),
        ("social", "社会(S)", '#1565C0'),
        ("governance", "治理(G)", '#FF8F00'),
        ("overall", "综合ESG", '#C62828'),
    ]
    valid_years = []
    for key, label, color in cat_config:
        vals = []
        vy = []
        for y in years:
            if key == "overall":
                s = calc_esg_scores(y)
                v = s["overall"]
            else:
                s = calc_esg_scores(y)
                v = s["categories"].get(key, {}).get("score", 0)
            if v > 0:
                vals.append(v)
                vy.append(y)
        if len(vals) > 0:
            marker = 'o' if key != "overall" else 's'
            ax.plot(vy, vals, f'{marker}-', label=label, color=color, linewidth=2)
            valid_years = vy
    if valid_years:
        ax.set_xticks(valid_years)
    ax.set_title('ESG 历年评分趋势', fontsize=14)
    ax.set_xlabel('年份')
    ax.set_ylabel('评分')
    ax.set_ylim(0, 100)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig
