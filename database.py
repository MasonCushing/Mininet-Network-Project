
import sqlite3
from datetime import datetime, timezone

DATABASE = "network_manager.db"


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS network_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                severity TEXT NOT NULL,
                event_type TEXT NOT NULL,
                device TEXT,
                message TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_timestamp
            ON network_events(timestamp)
        """)


def add_event(severity, event_type, message, device=None):
    timestamp = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO network_events
            (timestamp, severity, event_type, device, message)
            VALUES (?, ?, ?, ?, ?)
        """, (
            timestamp,
            severity,
            event_type,
            device,
            message
        ))


def get_events(limit=100):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT *
            FROM network_events
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return [dict(row) for row in rows]


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS network_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                severity TEXT NOT NULL,
                event_type TEXT NOT NULL,
                device TEXT,
                message TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_timestamp
            ON network_events(timestamp)
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS performance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                latency REAL,
                packet_loss REAL,
                throughput REAL,
                duration INTEGER
            )
        """)

        columns = [
            row['name']
            for row in conn.execute(
                "PRAGMA table_info(performance_history)"
            ).fetchall()
        ]

        if 'jitter' not in columns:
            conn.execute("""
                ALTER TABLE performance_history
                ADD COLUMN jitter REAL
            """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_performance_timestamp
            ON performance_history(timestamp)
        """)



def add_performance(
    source,
    target,
    latency,
    packet_loss,
    throughput,
    duration,
    jitter=None
):
    timestamp = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO performance_history (
                timestamp,
                source,
                target,
                latency,
                jitter,
                packet_loss,
                throughput,
                duration
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            source,
            target,
            latency,
            jitter,
            packet_loss,
            throughput,
            duration
        ))



def get_performance_history(limit=100):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT *
            FROM performance_history
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return [dict(row) for row in reversed(rows)]

def reset_performance_history():
    """Delete saved performance measurements only."""

    with get_connection() as conn:
        conn.execute("""
            DELETE FROM performance_history
        """)
