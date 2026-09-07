"""Compact append-only Stigma Film Memory using only the standard library."""

from dataclasses import dataclass
from hashlib import sha256
import json
import sqlite3
import zlib


@dataclass(frozen=True, slots=True)
class FilmFrame:
    frame_id: int
    digest: str
    state: str
    method: str | None
    compressed_bytes: int
    original_bytes: int

    def as_dict(self):
        return {"frame_id": self.frame_id, "digest": self.digest, "state": self.state, "method": self.method, "compressed_bytes": self.compressed_bytes, "original_bytes": self.original_bytes}


class StigmaFilmMemory:
    """Stores compressed immutable frames; UI reads metadata until a frame is recalled."""

    def __init__(self, connection: sqlite3.Connection):
        self.db = connection
        self.db.execute("""CREATE TABLE IF NOT EXISTS stigma_frames (
            frame_id INTEGER PRIMARY KEY AUTOINCREMENT,
            digest TEXT NOT NULL UNIQUE,
            state TEXT NOT NULL,
            method TEXT,
            payload BLOB NOT NULL,
            original_bytes INTEGER NOT NULL
        )""")

    def remember(self, value: dict) -> FilmFrame:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        digest = sha256(raw).hexdigest()
        payload = zlib.compress(raw, level=9)
        state = str(value.get("state", "unavailable"))
        method = value.get("method")
        self.db.execute("INSERT OR IGNORE INTO stigma_frames(digest,state,method,payload,original_bytes) VALUES(?,?,?,?,?)", (digest, state, method, payload, len(raw)))
        row = self.db.execute("SELECT frame_id,state,method,length(payload),original_bytes FROM stigma_frames WHERE digest=?", (digest,)).fetchone()
        return FilmFrame(row[0], digest, row[1], row[2], row[3], row[4])

    def recall(self, digest: str):
        row = self.db.execute("SELECT payload FROM stigma_frames WHERE digest=?", (digest,)).fetchone()
        return None if row is None else json.loads(zlib.decompress(row[0]))

