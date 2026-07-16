import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from diagnosis_engine import diagnose

SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA_PATH.read_text())

    cur = connection.cursor()
    # Symptoms
    cur.execute("INSERT INTO symptoms (id, name, category) VALUES (1, 'Rough idle', 'Engine')")
    cur.execute("INSERT INTO symptoms (id, name, category) VALUES (2, 'Engine stalls while driving', 'Engine')")
    cur.execute("INSERT INTO symptoms (id, name, category) VALUES (3, 'Squealing when braking', 'Brakes')")
    # DTC codes
    cur.execute("INSERT INTO dtc_codes (id, code, description, category) VALUES (1, 'P0300', 'Random misfire', 'Ignition')")
    cur.execute("INSERT INTO dtc_codes (id, code, description, category) VALUES (2, 'P0420', 'Catalyst efficiency', 'Emissions')")
    # Faults
    cur.execute(
        "INSERT INTO faults (id, name, description, severity, recommended_action) "
        "VALUES (1, 'Worn Spark Plugs', 'desc', 'Medium', 'Replace plugs')"
    )
    cur.execute(
        "INSERT INTO faults (id, name, description, severity, recommended_action) "
        "VALUES (2, 'Worn Brake Pads', 'desc', 'Medium', 'Replace pads')"
    )
    # Rules: fault 1 (spark plugs) tied to symptoms 1, 2 and code P0300
    cur.execute("INSERT INTO fault_symptoms (fault_id, symptom_id, weight) VALUES (1, 1, 2)")
    cur.execute("INSERT INTO fault_symptoms (fault_id, symptom_id, weight) VALUES (1, 2, 1)")
    cur.execute("INSERT INTO fault_dtc_codes (fault_id, dtc_code_id, weight) VALUES (1, 1, 3)")
    # Rules: fault 2 (brake pads) tied to symptom 3 only
    cur.execute("INSERT INTO fault_symptoms (fault_id, symptom_id, weight) VALUES (2, 3, 3)")
    connection.commit()
    yield connection
    connection.close()


def test_no_input_returns_no_results(conn):
    assert diagnose([], [], conn=conn) == []


def test_symptom_only_partial_match(conn):
    results = diagnose(symptom_ids=[1], dtc_codes=[], conn=conn)
    assert len(results) == 1
    assert results[0]["name"] == "Worn Spark Plugs"
    # matched weight 2 out of total 6 (2+1+3) = 33.3%
    assert results[0]["confidence"] == pytest.approx(33.3, abs=0.1)
    assert results[0]["matched_symptoms"] == ["Rough idle"]
    assert results[0]["matched_codes"] == []


def test_symptom_and_code_combine_for_higher_confidence(conn):
    results = diagnose(symptom_ids=[1, 2], dtc_codes=["P0300"], conn=conn)
    assert len(results) == 1
    # matched weight 2+1+3 = 6 out of total 6 = 100%
    assert results[0]["confidence"] == 100.0
    assert set(results[0]["matched_symptoms"]) == {"Rough idle", "Engine stalls while driving"}
    assert results[0]["matched_codes"] == ["P0300"]


def test_unrelated_fault_not_matched(conn):
    results = diagnose(symptom_ids=[1], dtc_codes=[], conn=conn)
    names = [r["name"] for r in results]
    assert "Worn Brake Pads" not in names


def test_dtc_code_lookup_is_case_insensitive(conn):
    results = diagnose(symptom_ids=[], dtc_codes=["p0300"], conn=conn)
    assert len(results) == 1
    assert results[0]["name"] == "Worn Spark Plugs"


def test_results_are_ranked_by_confidence_descending(conn):
    results = diagnose(symptom_ids=[1, 3], dtc_codes=[], conn=conn)
    assert len(results) == 2
    assert results[0]["confidence"] >= results[1]["confidence"]
    assert results[0]["rank"] == 1
    assert results[1]["rank"] == 2
