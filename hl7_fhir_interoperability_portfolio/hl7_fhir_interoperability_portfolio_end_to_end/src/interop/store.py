"""SQLite audit log and demo idempotency store."""
import json, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

class MessageStore:
    def __init__(self, path: str = "interop_messages.db"):
        self.path = path
        self._memory_conn = None
        if path == ":memory:":
            # A normal SQLite :memory: database is per connection. Keep one connection
            # so each operation sees the same database during tests.
            self._memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._memory_conn.row_factory = sqlite3.Row
        self._init_db()

    def _connect(self):
        if self._memory_conn is not None:
            return self._memory_conn
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        return con

    def _init_db(self):
        with self._connect() as con:
            con.execute("""CREATE TABLE IF NOT EXISTS messages (
                control_id TEXT PRIMARY KEY,
                message_type TEXT,
                received_at TEXT NOT NULL,
                status TEXT NOT NULL,
                error TEXT,
                resources_json TEXT
            )""")

    def get(self, control_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as con:
            row = con.execute("SELECT * FROM messages WHERE control_id=?", (control_id,)).fetchone()
        return dict(row) if row else None

    def record(self, control_id: str, message_type: str, status: str,
               error: Optional[str] = None, resources: Optional[list] = None) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        try:
            with self._connect() as con:
                con.execute("""INSERT INTO messages
                    (control_id,message_type,received_at,status,error,resources_json)
                    VALUES (?,?,?,?,?,?)""",
                    (control_id, message_type, now, status, error,
                     json.dumps(resources) if resources is not None else None))
            return True
        except sqlite3.IntegrityError:
            return False

    def recent(self, limit: int = 50):
        with self._connect() as con:
            rows = con.execute("SELECT * FROM messages ORDER BY received_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]
