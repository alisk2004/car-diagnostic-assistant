"""Rule-based expert system that scores candidate faults against the
symptoms and OBD-II codes a user reports.

For each fault, every linked symptom/code carries a weight (how strong a
signal it is). Confidence = (sum of weights matched) / (sum of all weights
defined for that fault) * 100. This keeps the reasoning fully explainable:
you can always point to exactly which symptoms/codes drove a given score.
"""

from database import get_connection


def diagnose(symptom_ids=None, dtc_codes=None, conn=None):
    symptom_ids = {int(s) for s in (symptom_ids or [])}
    dtc_codes = {c.strip().upper() for c in (dtc_codes or []) if c and c.strip()}

    own_conn = conn is None
    if own_conn:
        conn = get_connection()

    matched_code_ids = set()
    if dtc_codes:
        placeholders = ",".join("?" * len(dtc_codes))
        rows = conn.execute(
            f"SELECT id FROM dtc_codes WHERE code IN ({placeholders})", tuple(dtc_codes)
        ).fetchall()
        matched_code_ids = {row["id"] for row in rows}

    faults = conn.execute("SELECT * FROM faults").fetchall()
    fs_rows = conn.execute(
        "SELECT fs.fault_id, fs.symptom_id, fs.weight, s.name "
        "FROM fault_symptoms fs JOIN symptoms s ON s.id = fs.symptom_id"
    ).fetchall()
    fc_rows = conn.execute(
        "SELECT fc.fault_id, fc.dtc_code_id, fc.weight, d.code "
        "FROM fault_dtc_codes fc JOIN dtc_codes d ON d.id = fc.dtc_code_id"
    ).fetchall()

    if own_conn:
        conn.close()

    fault_by_id = {f["id"]: f for f in faults}
    totals = {f["id"]: 0 for f in faults}
    matched = {f["id"]: 0 for f in faults}
    matched_symptoms = {f["id"]: [] for f in faults}
    matched_codes = {f["id"]: [] for f in faults}

    for row in fs_rows:
        totals[row["fault_id"]] += row["weight"]
        if row["symptom_id"] in symptom_ids:
            matched[row["fault_id"]] += row["weight"]
            matched_symptoms[row["fault_id"]].append(row["name"])

    for row in fc_rows:
        totals[row["fault_id"]] += row["weight"]
        if row["dtc_code_id"] in matched_code_ids:
            matched[row["fault_id"]] += row["weight"]
            matched_codes[row["fault_id"]].append(row["code"])

    results = []
    for fault_id, total in totals.items():
        matched_weight = matched[fault_id]
        if matched_weight <= 0 or total <= 0:
            continue
        fault = fault_by_id[fault_id]
        results.append({
            "fault_id": fault_id,
            "name": fault["name"],
            "description": fault["description"],
            "severity": fault["severity"],
            "recommended_action": fault["recommended_action"],
            "confidence": round((matched_weight / total) * 100, 1),
            "matched_symptoms": matched_symptoms[fault_id],
            "matched_codes": matched_codes[fault_id],
        })

    results.sort(key=lambda r: r["confidence"], reverse=True)
    for rank, result in enumerate(results, start=1):
        result["rank"] = rank

    return results
