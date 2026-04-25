import sqlite3
from typing import Optional

_conn: Optional[sqlite3.Connection] = None


def init_db(path: str = "catalog.db") -> sqlite3.Connection:
    global _conn
    _conn = sqlite3.connect(path, check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    _conn.execute("PRAGMA foreign_keys = ON")
    _conn.executescript("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            price REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS item_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
            filename TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0
        );
    """)
    try:
        _conn.execute("ALTER TABLE items ADD COLUMN category TEXT NOT NULL DEFAULT ''")
        _conn.commit()
    except Exception:
        pass  # column already exists
    _conn.commit()
    return _conn


def create_item(title: str, description: str, price: float, status: str, category: str = "") -> int:
    cur = _conn.execute(
        "INSERT INTO items (title, description, price, status, category) VALUES (?, ?, ?, ?, ?)",
        (title, description, price, status, category),
    )
    _conn.commit()
    return cur.lastrowid


def get_item(item_id: int) -> Optional[sqlite3.Row]:
    return _conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()


def list_items() -> list:
    return _conn.execute("SELECT * FROM items ORDER BY created_at DESC").fetchall()


def update_item(item_id: int, title: str, description: str, price: float, status: str, category: str = ""):
    _conn.execute(
        "UPDATE items SET title=?, description=?, price=?, status=?, category=? WHERE id=?",
        (title, description, price, status, category, item_id),
    )
    _conn.commit()


def delete_item(item_id: int):
    _conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    _conn.commit()


def add_image(item_id: int, filename: str, sort_order: int = 0) -> int:
    cur = _conn.execute(
        "INSERT INTO item_images (item_id, filename, sort_order) VALUES (?, ?, ?)",
        (item_id, filename, sort_order),
    )
    _conn.commit()
    return cur.lastrowid


def get_images(item_id: int) -> list:
    return _conn.execute(
        "SELECT * FROM item_images WHERE item_id = ? ORDER BY sort_order",
        (item_id,),
    ).fetchall()


def delete_image(image_id: int):
    _conn.execute("DELETE FROM item_images WHERE id = ?", (image_id,))
    _conn.commit()


def set_cover_image(item_id: int, image_id: int):
    images = get_images(item_id)
    if not any(img["id"] == image_id for img in images):
        raise ValueError(f"image {image_id} does not belong to item {item_id}")
    ordered = [img for img in images if img["id"] == image_id] + \
              [img for img in images if img["id"] != image_id]
    for i, img in enumerate(ordered):
        _conn.execute("UPDATE item_images SET sort_order = ? WHERE id = ?", (i, img["id"]))
    _conn.commit()
