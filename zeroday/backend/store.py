"""Small SQLite persistence layer for agents, events and trade proposals."""
from __future__ import annotations
import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(os.getenv("ZERO_DAY_DB_PATH", "data/zeroday.db"))
_lock = threading.RLock()

@contextmanager
def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db() -> None:
    with _lock, _connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS agents (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, strategy TEXT NOT NULL DEFAULT 'trend',
          model TEXT NOT NULL DEFAULT '', provider_id TEXT NOT NULL DEFAULT 'default', risk_profile TEXT NOT NULL DEFAULT 'conservative',
          allocation REAL NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'idle',
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS events (
          id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL,
          message TEXT NOT NULL, payload_json TEXT NOT NULL DEFAULT '{}',
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS proposals (
          id TEXT PRIMARY KEY, agent_id TEXT NOT NULL, symbol TEXT NOT NULL,
          action TEXT NOT NULL, confidence REAL NOT NULL DEFAULT 0,
          rationale TEXT NOT NULL, snapshot_json TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending_validation', created_at TEXT NOT NULL,
          FOREIGN KEY(agent_id) REFERENCES agents(id)
        );
        CREATE TABLE IF NOT EXISTS provider_profiles (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, base_url TEXT NOT NULL,
          model TEXT NOT NULL, api_key_env TEXT NOT NULL DEFAULT '',
          enabled INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL
        );
        """)
        columns = {row["name"] for row in db.execute("PRAGMA table_info(agents)").fetchall()}
        if "provider_id" not in columns:
            db.execute("ALTER TABLE agents ADD COLUMN provider_id TEXT NOT NULL DEFAULT 'default'")
        db.commit()

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def event(kind: str, message: str, payload: dict[str, Any] | None = None) -> None:
    with _lock, _connect() as db:
        db.execute("INSERT INTO events(kind,message,payload_json,created_at) VALUES(?,?,?,?)",
                   (kind, message[:500], json.dumps(payload or {})[:8000], now()))
        db.commit()

def list_events(limit: int = 50) -> list[dict[str, Any]]:
    with _lock, _connect() as db:
        rows = db.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (max(1,min(limit,200)),)).fetchall()
        return [dict(r) | {"payload": json.loads(r["payload_json"])} for r in rows]

def create_agent(agent: dict[str, Any]) -> dict[str, Any]:
    with _lock, _connect() as db:
        db.execute("""INSERT INTO agents(id,name,strategy,model,provider_id,risk_profile,allocation,status,created_at)
          VALUES(?,?,?,?,?,?,?,?,?)""",
          (agent["id"],agent["name"],agent.get("strategy","trend"),agent.get("model",""),agent.get("provider_id","default"),
           agent.get("risk_profile","conservative"),agent.get("allocation",0),"idle",now()))
        db.commit()
    event("agent", f"Agente {agent['name']} registrado.", {"agent_id":agent["id"]})
    return get_agent(agent["id"])

def get_agent(agent_id: str) -> dict[str, Any] | None:
    with _lock, _connect() as db:
        row = db.execute("SELECT * FROM agents WHERE id=?", (agent_id,)).fetchone()
        return dict(row) if row else None

def list_agents() -> list[dict[str, Any]]:
    with _lock, _connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM agents ORDER BY created_at DESC").fetchall()]

def set_agent_status(agent_id: str, status: str) -> None:
    with _lock, _connect() as db:
        db.execute("UPDATE agents SET status=? WHERE id=?", (status, agent_id)); db.commit()

def save_proposal(p: dict[str, Any]) -> None:
    with _lock, _connect() as db:
        db.execute("""INSERT INTO proposals(id,agent_id,symbol,action,confidence,rationale,snapshot_json,status,created_at)
          VALUES(?,?,?,?,?,?,?,?,?)""",
          (p["id"],p["agent_id"],p["symbol"],p["action"],p["confidence"],p["rationale"],
           json.dumps(p["snapshot"]),p["status"],now()))
        db.commit()
    event("proposal", f"Agente {p['agent_id']} propôs {p['action']} em {p['symbol']}; nenhuma ordem foi enviada.",
          {"proposal_id":p["id"],"status":p["status"]})

def list_proposals(limit: int = 100) -> list[dict[str, Any]]:
    with _lock, _connect() as db:
        rows = db.execute("SELECT * FROM proposals ORDER BY created_at DESC LIMIT ?", (max(1,min(limit,300)),)).fetchall()
        return [dict(r) | {"snapshot":json.loads(r["snapshot_json"])} for r in rows]

def list_provider_profiles() -> list[dict[str, Any]]:
    with _lock, _connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM provider_profiles ORDER BY created_at DESC").fetchall()]
