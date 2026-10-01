import sqlite3
from datetime import datetime, timezone
import json

DB_PATH = "db/telemetry.db"


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        # Buat tabel utama
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            data TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """)

        # PERBAIKAN: Tambahkan index untuk mempercepat pencarian data berdasarkan device_id & timestamp
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_device_timestamp 
        ON sensor_data (device_id, timestamp)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp 
        ON sensor_data (timestamp)
        """)


def insert_sensor_data(device_id, data):
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # PERBAIKAN: Gunakan ISO/UTC timestamp agar konsisten di semua server
        utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
        INSERT INTO sensor_data (device_id, data, timestamp)
        VALUES (?, ?, ?)
        """, (
            device_id,
            json.dumps(data) if isinstance(data, (dict, list)) else data,
            utc_now
        ))


def get_all_data(limit=100):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT device_id, data, timestamp
        FROM sensor_data
        ORDER BY id DESC
        LIMIT ?
        """, (limit,))
        return cursor.fetchall()


def get_by_device(device_id, limit=100):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT device_id, data, timestamp
        FROM sensor_data
        WHERE device_id = ?
        ORDER BY id DESC
        LIMIT ?
        """, (device_id, limit))
        return cursor.fetchall()


def get_data_by_range(device_id=None, modifier="-1 day", limit=None):
    """
    Mengambil data telemetry berdasarkan modifier waktu SQLite & optional device_id.
    Contoh modifier: '-1 day', '-7 days', '-1 month'
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        # PERBAIKAN: Menggunakan 'now' (UTC) agar sinkron dengan datetime.now(timezone.utc)
        query = """
            SELECT device_id, data, timestamp
            FROM sensor_data
            WHERE timestamp >= datetime('now', ?)
        """
        params = [modifier]

        if device_id:
            query += " AND device_id = ?"
            params.append(device_id)

        query += " ORDER BY id ASC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)
        return cursor.fetchall()
