"""
Edge Onboard Telemetry Cache (SQLite Circuit Breaker)
=====================================================
Stores Protobuf telemetry packets to a local SQLite database during cellular/network
dropouts. Upon reconnection, buffered records are burst-uploaded to the MQTT broker
in strict FIFO order (Section 2.1 & 5.2 of Master Plan).
"""

import sqlite3
import logging
import threading
import time
from typing import List, Tuple

logger = logging.getLogger("EdgeCache")


class EdgeTelemetryCache:
    def __init__(self, db_path: str = "edge/storage/telemetry_cache.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS offline_telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    payload BLOB NOT NULL,
                    timestamp_ms INTEGER NOT NULL,
                    created_at REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON offline_telemetry (timestamp_ms)
            """)
            conn.commit()
            logger.info(f"[Cache] SQLite offline buffer ready at {self.db_path}")

    def enqueue(self, topic: str, payload_bytes: bytes, timestamp_ms: int) -> int:
        """Saves a binary packet into the offline database."""
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO offline_telemetry (topic, payload, timestamp_ms, created_at) VALUES (?, ?, ?, ?)",
                (topic, payload_bytes, timestamp_ms, time.time())
            )
            conn.commit()
            record_id = cursor.lastrowid
            logger.debug(f"[Cache] Queued packet #{record_id} ({len(payload_bytes)} bytes)")
            return record_id

    def peek_batch(self, limit: int = 50) -> List[Tuple[int, str, bytes]]:
        """Retrieves oldest batch of buffered records in FIFO order (id, topic, payload)."""
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, topic, payload FROM offline_telemetry ORDER BY id ASC LIMIT ?",
                (limit,)
            )
            return cursor.fetchall()

    def remove_batch(self, ids: List[int]):
        """Deletes successfully burst-uploaded records."""
        if not ids:
            return
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" for _ in ids)
            cursor.execute(
                f"DELETE FROM offline_telemetry WHERE id IN ({placeholders})",
                ids
            )
            conn.commit()
            logger.info(f"[Cache] Purged {len(ids)} burst-uploaded packets from offline cache")

    def count(self) -> int:
        """Returns number of queued packets waiting for transmission."""
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM offline_telemetry")
            return cursor.fetchone()[0]
