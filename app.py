import os
from datetime import date

from flask import Flask, Response, abort, redirect, render_template, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import connect, free_tables, init_db
from services import SLOTS, create_booking

app = Flask(__name__)
ADMIN_HASH = generate_password_hash(os.environ.get("ADMIN_PASSWORD", "admin"))

def _params():
    day = request.values.get("date") or date.today().isoformat()
    slot = request.values.get("time") or "18:00"
    guests = request.values.get("guests", type=int) or 1
    return day, slot, guests

@app.route("/")
def catalog():
    day, slot, guests = _params()
    con = connect()
    tables = free_tables(con, day, slot, guests)
    con.close()
    return render_template("catalog.html", tables=tables, day=day, slot=slot, guests=guests, slots=SLOTS)

@app.route("/booking/<int:table_id>")
def booking_form(table_id):
    day, slot, guests = _params()
    return render_template("booking.html", table_id=table_id, day=day, slot=slot, guests=guests, error=None)

@app.route("/bookings", methods=["POST"])
def booking_create():
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
def booking_status(number):
    con = connect()
    b = con.execute("SELECT * FROM bookings WHERE number=?", (number,)).fetchone()
    con.close()
    if b is None:
        abort(404)
    return render_template("status.html", b=b)

@app.route("/hall")
def hall():
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
def admin():
    admin_required()
    con = connect()
    rows = con.execute("SELECT * FROM bookings ORDER BY booking_date, booking_time").fetchall()
    con.close()
    return render_template("admin.html", bookings=rows)

@app.route("/admin/<int:bid>/<action>", methods=["POST"])
def admin_action(bid, action):
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
