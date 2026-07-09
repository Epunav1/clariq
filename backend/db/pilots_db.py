import sqlite3
import os
from typing import Dict, List, Optional
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'clariq_pilots.sqlite')

def _conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    c = _conn()
    cur = c.cursor()
    # create table if missing
    cur.execute('''
    CREATE TABLE IF NOT EXISTS pilots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        store_name TEXT,
        platform TEXT,
        notes TEXT,
        status TEXT DEFAULT 'new',
        contacted_at TEXT,
        created_at TEXT
    )
    ''')
    c.commit()
    # ensure columns exist for older DBs
    cur.execute("PRAGMA table_info(pilots)")
    cols = [r[1] for r in cur.fetchall()]
    if 'status' not in cols:
        cur.execute("ALTER TABLE pilots ADD COLUMN status TEXT DEFAULT 'new'")
    if 'contacted_at' not in cols:
        cur.execute("ALTER TABLE pilots ADD COLUMN contacted_at TEXT")
    if 'last_email_sent_at' not in cols:
        cur.execute("ALTER TABLE pilots ADD COLUMN last_email_sent_at TEXT")
    if 'last_email_body' not in cols:
        cur.execute("ALTER TABLE pilots ADD COLUMN last_email_body TEXT")
    c.commit()
    cur.close()
    c.close()

def add_pilot(data: Dict) -> Dict:
    init_db()
    c = _conn()
    cur = c.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute('INSERT INTO pilots (name, email, store_name, platform, notes, created_at) VALUES (?,?,?,?,?,?)', (
        data.get('name'), data.get('email'), data.get('store_name'), data.get('platform'), data.get('notes'), now
    ))
    c.commit()
    pid = cur.lastrowid
    cur.close()
    c.close()
    return {**data, 'id': pid, 'created_at': now}

def list_pilots() -> List[Dict]:
    init_db()
    c = _conn()
    cur = c.cursor()
    cur.execute('SELECT id, name, email, store_name, platform, notes, status, contacted_at, created_at FROM pilots ORDER BY created_at DESC')
    rows = cur.fetchall()
    cur.close()
    c.close()
    cols = ['id','name','email','store_name','platform','notes','status','contacted_at','created_at']
    return [dict(zip(cols, r)) for r in rows]


def update_pilot_status(pilot_id: int, status: str) -> Optional[Dict]:
    init_db()
    c = _conn()
    cur = c.cursor()
    from datetime import datetime
    now = datetime.utcnow().isoformat()
    cur.execute('UPDATE pilots SET status=?, contacted_at=? WHERE id=?', (status, now, pilot_id))
    c.commit()
    cur.close()
    c.close()
    # return updated record
    allp = list_pilots()
    for p in allp:
        if p['id'] == pilot_id:
            return p
    return None


def get_pilot(pilot_id: int) -> Optional[Dict]:
    init_db()
    c = _conn()
    cur = c.cursor()
    cur.execute('SELECT id, name, email, store_name, platform, notes, status, contacted_at, created_at FROM pilots WHERE id=?', (pilot_id,))
    row = cur.fetchone()
    cur.close()
    c.close()
    if not row:
        return None
    cols = ['id','name','email','store_name','platform','notes','status','contacted_at','created_at']
    return dict(zip(cols, row))


def record_email_send(pilot_id: int, body: str) -> Optional[Dict]:
    init_db()
    c = _conn()
    cur = c.cursor()
    from datetime import datetime
    now = datetime.utcnow().isoformat()
    cur.execute('UPDATE pilots SET last_email_sent_at=?, last_email_body=?, status=?, contacted_at=? WHERE id=?', (now, body, 'contacted', now, pilot_id))
    c.commit()
    cur.close()
    c.close()
    return get_pilot(pilot_id)
