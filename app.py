from flask import Flask, render_template, request, jsonify
import json, os

app = Flask(__name__)
DATA = os.path.join(os.path.dirname(__file__), "data", "tables.json")
BOOKINGS = []  # Временная заглушка вместо БД (см. ADR-001)

def load_tables():
    if not os.path.exists(DATA): return []
    with open(DATA, encoding="utf-8") as f: return json.load(f)

@app.route("/")
def catalog(): return render_template("catalog.html", tables=load_tables())

@app.route("/booking/<int:table_id>")
def booking(table_id): return render_template("booking.html")

@app.route("/hall")
def hall(): return render_template("hall.html")

@app.route("/admin")
def admin(): return render_template("admin.html", bookings=BOOKINGS)

@app.route("/api/bookings", methods=["POST"])
def create_booking():
    data = request.json
    number = len(BOOKINGS) + 1
    BOOKINGS.append({**data, "number": number, "status": "ОЖИДАЕТ"})
    return jsonify({"number": number, "status": "ОЖИДАЕТ"}), 201

if __name__ == "__main__": app.run(debug=True)
