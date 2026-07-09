import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), 'clariq_actions.sqlite')


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    c = _conn()
    cur = c.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT,
        pilot_id INTEGER,
        store_id TEXT,
        product_id TEXT,
        quantity INTEGER,
        metadata TEXT,
        created_at TEXT
    )
    ''')
    c.commit()
    cur.close()
    c.close()


def log_action(action_type: str, pilot_id: Optional[int] = None, store_id: Optional[str] = None, 
               product_id: Optional[str] = None, quantity: Optional[int] = None, 
               metadata: Optional[str] = None) -> Dict:
    init_db()
    c = _conn()
    cur = c.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute('''
    INSERT INTO actions (action_type, pilot_id, store_id, product_id, quantity, metadata, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (action_type, pilot_id, store_id, product_id, quantity, metadata, now))
    c.commit()
    action_id = cur.lastrowid
    cur.close()
    c.close()
    return {
        "id": action_id,
        "action_type": action_type,
        "pilot_id": pilot_id,
        "created_at": now
    }


def get_actions(action_type: Optional[str] = None, pilot_id: Optional[int] = None) -> List[Dict]:
    init_db()
    c = _conn()
    cur = c.cursor()
    if action_type and pilot_id:
        cur.execute(
            'SELECT id, action_type, pilot_id, store_id, product_id, quantity, metadata, created_at FROM actions WHERE action_type=? AND pilot_id=? ORDER BY created_at DESC',
            (action_type, pilot_id)
        )
    elif action_type:
        cur.execute(
            'SELECT id, action_type, pilot_id, store_id, product_id, quantity, metadata, created_at FROM actions WHERE action_type=? ORDER BY created_at DESC',
            (action_type,)
        )
    elif pilot_id:
        cur.execute(
            'SELECT id, action_type, pilot_id, store_id, product_id, quantity, metadata, created_at FROM actions WHERE pilot_id=? ORDER BY created_at DESC',
            (pilot_id,)
        )
    else:
        cur.execute(
            'SELECT id, action_type, pilot_id, store_id, product_id, quantity, metadata, created_at FROM actions ORDER BY created_at DESC'
        )
    rows = cur.fetchall()
    cur.close()
    c.close()
    cols = ['id', 'action_type', 'pilot_id', 'store_id', 'product_id', 'quantity', 'metadata', 'created_at']
    return [dict(zip(cols, r)) for r in rows]


def count_actions(action_type: Optional[str] = None, pilot_id: Optional[int] = None) -> int:
    init_db()
    c = _conn()
    cur = c.cursor()
    if action_type and pilot_id:
        cur.execute('SELECT COUNT(*) as cnt FROM actions WHERE action_type=? AND pilot_id=?', (action_type, pilot_id))
    elif action_type:
        cur.execute('SELECT COUNT(*) as cnt FROM actions WHERE action_type=?', (action_type,))
    elif pilot_id:
        cur.execute('SELECT COUNT(*) as cnt FROM actions WHERE pilot_id=?', (pilot_id,))
    else:
        cur.execute('SELECT COUNT(*) as cnt FROM actions')
    res = cur.fetchone()
    cur.close()
    c.close()
    return res['cnt'] if res else 0
