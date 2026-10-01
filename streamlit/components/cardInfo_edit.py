import os
import sqlite3
from datetime import date, datetime
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "db", "telemetry.db")


def parse_date(date_str):
    """Konversi string YYYY-MM-DD ke datetime.date.

    Kembalikan None jika format invalid/kosong.
    """
    if not date_str or date_str == "--":
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def get_metadata_by_device(device_id, pond_id="k1"):
    """Ambil metadata dari SQLite berdasarkan device_id dan pond_id."""
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
                    "jenis": row[0] if row[0] != "--" else "",
                    "tgl_mulai": row[1],
                    "tgl_panen": row[2],
                }
    except Exception:
        pass
    return None


def calculate_age(tgl_str):
    """Hitung usia (hari) dari tanggal YYYY-MM-DD."""
    if not tgl_str or tgl_str == "--":
        return "-- Hari"
    try:
        tgl_start = datetime.strptime(tgl_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        delta = (today - tgl_start).days
        return f"{max(0, delta)} Hari"
    except Exception:
        return "-- Hari"


def save_plant_fish_info(device_id, pond_id, jenis, tgl_mulai, tgl_panen):
    """Simpan atau update data metadata di SQLite."""
    val_jenis = jenis.strip() if jenis and jenis.strip() else "--"
    val_tgl_mulai = str(tgl_mulai) if tgl_mulai else "--"
    val_tgl_panen = str(tgl_panen) if tgl_panen else "--"

    # Pastikan folder db ada
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS metadata_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            pond_id TEXT NOT NULL DEFAULT 'k1',
            jenis TEXT NOT NULL,
            tgl_mulai TEXT NOT NULL,
            tgl_panen TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(device_id, pond_id)
        )
        """)

        cursor.execute(
            """
        INSERT INTO metadata_devices (device_id, pond_id, jenis, tgl_mulai, tgl_panen, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(device_id, pond_id) DO UPDATE SET
            jenis = excluded.jenis,
            tgl_mulai = excluded.tgl_mulai,
            tgl_panen = excluded.tgl_panen,
            updated_at = excluded.updated_at
        """,
            (
                device_id,
                pond_id,
                val_jenis,
                val_tgl_mulai,
                val_tgl_panen,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )


@st.dialog("Notifikasi")
def send_to_db(device_id, pond_id, new_jenis, new_tgl_up, new_tgl_down):
    disp_jenis = new_jenis if new_jenis else "--"
    disp_tgl_up = str(new_tgl_up) if new_tgl_up else "--"
    disp_tgl_down = str(new_tgl_down) if new_tgl_down else "--"

    st.success(f"Konfirmasi perubahan data `{device_id}` ({pond_id}):")
    st.write(f"**Jenis:** {disp_jenis}")
    st.write(f"**Tanggal Mulai/Tebar:** {disp_tgl_up}")
    st.write(f"**Tanggal Panen:** {disp_tgl_down}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Done", use_container_width=True, type="primary"):
            save_plant_fish_info(
                device_id, pond_id, new_jenis, new_tgl_up, new_tgl_down
            )
            st.toast("Data berhasil disimpan!", icon="✅")
            st.rerun()

    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()


# ================= EDIT WIDGETS =================
def cardInfoTanaman_edit(
    device_id="esp-farm-1", pond_id="tanaman", title=None
):
    display_title = title if title else device_id
    st.markdown(f"## Edit Info Tanaman ({display_title})")

    current_data = get_metadata_by_device(device_id, pond_id)

    default_jenis = current_data["jenis"] if current_data else ""
    default_tgl_up = (
        parse_date(current_data["tgl_mulai"]) if current_data else None
    )
    default_tgl_down = (
        parse_date(current_data["tgl_panen"]) if current_data else None
    )

    new_jenis = st.text_input(
        "Jenis Tanaman",
        value=default_jenis,
        placeholder="--",
        key=f"edit_jenis_tanam_{device_id}_{pond_id}",
    )
    new_tgl_up = st.date_input(
        "Tanggal Tanam",
        value=default_tgl_up,
        key=f"edit_tgl_up_tanam_{device_id}_{pond_id}",
    )
    new_tgl_down = st.date_input(
        "Tanggal Panen",
        value=default_tgl_down,
        key=f"edit_tgl_down_tanam_{device_id}_{pond_id}",
    )

    if st.button("Simpan Perubahan", key=f"btn_save_tanam_{device_id}_{pond_id}"):
        send_to_db(device_id, pond_id, new_jenis, new_tgl_up, new_tgl_down)


def cardInfoIkan_edit(device_id="esp-ikan-1", pond_id="k1", title=None):
    display_title = title if title else f"{device_id} ({pond_id})"
    st.markdown(f"## Edit Info Ikan ({display_title})")

    current_data = get_metadata_by_device(device_id, pond_id)

    default_jenis = current_data["jenis"] if current_data else ""
    default_tgl_up = (
        parse_date(current_data["tgl_mulai"]) if current_data else None
    )
    default_tgl_down = (
        parse_date(current_data["tgl_panen"]) if current_data else None
    )

    new_jenis_ikan = st.text_input(
        "Jenis Ikan",
        value=default_jenis,
        placeholder="--",
        key=f"edit_jenis_ikan_{device_id}_{pond_id}",
    )
    new_tgl_tebar = st.date_input(
        "Tanggal Tebar",
        value=default_tgl_up,
        key=f"edit_tgl_tebar_{device_id}_{pond_id}",
    )
    new_tgl_panen = st.date_input(
        "Tanggal Panen",
        value=default_tgl_down,
        key=f"edit_tgl_panen_{device_id}_{pond_id}",
    )

    if st.button("Simpan Perubahan", key=f"btn_save_ikan_{device_id}_{pond_id}"):
        send_to_db(
            device_id, pond_id, new_jenis_ikan, new_tgl_tebar, new_tgl_panen
        )


# ================= DISPLAY CARD WIDGETS =================
def cardInfoTanaman(
    device_id="esp-farm-1", pond_id="tanaman", title=None, status=True
):
    meta = get_metadata_by_device(device_id, pond_id)

    if meta:
        jenis = meta["jenis"] if meta["jenis"] else "--"
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
        jenis = meta["jenis"] if meta["jenis"] else "--"
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
