"""Persistent stepping-stone ledger backed by compact Stigma film frames."""

from datetime import UTC, datetime
from pathlib import Path
import sqlite3
from threading import Lock
from .evidence import Datum
from .stigma import StigmaFilmMemory


class JourneyLedger:
    def __init__(self, path="data/neuclx.sqlite3"):
        self.path = str(path)
        self._lock = Lock()
        if self.path != ":memory:": Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS stones(number INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT NOT NULL,prompt TEXT NOT NULL,frame_digest TEXT NOT NULL)")
            StigmaFilmMemory(db)

    def _connect(self): return sqlite3.connect(self.path)

    def record(self, prompt: str, response: Datum):
        created = datetime.now(UTC).isoformat()
        with self._lock, self._connect() as db:
            frame = StigmaFilmMemory(db).remember(response.as_dict())
            cursor = db.execute("INSERT INTO stones(created_at,prompt,frame_digest) VALUES(?,?,?)", (created, prompt, frame.digest))
            number = int(cursor.lastrowid)
        return {"number": number, "created_at": created, "prompt": prompt, "achievement": "success", "response": response.as_dict(), "stigma_frame": frame.as_dict()}

    def recent(self, limit=50):
        limit = max(1, min(int(limit), 500))
        with self._connect() as db:
            film = StigmaFilmMemory(db)
            rows = db.execute("SELECT number,created_at,prompt,frame_digest FROM stones ORDER BY number DESC LIMIT ?", (limit,)).fetchall()
            return [{"number": n, "created_at": c, "prompt": p, "achievement": "success", "response": film.recall(d), "stigma_frame": {"digest": d}} for n,c,p,d in reversed(rows)]

