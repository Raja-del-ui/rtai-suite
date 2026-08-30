"""Append-only local persistence: JSONL lines and a minimal SQLite event store."""

import datetime as dt
import json
import sqlite3
import threading
from pathlib import Path

from rtai_core.exceptions import StorageError


class JsonlStore:
    def __init__(self, path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def append(self, record: dict) -> None:
        line = json.dumps({"ts": dt.datetime.now().isoformat(timespec="milliseconds"),
                           **record}, default=str)
        try:
            with self._lock, self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError as exc:
            raise StorageError(f"cannot append to {self.path}: {exc}") from exc

    def read(self):
        if not self.path.exists():
            return []
        rows = []
        with self.path.open(encoding="utf-8") as fh:
            for number, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise StorageError(f"{self.path}:{number}: bad JSON ({exc})") from exc
        return rows


class SqliteEventStore:
    """Tiny append-only event store; one table, indexed by (kind, ts)."""

    SCHEMA = ("CREATE TABLE IF NOT EXISTS events ("
              "id INTEGER PRIMARY KEY AUTOINCREMENT,"
              "kind TEXT NOT NULL, ts TEXT NOT NULL,"
              "payload TEXT NOT NULL)")

    def __init__(self, path):
        self.path = Path(path)
        self._lock = threading.Lock()
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self._connect() as conn:
                conn.execute(self.SCHEMA)
                conn.execute("CREATE INDEX IF NOT EXISTS ix_events_kind_ts "
                             "ON events(kind, ts)")
        except sqlite3.Error as exc:
            raise StorageError(f"cannot open store {self.path}: {exc}") from exc

    def _connect(self):
        return sqlite3.connect(str(self.path), timeout=15)

    def emit(self, kind: str, **payload) -> int:
        ts = dt.datetime.now().isoformat(timespec="milliseconds")
        try:
            with self._lock, self._connect() as conn:
                cursor = conn.execute("INSERT INTO events(kind, ts, payload) "
                                      "VALUES (?, ?, ?)", (kind, ts,
                                                           json.dumps(payload, default=str)))
                return cursor.lastrowid
        except sqlite3.Error as exc:
            raise StorageError(f"emit failed on {self.path}: {exc}") from exc

    def query(self, kind=None, limit=1000):
        sql = "SELECT id, kind, ts, payload FROM events"
        params: tuple = ()
        if kind:
            sql += " WHERE kind = ?"
            params = (kind,)
        sql += " ORDER BY id DESC LIMIT ?"
        params += (limit,)
        try:
            with self._connect() as conn:
                rows = conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            raise StorageError(f"query failed on {self.path}: {exc}") from exc
        return [{"id": r[0], "kind": r[1], "ts": r[2], "payload": json.loads(r[3])}
                for r in rows]
