"""
Smart Travel Planner - Flask backend (REST API) + frontend
Covers: (a) Python backend, (b) Flask routes + HTTP methods, (c) frontend integration
Run:  python app.py   ->  open http://127.0.0.1:5000
"""
import sqlite3
from flask import Flask, jsonify, request, render_template, g

app = Flask(__name__)
DB = "travel.db"

# ---------- Sample data (our "database" of destinations) ----------
# cost_per_day = approx. INR per person per day (stay + food + local travel)
DESTINATIONS = [
    {"id": 1, "name": "Goa", "state": "Goa", "type": "beach", "cost_per_day": 3500,
     "best_season": "Nov-Feb", "places": ["Baga Beach", "Fort Aguada", "Dudhsagar Falls", "Old Goa Churches", "Anjuna Flea Market"]},
    {"id": 2, "name": "Manali", "state": "Himachal Pradesh", "type": "mountain", "cost_per_day": 3000,
     "best_season": "Mar-Jun", "places": ["Solang Valley", "Rohtang Pass", "Hadimba Temple", "Old Manali", "Jogini Falls"]},
    {"id": 3, "name": "Jaipur", "state": "Rajasthan", "type": "heritage", "cost_per_day": 2500,
     "best_season": "Oct-Mar", "places": ["Amber Fort", "Hawa Mahal", "City Palace", "Nahargarh Fort", "Jantar Mantar"]},
    {"id": 4, "name": "Rishikesh", "state": "Uttarakhand", "type": "adventure", "cost_per_day": 2200,
     "best_season": "Sep-Jun", "places": ["River Rafting", "Laxman Jhula", "Triveni Ghat Aarti", "Beatles Ashram", "Bungee Jumping"]},
    {"id": 5, "name": "Kerala (Munnar)", "state": "Kerala", "type": "nature", "cost_per_day": 3200,
     "best_season": "Sep-Mar", "places": ["Tea Gardens", "Eravikulam National Park", "Mattupetty Dam", "Echo Point", "Top Station"]},
    {"id": 6, "name": "Varanasi", "state": "Uttar Pradesh", "type": "spiritual", "cost_per_day": 2000,
     "best_season": "Oct-Mar", "places": ["Ganga Aarti", "Kashi Vishwanath", "Assi Ghat", "Sarnath", "Boat Ride at Sunrise"]},
    {"id": 7, "name": "Leh-Ladakh", "state": "Ladakh", "type": "adventure", "cost_per_day": 4500,
     "best_season": "May-Sep", "places": ["Pangong Lake", "Nubra Valley", "Khardung La", "Leh Palace", "Magnetic Hill"]},
    {"id": 8, "name": "Udaipur", "state": "Rajasthan", "type": "heritage", "cost_per_day": 3000,
     "best_season": "Oct-Mar", "places": ["City Palace", "Lake Pichola", "Saheliyon Ki Bari", "Jag Mandir", "Sajjangarh Fort"]},
]
# Transport cost per person from Delhi (one way, approx INR) - used in the budget estimate
TRANSPORT_FROM_DELHI = {1: 5000, 2: 1500, 3: 700, 4: 600, 5: 6500, 6: 1200, 7: 7000, 8: 1800}


# ---------- Database helpers (SQLite stores bookings) ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS bookings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, email TEXT NOT NULL,
            destination_id INTEGER NOT NULL,
            travellers INTEGER NOT NULL, days INTEGER NOT NULL,
            total_cost INTEGER NOT NULL)""")


def find_destination(dest_id):
    return next((d for d in DESTINATIONS if d["id"] == dest_id), None)


def estimate_cost(dest, travellers, days):
    stay = dest["cost_per_day"] * days * travellers
    transport = TRANSPORT_FROM_DELHI[dest["id"]] * 2 * travellers  # return trip
    return stay + transport


# ---------- Frontend ----------
@app.route("/")
def home():
    return render_template("index.html")


# ---------- API: destinations (GET) ----------
@app.route("/api/destinations", methods=["GET"])
def list_destinations():
    """Optional filter: /api/destinations?type=beach"""
    t = request.args.get("type")
    data = [d for d in DESTINATIONS if not t or d["type"] == t.lower()]
    return jsonify(data), 200


@app.route("/api/destinations/<int:dest_id>", methods=["GET"])
def get_destination(dest_id):
    dest = find_destination(dest_id)
    if not dest:
        return jsonify({"error": "Destination not found"}), 404
    return jsonify(dest), 200


# ---------- API: smart planner (POST) ----------
@app.route("/api/plan", methods=["POST"])
def plan_trip():
    """Body: {"budget": 30000, "days": 4, "travellers": 2, "type": "beach"(optional)}
    Returns destinations that fit the budget, cheapest-fit first, with day-wise itinerary."""
    data = request.get_json(silent=True) or {}
    try:
        budget = int(data["budget"])
        days = int(data["days"])
        travellers = int(data.get("travellers", 1))
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "budget, days (and travellers) must be numbers"}), 400
    if budget <= 0 or days <= 0 or travellers <= 0:
        return jsonify({"error": "values must be greater than 0"}), 400

    wanted = (data.get("type") or "").lower()
    results = []
    for d in DESTINATIONS:
        if wanted and d["type"] != wanted:
            continue
        cost = estimate_cost(d, travellers, days)
        if cost <= budget:
            itinerary = [{"day": i + 1, "visit": d["places"][i % len(d["places"])]} for i in range(days)]
            results.append({"destination": d["name"], "id": d["id"], "type": d["type"],
                            "best_season": d["best_season"], "estimated_cost": cost,
                            "money_left": budget - cost, "itinerary": itinerary})
    results.sort(key=lambda r: r["estimated_cost"], reverse=True)  # best use of budget first
    return jsonify({"count": len(results), "suggestions": results}), 200


# ---------- API: bookings (full CRUD: POST, GET, PUT, DELETE) ----------
@app.route("/api/bookings", methods=["POST"])
def create_booking():
    data = request.get_json(silent=True) or {}
    required = ["name", "email", "destination_id", "travellers", "days"]
    if any(k not in data or data[k] in ("", None) for k in required):
        return jsonify({"error": f"Required fields: {', '.join(required)}"}), 400
    dest = find_destination(int(data["destination_id"]))
    if not dest:
        return jsonify({"error": "Invalid destination_id"}), 404
    travellers, days = int(data["travellers"]), int(data["days"])
    total = estimate_cost(dest, travellers, days)
    db = get_db()
    cur = db.execute("INSERT INTO bookings(name,email,destination_id,travellers,days,total_cost) VALUES(?,?,?,?,?,?)",
                     (data["name"], data["email"], dest["id"], travellers, days, total))
    db.commit()
    return jsonify({"message": "Booking confirmed", "booking_id": cur.lastrowid,
                    "destination": dest["name"], "total_cost": total}), 201


@app.route("/api/bookings", methods=["GET"])
def list_bookings():
    rows = get_db().execute("SELECT * FROM bookings").fetchall()
    out = []
    for r in rows:
        item = dict(r)
        item["destination"] = find_destination(r["destination_id"])["name"]
        out.append(item)
    return jsonify(out), 200


@app.route("/api/bookings/<int:booking_id>", methods=["PUT"])
def update_booking(booking_id):
    data = request.get_json(silent=True) or {}
    db = get_db()
    row = db.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
    if not row:
        return jsonify({"error": "Booking not found"}), 404
    travellers = int(data.get("travellers", row["travellers"]))
    days = int(data.get("days", row["days"]))
    total = estimate_cost(find_destination(row["destination_id"]), travellers, days)
    db.execute("UPDATE bookings SET travellers=?, days=?, total_cost=? WHERE id=?",
               (travellers, days, total, booking_id))
    db.commit()
    return jsonify({"message": "Booking updated", "total_cost": total}), 200


@app.route("/api/bookings/<int:booking_id>", methods=["DELETE"])
def delete_booking(booking_id):
    db = get_db()
    cur = db.execute("DELETE FROM bookings WHERE id=?", (booking_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "Booking not found"}), 404
    return jsonify({"message": "Booking cancelled"}), 200


init_db()

if __name__ == "__main__":
    app.run(debug=True)
