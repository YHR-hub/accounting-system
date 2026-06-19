from __future__ import annotations

"""文件附件管理模块。"""

import os
import shutil
import time

from .audit import log_action
from .auth import CURRENT_USER
from .constants import ATTACHMENT_DIR
from .database import get_conn


def init_attachment_dir():
    os.makedirs(ATTACHMENT_DIR, exist_ok=True)


def attach_file(voucher_id: int, source_path: str) -> dict:
    if not os.path.exists(source_path):
        return {"success": False, "error": "文件不存在"}
    try:
        os.makedirs(ATTACHMENT_DIR, exist_ok=True)
        fname = os.path.basename(source_path)
        dest = os.path.join(ATTACHMENT_DIR, f"{voucher_id}_{int(time.time())}_{fname}")
        shutil.copy2(source_path, dest)
        fsize = os.path.getsize(dest)
        conn = get_conn()
        conn.execute("INSERT INTO attachments (voucher_id, filename, filepath, file_size, file_type) VALUES (?,?,?,?,?)",
                    (voucher_id, fname, dest, fsize, os.path.splitext(fname)[1].lower()))
        conn.commit()
        conn.close()
        log_action(CURRENT_USER.get("username","system"), "attach", "voucher", str(voucher_id), fname)
        return {"success": True, "filepath": dest}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_attachments(voucher_id: int = 0) -> list:
    conn = get_conn()
    if voucher_id:
        rows = conn.execute("SELECT * FROM attachments WHERE voucher_id=? ORDER BY created_at DESC", (voucher_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM attachments ORDER BY created_at DESC LIMIT 100").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_attachment(att_id: int) -> bool:
    conn = get_conn()
    row = conn.execute("SELECT * FROM attachments WHERE id=?", (att_id,)).fetchone()
    if row and os.path.exists(row["filepath"]):
        os.remove(row["filepath"])
    conn.execute("DELETE FROM attachments WHERE id=?", (att_id,))
    conn.commit()
    conn.close()
    return True
