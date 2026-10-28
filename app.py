"""Каркас прототипа «Бронь столиков в ресторане» (ЛР-5).

Архитектура: монолит Flask + серверные шаблоны Jinja2 (ADR-003),
хранилище SQLite в режиме WAL (ADR-001), проверка занятости столика
в одной транзакции BEGIN IMMEDIATE + частичный уникальный индекс (ADR-002).
Реализован сквозной сценарий «Оформление брони» (История 2); остальные
экраны — заглушки по бэклогу ЛР-4.
"""
import os
import re
import secrets
import sqlite3
from datetime import date

from flask import Flask, Response, abort, redirect, render_template, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "reservation.db"))
SLOTS = ["10:00", "12:00", "14:00", "16:00", "18:00", "20:00"]  # слоты по 2 ч, ресторан 10:00–23:00
ACTIVE = ("ОЖИДАЕТ", "ПОДТВЕРЖДЕНА")
ADMIN_HASH = generate_password_hash(os.environ.get("ADMIN_PASSWORD", "admin"))  # НФТ-5: пароль хранится только в виде хеша

app = Flask(__name__)


# ---------- слой данных ----------
def connect():
    # isolation_level=None: транзакциями управляем вручную (нужен BEGIN IMMEDIATE)
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
        -- вторая линия защиты от двойной брони (ADR-002); отменённые брони слот освобождают
        CREATE UNIQUE INDEX IF NOT EXISTS ux_active_slot
            ON bookings(table_id, booking_date, booking_time)
            WHERE status IN ('ОЖИДАЕТ','ПОДТВЕРЖДЕНА');
        -- ускоряет каталог (НФТ-1)
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


# ---------- бизнес-логика (роль «Сервис проверки занятости» с диаграммы последовательностей) ----------
def create_booking(con, table_id, day, slot, guests, name, phone):
    """Возвращает ('ok', номер) | ('busy', None) | ('invalid', текст ошибки)."""
    try:
        d = date.fromisoformat(day)
    except ValueError:
        return "invalid", "Некорректная дата"
    if d < date.today():
        return "invalid", "Нельзя бронировать на прошедшую дату"
    if slot not in SLOTS:
        return "invalid", "Ресторан работает с 10:00 до 23:00: выберите время из списка"
    if not name.strip():
        return "invalid", "Укажите имя"
    if not re.fullmatch(r"\+?\d{10,15}", re.sub(r"[ ()-]", "", phone)):
        return "invalid", "Телефон: от 10 до 15 цифр"
    t = con.execute("SELECT seats FROM tables WHERE id=?", (table_id,)).fetchone()
    if t is None:
        return "invalid", "Такого столика нет"
    if not 1 <= guests <= t["seats"]:
        return "invalid", f"За этим столиком от 1 до {t['seats']} гостей"

    number = "B-" + secrets.token_hex(3).upper()
    con.execute("BEGIN IMMEDIATE")  # блокировка записи: проверка и вставка — одна неделимая операция
    try:
        busy = con.execute(
            "SELECT 1 FROM bookings WHERE table_id=? AND booking_date=? AND booking_time=? "
            "AND status IN ('ОЖИДАЕТ','ПОДТВЕРЖДЕНА')", (table_id, day, slot)).fetchone()
        if busy:
            con.execute("ROLLBACK")
            return "busy", None
        con.execute(
            "INSERT INTO bookings(number,table_id,booking_date,booking_time,guests,name,phone) "
            "VALUES (?,?,?,?,?,?,?)", (number, table_id, day, slot, guests, name.strip(), phone.strip()))
        con.execute("COMMIT")
        return "ok", number
    except Exception:
        con.execute("ROLLBACK")
        raise


# ---------- экраны ----------
def _params():
    day = request.values.get("date") or date.today().isoformat()
    slot = request.values.get("time") or "18:00"
    guests = request.values.get("guests", type=int) or 1
    return day, slot, guests


@app.route("/")
def catalog():  # История 1 / ФТ-1, ФТ-2
    day, slot, guests = _params()
    con = connect()
    tables = free_tables(con, day, slot, guests)
    con.close()
    return render_template("catalog.html", tables=tables, day=day, slot=slot, guests=guests, slots=SLOTS)


@app.route("/booking/<int:table_id>")
def booking_form(table_id):  # форма брони
    day, slot, guests = _params()
    return render_template("booking.html", table_id=table_id, day=day, slot=slot, guests=guests, error=None)


@app.route("/bookings", methods=["POST"])
def booking_create():  # История 2 / ФТ-4, ФТ-5, ФТ-6
    f = request.form
    table_id, guests = int(f.get("table_id", 0)), int(f.get("guests") or 0)
    con = connect()
    status, result = create_booking(con, table_id, f.get("date", ""), f.get("time", ""), guests,
                                    f.get("name", ""), f.get("phone", ""))
    con.close()
    if status == "ok":
        return redirect(url_for("booking_status", number=result), code=303)
    msg = "Столик уже занят на это время — выберите другой" if status == "busy" else result
    return render_template("booking.html", table_id=table_id, day=f.get("date"), slot=f.get("time"),
                           guests=guests, error=msg), (409 if status == "busy" else 400)


@app.route("/status/<number>")
def booking_status(number):  # ФТ-7
    con = connect()
    b = con.execute("SELECT * FROM bookings WHERE number=?", (number,)).fetchone()
    con.close()
    if b is None:
        abort(404)
    return render_template("status.html", b=b)


@app.route("/hall")
def hall():  # ФТ-3: схема зала
    day, slot, _ = _params()
    con = connect()
    free_ids = {t["id"] for t in free_tables(con, day, slot)}
    tables = con.execute("SELECT * FROM tables ORDER BY id").fetchall()
    con.close()
    return render_template("hall.html", tables=tables, free_ids=free_ids, day=day, slot=slot, slots=SLOTS)


def admin_required():
    a = request.authorization
    if not (a and a.username == "admin" and check_password_hash(ADMIN_HASH, a.password or "")):
        abort(Response("Нужна авторизация", 401, {"WWW-Authenticate": 'Basic realm="admin"'}))


@app.route("/admin")
def admin():  # ФТ-10 (заглушка кабинета: список броней)
    admin_required()
    con = connect()
    rows = con.execute("SELECT * FROM bookings ORDER BY booking_date, booking_time").fetchall()
    con.close()
    return render_template("admin.html", bookings=rows)


@app.route("/admin/<int:bid>/<action>", methods=["POST"])
def admin_action(bid, action):  # ФТ-11, ФТ-12
    admin_required()
    if action not in ("confirm", "reject"):
        abort(404)
    new = "ПОДТВЕРЖДЕНА" if action == "confirm" else "ОТКЛОНЕНА"
    con = connect()
    con.execute("UPDATE bookings SET status=? WHERE id=? AND status='ОЖИДАЕТ'", (new, bid))
    con.close()
    return redirect(url_for("admin"), code=303)


init_db()

if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 5000)), debug=bool(os.environ.get("DEBUG")))
