import os
import sqlite3
from datetime import datetime
import streamlit as st

# Path absolut ke database agar tidak keleset saat di-import
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "db", "telemetry.db")


def get_metadata_by_device(device_id, pond_id="k1"):
    """Mengambil metadata berdasarkan device_id dan pond_id."""
    if not os.path.exists(DB_PATH):
        return None

    try:
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT jenis, tgl_mulai, tgl_panen 
                FROM metadata_devices 
                WHERE device_id = ? AND pond_id = ?
            """,
                (device_id, pond_id),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "jenis": row[0] if row[0] else "--",
                    "tgl_mulai": row[1] if row[1] else "--",
                    "tgl_panen": row[2] if row[2] else "--",
                }
    except sqlite3.Error as e:
        st.error(f"Error Database ({device_id}/{pond_id}): {e}")
    return None


def calculate_age(tgl_str):
    """Menghitung usia (dalam hari) dari string tanggal 'YYYY-MM-DD'."""
    if not tgl_str or tgl_str == "--":
        return "-- Hari"

    try:
        tgl_start = datetime.strptime(tgl_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        delta = (today - tgl_start).days
        return f"{max(0, delta)} Hari"
    except Exception:
        return "-- Hari"


def cardInfoTanaman(
    device_id="esp-farm-1", pond_id="tanaman", title=None, status=True
):
    meta = get_metadata_by_device(device_id, pond_id)

    if meta:
        jenis = meta["jenis"]
        tgl_up = meta["tgl_mulai"]
        tgl_down = meta["tgl_panen"]
        usia = calculate_age(tgl_up)
    else:
        jenis, tgl_up, tgl_down, usia = "--", "--", "--", "-- Hari"

    icon = ":green[#]" if status else ":red[!]"
    display_title = title if title else device_id

    st.markdown(f"## {display_title} {icon}")
    st.markdown(f"""
    **Device ID:** `{device_id}`  
    **Jenis Tanaman:** {jenis}  
    **Tanggal Tanam:** {tgl_up}  
    **Tanggal Panen:** {tgl_down}  
    **Usia Tanaman:** {usia}
    """)


def cardInfoIkan(
    device_id="esp-ikan-1", pond_id="k1", title=None, status=True
):
    meta = get_metadata_by_device(device_id, pond_id)

    if meta:
        jenis = meta["jenis"]
        tgl_up = meta["tgl_mulai"]
        tgl_down = meta["tgl_panen"]
        usia = calculate_age(tgl_up)
    else:
        jenis, tgl_up, tgl_down, usia = "--", "--", "--", "-- Hari"

    icon = ":green[#]" if status else ":red[!]"
    display_title = title if title else device_id

    st.markdown(f"## {display_title} {icon}")
    st.markdown(f"""
    **Device ID:** `{device_id}`  
    **Jenis Ikan:** {jenis}  
    **Tanggal Tebar:** {tgl_up}  
    **Tanggal Panen:** {tgl_down}  
    **Usia Ikan:** {usia}
    """)
