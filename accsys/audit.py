from __future__ import annotations

"""审计轨迹模块。"""

from .database import get_conn


def log_action(username: str, action: str, target_type: str = "", target_id: str = "", detail: str = ""):
    conn = get_conn()
    conn.execute("INSERT INTO audit_log (username, action, target_type, target_id, detail) VALUES (?,?,?,?,?)",
                 (username, action, target_type, target_id, detail))
    conn.commit()
    conn.close()


def get_audit_logs(limit: int = 200, target_type: str = "") -> list:
    conn = get_conn()
    if target_type:
        rows = conn.execute("SELECT * FROM audit_log WHERE target_type=? ORDER BY id DESC LIMIT ?",
                           (target_type, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
