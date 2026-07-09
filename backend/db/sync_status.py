import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path

# Database for sync status tracking
SYNC_DB = Path(__file__).parent / 'db' / 'sync_status.sqlite'


def init_sync_db():
    """Initialize sync status database."""
    SYNC_DB.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(SYNC_DB))
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS sync_jobs (
        id TEXT PRIMARY KEY,
        sync_type TEXT NOT NULL,
        store_id TEXT,
        status TEXT DEFAULT 'pending',
        last_synced_at TEXT,
        next_sync_at TEXT,
        error_message TEXT,
        records_synced INTEGER DEFAULT 0,
        duration_seconds REAL,
        created_at TEXT,
        updated_at TEXT
    )''')
    
    conn.commit()
    conn.close()


def get_or_create_sync_job(job_id: str, sync_type: str, store_id: Optional[str] = None) -> Dict:
    """Get or create a sync job record."""
    conn = sqlite3.connect(str(SYNC_DB))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT * FROM sync_jobs WHERE id = ?', (job_id,))
    row = c.fetchone()
    
    if row:
        conn.close()
        return dict(row)
    
    # Create new job
    now = datetime.utcnow().isoformat()
    c.execute('''INSERT INTO sync_jobs 
        (id, sync_type, store_id, status, created_at, updated_at) 
        VALUES (?, ?, ?, ?, ?, ?)''',
        (job_id, sync_type, store_id, 'pending', now, now))
    conn.commit()
    conn.close()
    
    return {
        'id': job_id,
        'sync_type': sync_type,
        'store_id': store_id,
        'status': 'pending',
        'last_synced_at': None,
        'next_sync_at': None,
        'error_message': None,
        'records_synced': 0,
        'duration_seconds': None,
        'created_at': now,
        'updated_at': now
    }


def update_sync_job(job_id: str, status: str, **kwargs) -> Dict:
    """Update a sync job with new status and metadata."""
    conn = sqlite3.connect(str(SYNC_DB))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    updates = {'status': status, 'updated_at': datetime.utcnow().isoformat()}
    updates.update(kwargs)
    
    set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
    values = list(updates.values()) + [job_id]
    
    c.execute(f'UPDATE sync_jobs SET {set_clause} WHERE id = ?', values)
    
    c.execute('SELECT * FROM sync_jobs WHERE id = ?', (job_id,))
    row = c.fetchone()
    conn.commit()
    conn.close()
    
    return dict(row) if row else {}


def get_all_sync_jobs() -> List[Dict]:
    """Get all sync jobs."""
    conn = sqlite3.connect(str(SYNC_DB))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT * FROM sync_jobs ORDER BY updated_at DESC')
    rows = c.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_sync_job(job_id: str) -> Optional[Dict]:
    """Get a specific sync job."""
    conn = sqlite3.connect(str(SYNC_DB))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT * FROM sync_jobs WHERE id = ?', (job_id,))
    row = c.fetchone()
    conn.close()
    
    return dict(row) if row else None


# Initialize on import
init_sync_db()
