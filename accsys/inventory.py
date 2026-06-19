from __future__ import annotations

"""库存管理（进销存）模块。"""

from .database import get_conn


def init_inventory_tables():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT DEFAULT '',
            unit TEXT DEFAULT '个',
            unit_price DECIMAL(18,2) DEFAULT 0,
            quantity DECIMAL(18,2) DEFAULT 0,
            min_stock DECIMAL(18,2) DEFAULT 0,
            location TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS inventory_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            trans_type TEXT NOT NULL CHECK(trans_type IN ('in','out','adjust')),
            quantity DECIMAL(18,2) NOT NULL,
            unit_price DECIMAL(18,2) DEFAULT 0,
            ref_type TEXT DEFAULT '',
            ref_id TEXT DEFAULT '',
            note TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS inventory_warehouse (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            location TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()


def add_product(code: str, name: str, category: str = "", unit: str = "个",
                unit_price: float = 0, min_stock: float = 0, location: str = "") -> dict:
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO products (code, name, category, unit, unit_price, min_stock, location)
            VALUES (?,?,?,?,?,?,?)
        """, (code, name, category, unit, unit_price, min_stock, location))
        conn.commit()
        return {"success": True, "id": conn.execute("SELECT last_insert_rowid()").fetchone()[0]}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def update_product(pid: int, **kwargs):
    conn = get_conn()
    fields = {k: v for k, v in kwargs.items() if k in ("name","category","unit","unit_price","min_stock","location","is_active")}
    if not fields:
        conn.close()
        return
    sets = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [pid]
    conn.execute(f"UPDATE products SET {sets} WHERE id=?", vals)
    conn.commit()
    conn.close()


def inventory_in(product_id: int, quantity: float, unit_price: float = 0,
                 ref_type: str = "", ref_id: str = "", note: str = ""):
    conn = get_conn()
    conn.execute("""
        INSERT INTO inventory_transactions (product_id, trans_type, quantity, unit_price, ref_type, ref_id, note)
        VALUES (?, 'in', ?, ?, ?, ?, ?)
    """, (product_id, quantity, unit_price, ref_type, ref_id, note))
    conn.execute("UPDATE products SET quantity=quantity+?, unit_price=? WHERE id=?",
                 (quantity, unit_price, product_id))
    conn.commit()
    conn.close()


def inventory_out(product_id: int, quantity: float, ref_type: str = "",
                  ref_id: str = "", note: str = "", method: str = "fifo"):
    conn = get_conn()
    cur = conn.execute("SELECT quantity, unit_price FROM products WHERE id=?", (product_id,)).fetchone()
    if not cur or cur["quantity"] < quantity:
        conn.close()
        return {"success": False, "error": "库存不足"}
    qty_out = quantity
    cost_total = 0.0
    if method == "fifo":
        items = conn.execute("""
            SELECT id, quantity, unit_price FROM inventory_transactions
            WHERE product_id=? AND trans_type='in' AND quantity>0
            ORDER BY created_at ASC
        """, (product_id,)).fetchall()
        for it in items:
            if qty_out <= 0:
                break
            take = min(qty_out, float(it["quantity"]))
            cost_total += take * float(it["unit_price"])
            qty_out -= take
            conn.execute("UPDATE inventory_transactions SET quantity=quantity-? WHERE id=?",
                         (take, it["id"]))
    else:
        cost_total = quantity * float(cur["unit_price"])
    conn.execute("""
        INSERT INTO inventory_transactions (product_id, trans_type, quantity, unit_price, ref_type, ref_id, note)
        VALUES (?, 'out', ?, ?, ?, ?, ?)
    """, (product_id, -quantity, cost_total / quantity, ref_type, ref_id, note))
    conn.execute("UPDATE products SET quantity=quantity-? WHERE id=?", (quantity, product_id))
    conn.commit()
    conn.close()
    return {"success": True, "cost": round(cost_total, 2)}


def inventory_adjust(product_id: int, new_quantity: float, note: str = ""):
    conn = get_conn()
    cur = conn.execute("SELECT quantity FROM products WHERE id=?", (product_id,)).fetchone()
    if not cur:
        conn.close()
        return
    diff = new_quantity - float(cur["quantity"])
    conn.execute("""
        INSERT INTO inventory_transactions (product_id, trans_type, quantity, note)
        VALUES (?, 'adjust', ?, ?)
    """, (product_id, diff, note))
    conn.execute("UPDATE products SET quantity=? WHERE id=?", (new_quantity, product_id))
    conn.commit()
    conn.close()


def get_all_products(include_inactive: bool = False) -> list:
    conn = get_conn()
    q = "SELECT * FROM products" if include_inactive else "SELECT * FROM products WHERE is_active=1"
    rows = conn.execute(q).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_product(id: int) -> dict:
    conn = get_conn()
    r = conn.execute("SELECT * FROM products WHERE id=?", (id,)).fetchone()
    conn.close()
    return dict(r) if r else {}


def get_inventory_transactions(product_id: int = 0, limit: int = 100) -> list:
    conn = get_conn()
    if product_id:
        rows = conn.execute("""
            SELECT t.*, p.name as product_name, p.code as product_code
            FROM inventory_transactions t
            JOIN products p ON t.product_id=p.id
            WHERE t.product_id=?
            ORDER BY t.created_at DESC LIMIT ?
        """, (product_id, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT t.*, p.name as product_name, p.code as product_code
            FROM inventory_transactions t
            JOIN products p ON t.product_id=p.id
            ORDER BY t.created_at DESC LIMIT ?
        """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_inventory_summary() -> list:
    conn = get_conn()
    rows = conn.execute("""
        SELECT p.*,
               COALESCE(SUM(CASE WHEN t.trans_type='in' THEN t.quantity ELSE 0 END),0) as total_in,
               COALESCE(SUM(CASE WHEN t.trans_type='out' THEN ABS(t.quantity) ELSE 0 END),0) as total_out,
               p.quantity * p.unit_price as stock_value
        FROM products p
        LEFT JOIN inventory_transactions t ON t.product_id=p.id
        WHERE p.is_active=1
        GROUP BY p.id
        ORDER BY p.code
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
