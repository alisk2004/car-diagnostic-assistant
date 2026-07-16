import json
from collections import defaultdict
from datetime import datetime

from flask import Flask, jsonify, render_template, request

from database import get_connection, init_db, is_seeded
from diagnosis_engine import diagnose

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/symptoms")
def api_symptoms():
    conn = get_connection()
    rows = conn.execute("SELECT id, name, category FROM symptoms ORDER BY category, name").fetchall()
    conn.close()

    grouped = defaultdict(list)
    for row in rows:
        grouped[row["category"]].append({"id": row["id"], "name": row["name"]})
    return jsonify(grouped)


@app.route("/api/dtc-codes")
def api_dtc_codes():
    query = request.args.get("query", "").strip()
    conn = get_connection()
    if query:
        like = f"%{query}%"
        rows = conn.execute(
            "SELECT id, code, description, category FROM dtc_codes "
            "WHERE code LIKE ? OR description LIKE ? ORDER BY code",
            (like, like),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, code, description, category FROM dtc_codes ORDER BY code"
        ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/api/diagnose", methods=["POST"])
def api_diagnose():
    payload = request.get_json(silent=True) or {}
    symptom_ids = payload.get("symptom_ids", [])
    dtc_codes = payload.get("dtc_codes", [])
    vehicle = payload.get("vehicle", {}) or {}

    if not symptom_ids and not dtc_codes:
        return jsonify({"error": "Provide at least one symptom or DTC code."}), 400

    conn = get_connection()
    results = diagnose(symptom_ids, dtc_codes, conn=conn)

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO diagnostic_sessions "
        "(vehicle_make, vehicle_model, vehicle_year, created_at, input_symptoms_json, input_codes_json) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            vehicle.get("make"),
            vehicle.get("model"),
            vehicle.get("year"),
            datetime.utcnow().isoformat(),
            json.dumps(symptom_ids),
            json.dumps(dtc_codes),
        ),
    )
    session_id = cur.lastrowid

    for result in results:
        cur.execute(
            "INSERT INTO diagnostic_results "
            "(session_id, fault_id, confidence, rank, matched_symptoms_json, matched_codes_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                session_id,
                result["fault_id"],
                result["confidence"],
                result["rank"],
                json.dumps(result["matched_symptoms"]),
                json.dumps(result["matched_codes"]),
            ),
        )
    conn.commit()
    conn.close()

    return jsonify({"session_id": session_id, "results": results})


@app.route("/api/history")
def api_history():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, vehicle_make, vehicle_model, vehicle_year, created_at FROM diagnostic_sessions "
        "ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/api/history/<int:session_id>")
def api_history_detail(session_id):
    conn = get_connection()
    session = conn.execute(
        "SELECT * FROM diagnostic_sessions WHERE id = ?", (session_id,)
    ).fetchone()
    if session is None:
        conn.close()
        return jsonify({"error": "Session not found"}), 404

    results = conn.execute(
        "SELECT dr.confidence, dr.rank, dr.matched_symptoms_json, dr.matched_codes_json, "
        "f.name, f.description, f.severity, f.recommended_action "
        "FROM diagnostic_results dr JOIN faults f ON f.id = dr.fault_id "
        "WHERE dr.session_id = ? ORDER BY dr.rank",
        (session_id,),
    ).fetchall()
    conn.close()

    session_dict = dict(session)
    session_dict["input_symptoms"] = json.loads(session_dict.pop("input_symptoms_json"))
    session_dict["input_codes"] = json.loads(session_dict.pop("input_codes_json"))

    result_dicts = []
    for row in results:
        result = dict(row)
        result["matched_symptoms"] = json.loads(result.pop("matched_symptoms_json"))
        result["matched_codes"] = json.loads(result.pop("matched_codes_json"))
        result_dicts.append(result)
    session_dict["results"] = result_dicts
    return jsonify(session_dict)


def ensure_ready():
    init_db()
    if not is_seeded():
        import seed_data
        seed_data.seed()


if __name__ == "__main__":
    ensure_ready()
    app.run(debug=True)
