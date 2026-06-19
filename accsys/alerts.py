from __future__ import annotations

"""财务预警模块。"""

from .database import get_conn
from .reports import calc_financial_ratios


DEFAULT_ALERT_RULES = [
    ("流动比率过低", "current_ratio", "lt", 1.5, "warning"),
    ("资产负债率过高", "debt_ratio", "gt", 0.7, "critical"),
    ("净利润率为负", "net_profit_margin", "lt", 0, "critical"),
    ("速动比率过低", "quick_ratio", "lt", 1.0, "warning"),
    ("毛利率过低", "gross_margin", "lt", 0.15, "warning"),
]


def init_alert_rules():
    conn = get_conn()
    if conn.execute("SELECT COUNT(*) FROM alert_rules").fetchone()[0] == 0:
        for name, indicator, op, threshold, level in DEFAULT_ALERT_RULES:
            conn.execute("INSERT INTO alert_rules (name, indicator, operator, threshold, level) VALUES (?,?,?,?,?)",
                        (name, indicator, op, threshold, level))
        conn.commit()
    conn.close()


def add_alert_rule(name: str, indicator: str, operator: str, threshold: float, level: str = "warning") -> dict:
    conn = get_conn()
    try:
        conn.execute("INSERT INTO alert_rules (name, indicator, operator, threshold, level) VALUES (?,?,?,?,?)",
                    (name, indicator, operator, threshold, level))
        conn.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def update_alert_rule(rule_id: int, **kwargs):
    conn = get_conn()
    fields = {k: v for k, v in kwargs.items() if k in ("name","indicator","operator","threshold","enabled","level")}
    if not fields:
        conn.close()
        return
    sets = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [rule_id]
    conn.execute(f"UPDATE alert_rules SET {sets} WHERE id=?", vals)
    conn.commit()
    conn.close()


def get_alert_rules() -> list:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM alert_rules ORDER BY level, name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _calc_indicator(indicator: str) -> float:
    ratios = calc_financial_ratios()
    mapping = {
        "current_ratio": "current_ratio",
        "quick_ratio": "quick_ratio",
        "debt_ratio": "debt_ratio",
        "net_profit_margin": "net_margin",
        "gross_margin": "gross_margin",
        "roe": "roe",
        "roa": "roa",
        "inventory_turnover": "inventory_turnover",
        "receivable_turnover": "receivable_turnover",
    }
    key = mapping.get(indicator)
    if key and key in ratios:
        return float(ratios[key])
    return -1


def check_alerts() -> list:
    results = []
    conn = get_conn()
    rules = conn.execute("SELECT * FROM alert_rules WHERE enabled=1").fetchall()
    for rule in rules:
        value = _calc_indicator(rule["indicator"])
        if value < 0:
            continue
        triggered = False
        if rule["operator"] == "gt" and value > rule["threshold"]:
            triggered = True
        elif rule["operator"] == "lt" and value < rule["threshold"]:
            triggered = True
        elif rule["operator"] == "gte" and value >= rule["threshold"]:
            triggered = True
        elif rule["operator"] == "lte" and value <= rule["threshold"]:
            triggered = True
        elif rule["operator"] == "eq" and abs(value - rule["threshold"]) < 0.001:
            triggered = True
        if triggered:
            msg = f"{rule['name']}: {value:.4f} (阈值: {rule['threshold']})"
            conn.execute("INSERT INTO alert_history (rule_id, message, level) VALUES (?,?,?)",
                        (rule["id"], msg, rule["level"]))
            results.append({"rule": rule["name"], "message": msg, "level": rule["level"], "value": value})
    conn.commit()
    conn.close()
    return results


def get_alert_history(limit: int = 100, unresolved_only: bool = False) -> list:
    conn = get_conn()
    if unresolved_only:
        rows = conn.execute("SELECT h.*, r.name as rule_name FROM alert_history h LEFT JOIN alert_rules r ON h.rule_id=r.id WHERE h.resolved=0 ORDER BY h.id DESC LIMIT ?",
                           (limit,)).fetchall()
    else:
        rows = conn.execute("SELECT h.*, r.name as rule_name FROM alert_history h LEFT JOIN alert_rules r ON h.rule_id=r.id ORDER BY h.id DESC LIMIT ?",
                           (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def resolve_alert(alert_id: int):
    conn = get_conn()
    conn.execute("UPDATE alert_history SET resolved=1 WHERE id=?", (alert_id,))
    conn.commit()
    conn.close()
