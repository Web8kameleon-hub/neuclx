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
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._initialize()

    def close(self):
        if getattr(self, "_connection", None) is not None:
            self._connection.close()
            self._connection = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def _initialize(self):
        self._connection.execute("CREATE TABLE IF NOT EXISTS stones(number INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT NOT NULL,prompt TEXT NOT NULL,frame_digest TEXT NOT NULL)")
        StigmaFilmMemory(self._connection)
        self._connection.commit()

    def _connect(self):
        if self._connection is None:
            self._connection = sqlite3.connect(self.path, check_same_thread=False)
        return self._connection

    def record(self, prompt: str, response: Datum):
        created = datetime.now(UTC).isoformat()
        connection = self._connect()
        with self._lock:
            frame = StigmaFilmMemory(connection).remember(response.as_dict())
            cursor = connection.execute("INSERT INTO stones(created_at,prompt,frame_digest) VALUES(?,?,?)", (created, prompt, frame.digest))
            connection.commit()
            number = int(cursor.lastrowid)
        achievement = "success" if response.state.value in {"measured", "computed"} else "recorded"
        return {"number": number, "created_at": created, "prompt": prompt, "achievement": achievement, "response": response.as_dict(), "stigma_frame": frame.as_dict()}

    def recent(self, limit=50):
        limit = max(1, min(int(limit), 500))
        connection = self._connect()
        film = StigmaFilmMemory(connection)
        rows = connection.execute("SELECT number,created_at,prompt,frame_digest FROM stones ORDER BY number DESC LIMIT ?", (limit,)).fetchall()
        entries = []
        for n,c,p,d in reversed(rows):
            response = film.recall(d)
            achievement = "success" if response.get("state") in {"measured", "computed"} else "recorded"
            entries.append({"number": n, "created_at": c, "prompt": p, "achievement": achievement, "response": response, "stigma_frame": {"digest": d}})
        return entries

