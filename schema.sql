-- Car Diagnostic Assistant database schema

CREATE TABLE IF NOT EXISTS symptoms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dtc_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    category TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS faults (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
    recommended_action TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fault_symptoms (
    fault_id INTEGER NOT NULL REFERENCES faults(id),
    symptom_id INTEGER NOT NULL REFERENCES symptoms(id),
    weight INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (fault_id, symptom_id)
);

CREATE TABLE IF NOT EXISTS fault_dtc_codes (
    fault_id INTEGER NOT NULL REFERENCES faults(id),
    dtc_code_id INTEGER NOT NULL REFERENCES dtc_codes(id),
    weight INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (fault_id, dtc_code_id)
);

CREATE TABLE IF NOT EXISTS diagnostic_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_make TEXT,
    vehicle_model TEXT,
    vehicle_year TEXT,
    created_at TEXT NOT NULL,
    input_symptoms_json TEXT NOT NULL,
    input_codes_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS diagnostic_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES diagnostic_sessions(id),
    fault_id INTEGER NOT NULL REFERENCES faults(id),
    confidence REAL NOT NULL,
    rank INTEGER NOT NULL,
    matched_symptoms_json TEXT NOT NULL DEFAULT '[]',
    matched_codes_json TEXT NOT NULL DEFAULT '[]'
);
