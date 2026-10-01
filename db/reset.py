import sqlite3

# Nama file database target
DB_FILE = "telemetry.db"


def clear_data_only():
    """TIPE 1: Bersihkan semua DATA saja, tabel dan strukturnya TIDAK dihapus."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Ambil semua nama tabel
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE"
        " 'sqlite_%';"
    )
    tables = cursor.fetchall()

    if not tables:
        print("Tidak ada tabel yang ditemukan.")
        conn.close()
        return

    cursor.execute("PRAGMA foreign_keys = OFF;")

    for table_tuple in tables:
        table_name = table_tuple[0]
        cursor.execute(f"DELETE FROM {table_name};")
        print(f"[DATA CLEARED] Isi tabel '{table_name}' berhasil dikosongkan.")

    # Reset counter AUTOINCREMENT jika tabel sqlite_sequence ada
    try:
        cursor.execute("DELETE FROM sqlite_sequence;")
    except sqlite3.OperationalError:
        pass  # Abaikan jika tabel sequence belum dibuat

    conn.commit()
    cursor.execute("PRAGMA foreign_keys = ON;")
    conn.close()

    print("\n✅ [OK] Semua data berhasil dikosongkan! (Struktur tabel aman)\n")


def drop_all_tables():
    """TIPE 2: Bersihkan SEMUANYA (Hapus semua tabel beserta isinya total)."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE"
        " 'sqlite_%';"
    )
    tables = cursor.fetchall()

    if not tables:
        print("Tidak ada tabel yang ditemukan.")
        conn.close()
        return

    cursor.execute("PRAGMA foreign_keys = OFF;")

    for table_tuple in tables:
        table_name = table_tuple[0]
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        print(f"[TABLE DROPPED] Tabel '{table_name}' berhasil dihapus.")

    conn.commit()
    cursor.execute("PRAGMA foreign_keys = ON;")
    conn.close()

    print("\n✅ [OK] Semua tabel dan data berhasil dihapus total!\n")


if __name__ == "__main__":
    print("=== PILIH MODE RESET DATABASE ===")
    print("1. Bersihkan DATA saja (Tabel tetap ada)")
    print("2. Bersihkan SEMUANYA (Hapus semua tabel & data)")

    pilihan = input("Masukkan pilihan (1/2): ").strip()

    if pilihan == "1":
        clear_data_only()
    elif pilihan == "2":
        drop_all_tables()
    else:
        print("Pilihan tidak valid! Batal melakukan reset.")
