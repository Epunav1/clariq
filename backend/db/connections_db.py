import sqlite3
import os
from typing import Dict, List, Optional
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'clariq_connections.sqlite')


def _conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = _conn()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS connections (
        id TEXT PRIMARY KEY,
        platform TEXT,
        store_name TEXT,
        store_url TEXT,
        api_key TEXT,
        connection_method TEXT,
        status TEXT,
        connected_at TEXT,
        last_sync TEXT,
        products_synced INTEGER DEFAULT 0,
        orders_synced INTEGER DEFAULT 0,
        customers_synced INTEGER DEFAULT 0
    )
    ''')
    conn.commit()
    cur.close()
    conn.close()


def add_connection(conn: Dict) -> Dict:
    init_db()
    conn_db = _conn()
    cur = conn_db.cursor()
    now = conn.get('connected_at') or datetime.utcnow().isoformat()
    cur.execute('''INSERT INTO connections
        (id, platform, store_name, store_url, api_key, connection_method, status, connected_at, last_sync, products_synced, orders_synced, customers_synced)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        conn['id'], conn.get('platform'), conn.get('store_name'), conn.get('store_url'), conn.get('api_key'), conn.get('connection_method'), conn.get('status', 'connected'), now, conn.get('last_sync'), conn.get('products_synced', 0), conn.get('orders_synced', 0), conn.get('customers_synced', 0)
    ))
    conn_db.commit()
    cur.close()
    conn_db.close()
    return conn


def list_connections() -> List[Dict]:
    init_db()
    c = _conn()
    cur = c.cursor()
    cur.execute('SELECT id, platform, store_name, store_url, connection_method, status, connected_at, last_sync, products_synced, orders_synced, customers_synced FROM connections ORDER BY connected_at DESC')
    rows = cur.fetchall()
    cols = ['id','platform','store_name','store_url','connection_method','status','connected_at','last_sync','products_synced','orders_synced','customers_synced']
    out = [dict(zip(cols, r)) for r in rows]
    cur.close()
    c.close()
    return out


def get_connections(platform: Optional[str] = None) -> List[Dict]:
    """Get connections, optionally filtered by platform."""
    init_db()
    c = _conn()
    cur = c.cursor()
    if platform:
        cur.execute('SELECT id, platform, store_name, store_url, api_key, connection_method, status, connected_at, last_sync, products_synced, orders_synced, customers_synced FROM connections WHERE platform=? ORDER BY connected_at DESC', (platform,))
    else:
        cur.execute('SELECT id, platform, store_name, store_url, api_key, connection_method, status, connected_at, last_sync, products_synced, orders_synced, customers_synced FROM connections ORDER BY connected_at DESC')
    rows = cur.fetchall()
    cols = ['id','platform','store_name','store_url','api_key','connection_method','status','connected_at','last_sync','products_synced','orders_synced','customers_synced']
    out = [dict(zip(cols, r)) for r in rows]
    cur.close()
    c.close()
    return out


def get_connection(conn_id: str) -> Optional[Dict]:
    init_db()
    c = _conn()
    cur = c.cursor()
    cur.execute('SELECT id, platform, store_name, store_url, api_key, connection_method, status, connected_at, last_sync, products_synced, orders_synced, customers_synced FROM connections WHERE id=?', (conn_id,))
    r = cur.fetchone()
    cur.close()
    c.close()
    if not r:
        return None
    cols = ['id','platform','store_name','store_url','api_key','connection_method','status','connected_at','last_sync','products_synced','orders_synced','customers_synced']
    return dict(zip(cols, r))


def remove_connection(conn_id: str) -> Optional[Dict]:
    existing = get_connection(conn_id)
    if not existing:
        return None
    c = _conn()
    cur = c.cursor()
    cur.execute('DELETE FROM connections WHERE id=?', (conn_id,))
    c.commit()
    cur.close()
    c.close()
    return existing


def update_connection(conn_id: str, updates: Dict) -> Optional[Dict]:
    ex = get_connection(conn_id)
    if not ex:
        return None
    allowed = ['platform','store_name','store_url','api_key','connection_method','status','last_sync','products_synced','orders_synced','customers_synced']
    sets = []
    vals = []
    for k,v in updates.items():
        if k in allowed:
            sets.append(f"{k}=?")
            vals.append(v)
    if not sets:
        return ex
    vals.append(conn_id)
    c = _conn()
    cur = c.cursor()
    cur.execute(f"UPDATE connections SET {', '.join(sets)} WHERE id=?", tuple(vals))
    c.commit()
    cur.close()
    c.close()
    return get_connection(conn_id)
