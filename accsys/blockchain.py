"""区块链分布式账本模块"""
from __future__ import annotations
import hashlib
import json as json_mod
from datetime import datetime
from typing import Optional
from .database import get_conn

BLOCKCHAIN_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS blockchain (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    index_no INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    previous_hash TEXT NOT NULL DEFAULT '',
    hash TEXT NOT NULL,
    nonce INTEGER NOT NULL DEFAULT 0,
    data TEXT NOT NULL DEFAULT '{}',
    voucher_id INTEGER,
    voucher_no TEXT,
    UNIQUE(index_no)
)
'''


def _sha256(data_str: str) -> str:
    return hashlib.sha256(data_str.encode('utf-8')).hexdigest()


def _block_to_string(idx: int, timestamp: str, prev_hash: str, data_str: str, nonce: int) -> str:
    return f"{idx}{timestamp}{prev_hash}{data_str}{nonce}"


def init_blockchain():
    """Create blockchain table and genesis block if empty."""
    conn = get_conn()
    conn.execute(BLOCKCHAIN_TABLE_SQL)
    existing = conn.execute("SELECT COUNT(*) FROM blockchain").fetchone()[0]
    if existing == 0:
        genesis_data = json_mod.dumps({"type": "genesis", "note": "会计系统区块链账本创始区块"})
        timestamp = datetime.now().isoformat()
        nonce = 0
        raw = _block_to_string(0, timestamp, '0' * 64, genesis_data, nonce)
        g_hash = _sha256(raw)
        conn.execute(
            "INSERT INTO blockchain (index_no, timestamp, previous_hash, hash, nonce, data) "
            "VALUES (?,?,?,?,?,?)",
            (0, timestamp, '0' * 64, g_hash, nonce, genesis_data))
        conn.commit()
    conn.close()


def get_chain_length() -> int:
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) FROM blockchain").fetchone()[0]
    conn.close()
    return row


def get_block_by_index(idx: int) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM blockchain WHERE index_no=?", (idx,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_chain(limit: int = 100, offset: int = 0) -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM blockchain ORDER BY index_no DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _mine_block(idx: int, timestamp: str, prev_hash: str, data_str: str, difficulty: int = 2) -> tuple:
    """Simple proof-of-work mining."""
    nonce = 0
    prefix = '0' * difficulty
    while True:
        raw = _block_to_string(idx, timestamp, prev_hash, data_str, nonce)
        h = _sha256(raw)
        if h.startswith(prefix):
            return h, nonce
        nonce += 1
        if nonce > 1000000:
            raise Exception("Mining failed: exceeded max nonce")


def add_voucher_to_chain(v_id: Optional[int] = None, v_no: Optional[str] = None) -> bool:
    """Add a voucher as a block to the blockchain."""
    conn = get_conn()
    try:
        if v_id:
            row = conn.execute(
                "SELECT * FROM vouchers WHERE id=?", (v_id,)).fetchone()
        elif v_no:
            row = conn.execute(
                "SELECT * FROM vouchers WHERE voucher_no=?", (v_no,)).fetchone()
        else:
            return False

        if not row:
            return False

        voucher_data = {
            "id": row['id'],
            "voucher_no": row['voucher_no'],
            "date": row['date'],
            "summary": row['summary'],
            "fiscal_year": row['fiscal_year'],
            "fiscal_month": row['fiscal_month'],
        }

        last = conn.execute("SELECT * FROM blockchain ORDER BY index_no DESC LIMIT 1").fetchone()
        prev_hash = last['hash'] if last else '0' * 64
        new_idx = (last['index_no'] + 1) if last else 0

        timestamp = datetime.now().isoformat()
        data_str = json_mod.dumps(voucher_data, ensure_ascii=False)

        if new_idx == 0:
            h = _sha256(_block_to_string(0, timestamp, prev_hash, data_str, 0))
            nonce = 0
        else:
            h, nonce = _mine_block(new_idx, timestamp, prev_hash, data_str)

        conn.execute(
            "INSERT INTO blockchain (index_no, timestamp, previous_hash, hash, nonce, data, voucher_id, voucher_no) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (new_idx, timestamp, prev_hash, h, nonce, data_str, row['id'], row['voucher_no']))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"[ERR] add_voucher_to_chain: {e}")
        return False
    finally:
        conn.close()


def add_all_vouchers_to_chain() -> dict:
    """Hash all existing vouchers not yet in blockchain."""
    conn = get_conn()
    existing_vids = set(
        r['voucher_id'] for r in conn.execute(
            "SELECT voucher_id FROM blockchain WHERE voucher_id IS NOT NULL").fetchall()
        if r['voucher_id'])
    all_vouchers = conn.execute("SELECT id FROM vouchers ORDER BY id").fetchall()
    conn.close()

    count = 0
    for v in all_vouchers:
        if v['id'] not in existing_vids:
            if add_voucher_to_chain(v['id']):
                count += 1
    return {"added": count, "total_blocks": get_chain_length()}


def validate_chain() -> dict:
    """Validate blockchain integrity."""
    conn = get_conn()
    blocks = conn.execute("SELECT * FROM blockchain ORDER BY index_no ASC").fetchall()
    conn.close()

    if not blocks:
        return {"valid": False, "errors": ["Empty chain"]}

    errors = []
    for i, b in enumerate(blocks):
        b = dict(b)
        raw = _block_to_string(b['index_no'], b['timestamp'], b['previous_hash'], b['data'], b['nonce'])
        expected_hash = _sha256(raw)
        if b['hash'] != expected_hash:
            errors.append(f"Block {b['index_no']}: hash mismatch (tampered)")

        if i > 0:
            prev = dict(blocks[i - 1])
            if b['previous_hash'] != prev['hash']:
                errors.append(f"Block {b['index_no']}: previous_hash broken (chain broken)")

        if i == 0 and b['index_no'] != 0:
            errors.append(f"Genesis block index should be 0, got {b['index_no']}")

    return {"valid": len(errors) == 0, "errors": errors, "blocks": len(blocks)}


def get_chain_stats() -> dict:
    """Return statistics about the blockchain."""
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM blockchain").fetchone()[0]
    last = conn.execute("SELECT * FROM blockchain ORDER BY index_no DESC LIMIT 1").fetchone()
    conn.close()
    stats = {
        "total_blocks": total,
        "genesis_created": total > 0,
        "last_block_index": last['index_no'] if last else 0,
        "last_block_hash": last['hash'][:16] + '...' if last else '',
    }
    return stats


def export_chain_json(filepath: str) -> dict:
    """Export blockchain to JSON file."""
    chain = get_chain(limit=10000)
    try:
        blocks = []
        for b in reversed(chain):
            blocks.append({
                "index": b['index_no'],
                "timestamp": b['timestamp'],
                "previous_hash": b['previous_hash'],
                "hash": b['hash'],
                "nonce": b['nonce'],
                "data": json_mod.loads(b.get('data', '{}')),
                "voucher_id": b.get('voucher_id'),
                "voucher_no": b.get('voucher_no'),
            })
        with open(filepath, 'w', encoding='utf-8') as f:
            json_mod.dump({"blockchain": blocks, "validated": validate_chain()}, f,
                          ensure_ascii=False, indent=2)
        return {"message": f"已导出 {len(blocks)} 个区块到 {filepath}", "count": len(blocks)}
    except Exception as e:
        return {"error": f"导出失败: {e}"}


def import_chain_json(filepath: str) -> dict:
    """Import blockchain from JSON file (appends to existing)."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json_mod.load(f)
        imported = data.get('blockchain', [])
        if not imported:
            return {"error": "文件中没有区块链数据"}

        conn = get_conn()
        conn.execute(BLOCKCHAIN_TABLE_SQL)
        count = 0
        for b in imported:
            existing = conn.execute("SELECT id FROM blockchain WHERE index_no=?", (b['index'],)).fetchone()
            if existing:
                continue
            conn.execute(
                "INSERT OR IGNORE INTO blockchain (index_no, timestamp, previous_hash, hash, nonce, data, voucher_id, voucher_no) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (b['index'], b['timestamp'], b['previous_hash'], b['hash'],
                 b['nonce'], json_mod.dumps(b['data'], ensure_ascii=False),
                 b.get('voucher_id'), b.get('voucher_no')))
            count += 1
        conn.commit()
        conn.close()
        return {"message": f"已导入 {count} 个新区块", "count": count}
    except Exception as e:
        return {"error": f"导入失败: {e}"}
