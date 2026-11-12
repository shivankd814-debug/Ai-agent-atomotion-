import json, os, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from .config import get_settings


def _connect():
    path = get_settings().database_path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with _connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            task TEXT NOT NULL,
            provider TEXT NOT NULL,
            status TEXT NOT NULL,
            result TEXT,
            trace TEXT
        )""")

def save_task(task: str, provider: str, status: str, result: str = "", trace=None) -> int:
    with _connect() as con:
        cur = con.execute("INSERT INTO tasks(created_at,task,provider,status,result,trace) VALUES(?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), task, provider, status, result, json.dumps(trace or [], ensure_ascii=False)))
        return int(cur.lastrowid)

def recent_tasks(limit: int = 30):
    with _connect() as con:
        rows = con.execute("SELECT id,created_at,task,provider,status,result,trace FROM tasks ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) | {"trace": json.loads(r["trace"] or "[]")} for r in rows]


def enqueue_device_job(payload: dict) -> int:
    with _connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS device_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
            payload TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', result TEXT
        )""")
        cur = con.execute("INSERT INTO device_jobs(created_at,payload,status) VALUES(?,?, 'pending')",
            (datetime.now(timezone.utc).isoformat(), json.dumps(payload, ensure_ascii=False)))
        return int(cur.lastrowid)

def take_device_job():
    with _connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS device_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
            payload TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', result TEXT
        )""")
        row = con.execute("SELECT id,payload FROM device_jobs WHERE status='pending' ORDER BY id LIMIT 1").fetchone()
        if not row:
            return None
        con.execute("UPDATE device_jobs SET status='running' WHERE id=?", (row['id'],))
        return {"id": row['id'], "payload": json.loads(row['payload'])}

def finish_device_job(job_id: int, result: str):
    with _connect() as con:
        con.execute("UPDATE device_jobs SET status='completed', result=? WHERE id=?", (result[:1000], job_id))
