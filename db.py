import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "reservation.db"))

def connect():
    con = sqlite3.connect(DB_PATH, timeout=10, isolation_level=None)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = connect()
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS tables(
            id INTEGER PRIMARY KEY, seats INTEGER NOT NULL, zone TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS bookings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT UNIQUE NOT NULL,
            table_id INTEGER NOT NULL REFERENCES tables(id),
            booking_date TEXT NOT NULL, booking_time TEXT NOT NULL,
            guests INTEGER NOT NULL, name TEXT NOT NULL, phone TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ОЖИДАЕТ');
        CREATE UNIQUE INDEX IF NOT EXISTS ux_active_slot
            ON bookings(table_id, booking_date, booking_time)
            WHERE status IN ('ОЖИДАЕТ','ПОДТВЕРЖДЕНА');
        CREATE INDEX IF NOT EXISTS ix_bookings_date ON bookings(booking_date, booking_time, status);
        """
    )
    if con.execute("SELECT COUNT(*) FROM tables").fetchone()[0] == 0:
        seed = [(1, 2, "у окна"), (2, 4, "около входа"), (3, 6, "по центру зала"), (4, 8, "у окна"),
                (5, 2, "у окна"), (6, 4, "около входа"), (7, 6, "по центру зала"), (8, 4, "у окна")]
        con.executemany("INSERT INTO tables VALUES (?,?,?)", seed)
    con.close()

def free_tables(con, day, slot, guests=1):
    return con.execute(
        """SELECT * FROM tables t WHERE t.seats >= ? AND NOT EXISTS (
               SELECT 1 FROM bookings b WHERE b.table_id = t.id AND b.booking_date = ?
               AND b.booking_time = ? AND b.status IN ('ОЖИДАЕТ','ПОДТВЕРЖДЕНА'))
           ORDER BY t.id""", (guests, day, slot)).fetchall()
