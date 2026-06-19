from __future__ import annotations

"""数据备份与恢复模块。"""

import os
import shutil

from .audit import log_action
from .auth import CURRENT_USER
from .database import get_db_path


def backup_database(backup_path: str) -> dict:
    try:
        src = get_db_path()
        shutil.copy2(src, backup_path)
        log_action(CURRENT_USER.get("username","system"), "backup", "database", "", f"备份到 {backup_path}")
        return {"success": True, "path": backup_path}
    except Exception as e:
        return {"success": False, "error": str(e)}


def restore_database(backup_path: str) -> dict:
    if not os.path.exists(backup_path):
        return {"success": False, "error": "备份文件不存在"}
    try:
        dst = get_db_path()
        shutil.copy2(backup_path, dst)
        log_action(CURRENT_USER.get("username","system"), "restore", "database", "", f"从 {backup_path} 恢复")
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
