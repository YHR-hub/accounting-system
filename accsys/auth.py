from __future__ import annotations

"""多用户与权限管理及主题系统模块。"""

import hashlib
import json
import os

from .database import get_conn
from .constants import THEMES, THEME_FILE


CURRENT_USER: dict = {"username": "管理员", "role": "admin", "display_name": "管理员"}
_current_theme: str = "light"


def init_users():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'viewer' CHECK(role IN ('admin','accountant','viewer')),
            display_name TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        conn.execute("INSERT INTO users (username, password_hash, role, display_name) VALUES (?,?,?,?)",
                     ("admin", hashlib.sha256("admin123".encode()).hexdigest(), "admin", "管理员"))
        conn.execute("INSERT INTO users (username, password_hash, role, display_name) VALUES (?,?,?,?)",
                     ("accountant", hashlib.sha256("acc123".encode()).hexdigest(), "accountant", "会计员"))
        conn.execute("INSERT INTO users (username, password_hash, role, display_name) VALUES (?,?,?,?)",
                     ("viewer", hashlib.sha256("view123".encode()).hexdigest(), "viewer", "查询员"))
    conn.commit()
    conn.close()


def login(username: str, password: str) -> dict:
    global CURRENT_USER
    h = hashlib.sha256(password.encode()).hexdigest()
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE username=? AND password_hash=? AND is_active=1",
                       (username, h)).fetchone()
    conn.close()
    if row:
        CURRENT_USER = {"username": row["username"], "role": row["role"], "display_name": row["display_name"]}
        return {"success": True, "user": CURRENT_USER}
    return {"success": False, "error": "用户名或密码错误"}


def logout():
    global CURRENT_USER
    CURRENT_USER = {"username": "管理员", "role": "admin", "display_name": "管理员"}


def require_role(*roles):
    return CURRENT_USER.get("role") in roles


def get_theme() -> dict:
    return THEMES[_current_theme]


def get_theme_mode() -> str:
    return _current_theme


def set_theme_mode(mode: str):
    global _current_theme
    if mode in THEMES:
        _current_theme = mode
        try:
            with open(THEME_FILE, 'w', encoding='utf-8') as f:
                json.dump({"mode": mode}, f)
        except Exception:
            pass


def load_theme():
    global _current_theme
    try:
        if os.path.exists(THEME_FILE):
            with open(THEME_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get("mode") in THEMES:
                    _current_theme = data["mode"]
    except Exception:
        pass
