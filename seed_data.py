"""Populates the database with reference symptoms, OBD-II codes, faults,
and the weighted rules that link them for the diagnosis engine."""

from database import get_connection, init_db, is_seeded

SYMPTOMS = [
    ("Engine won't start", "Engine"),
    ("Engine cranks but won't start", "Engine"),
    ("Rough idle", "Engine"),
    ("Engine stalls while driving", "Engine"),
    ("Loss of power or acceleration", "Engine"),
    ("Check engine light is on", "Engine"),
    ("Engine overheating", "Cooling"),
    ("Knocking or ticking noise from engine", "Engine"),
    ("Vehicle uses more fuel than usual", "Engine"),
    ("Dashboard lights flicker or dim", "Electrical"),
    ("Clicking noise when starting", "Electrical"),
    ("Battery warning light on", "Electrical"),
    ("Slow engine crank", "Electrical"),
    ("Squealing or grinding noise when braking", "Brakes"),
    ("Vehicle pulls to one side when braking", "Brakes"),
    ("Soft or spongy brake pedal", "Brakes"),
    ("Longer stopping distance", "Brakes"),
    ("Slipping gears or delayed shifting", "Transmission"),
    ("Reddish fluid leaking under the car", "Transmission"),
    ("Jerking or shuddering when shifting", "Transmission"),
    ("Steam or smoke from under the hood", "Cooling"),
    ("Sweet smell from engine bay", "Cooling"),
    ("Rotten egg smell from exhaust", "Exhaust"),
    ("Excessive exhaust smoke", "Exhaust"),
]

DTC_CODES = [
    ("P0100", "Mass or Volume Air Flow Circuit Malfunction", "Fuel/Air"),
    ("P0101", "Mass or Volume Air Flow Circuit Range/Performance", "Fuel/Air"),
    ("P0113", "Intake Air Temperature Circuit High Input", "Fuel/Air"),
    ("P0128", "Coolant Thermostat Malfunction", "Cooling"),
    ("P0171", "System Too Lean (Bank 1)", "Fuel/Air"),
    ("P0172", "System Too Rich (Bank 1)", "Fuel/Air"),
    ("P0174", "System Too Lean (Bank 2)", "Fuel/Air"),
    ("P0217", "Engine Overheat Condition", "Cooling"),
    ("P0300", "Random/Multiple Cylinder Misfire Detected", "Ignition"),
    ("P0301", "Cylinder 1 Misfire Detected", "Ignition"),
    ("P0302", "Cylinder 2 Misfire Detected", "Ignition"),
    ("P0303", "Cylinder 3 Misfire Detected", "Ignition"),
    ("P0304", "Cylinder 4 Misfire Detected", "Ignition"),
    ("P0325", "Knock Sensor Circuit Malfunction", "Sensors"),
    ("P0335", "Crankshaft Position Sensor Circuit Malfunction", "Sensors"),
    ("P0340", "Camshaft Position Sensor Circuit Malfunction", "Sensors"),
    ("P0401", "Exhaust Gas Recirculation Flow Insufficient", "Emissions"),
    ("P0420", "Catalyst System Efficiency Below Threshold (Bank 1)", "Emissions"),
    ("P0430", "Catalyst System Efficiency Below Threshold (Bank 2)", "Emissions"),
    ("P0440", "Evaporative Emission Control System Malfunction", "Emissions"),
    ("P0442", "EVAP System Leak Detected (Small Leak)", "Emissions"),
    ("P0455", "EVAP System Leak Detected (Large Leak)", "Emissions"),
    ("P0500", "Vehicle Speed Sensor Malfunction", "Sensors"),
    ("P0562", "System Voltage Low", "Electrical"),
    ("P0563", "System Voltage High", "Electrical"),
    ("P0606", "ECM/PCM Processor Fault", "Electrical"),
    ("P0700", "Transmission Control System Malfunction", "Transmission"),
    ("P0715", "Input/Turbine Speed Sensor Circuit Malfunction", "Transmission"),
    ("P0730", "Incorrect Gear Ratio", "Transmission"),
]

# Each fault links to symptoms and DTC codes with an integer weight (higher =
# stronger evidence). The engine sums matched weights against the fault's
# total possible weight to compute a confidence percentage.
FAULTS = [
    {
        "name": "Worn or Fouled Spark Plugs",
        "description": "Spark plugs are worn, fouled, or gapped incorrectly, causing incomplete combustion.",
        "severity": "Medium",
        "recommended_action": "Inspect and replace spark plugs; check ignition coils if plugs look fine.",
        "symptoms": [("Rough idle", 2), ("Loss of power or acceleration", 2),
                     ("Engine stalls while driving", 1), ("Check engine light is on", 1),
                     ("Vehicle uses more fuel than usual", 2)],
        "codes": [("P0300", 3), ("P0301", 2), ("P0302", 2), ("P0303", 2), ("P0304", 2)],
    },
    {
        "name": "Failing Ignition Coil",
        "description": "One or more ignition coils are failing to deliver a consistent spark.",
        "severity": "Medium",
        "recommended_action": "Test and replace the faulty ignition coil(s).",
        "symptoms": [("Rough idle", 2), ("Engine stalls while driving", 2), ("Check engine light is on", 1)],
        "codes": [("P0300", 2), ("P0301", 3), ("P0302", 3), ("P0303", 3), ("P0304", 3)],
    },
    {
        "name": "Weak or Dying Battery",
        "description": "The battery is losing charge or can no longer hold a full charge.",
        "severity": "Low",
        "recommended_action": "Test battery voltage and load capacity; replace the battery if it fails.",
        "symptoms": [("Slow engine crank", 3), ("Clicking noise when starting", 2),
                     ("Dashboard lights flicker or dim", 2), ("Battery warning light on", 2),
                     ("Engine won't start", 2)],
        "codes": [("P0562", 2)],
    },
    {
        "name": "Failing Alternator",
        "description": "The alternator is not adequately recharging the battery while the engine runs.",
        "severity": "Medium",
        "recommended_action": "Test alternator output voltage; replace the alternator if charging is low.",
        "symptoms": [("Dashboard lights flicker or dim", 3), ("Battery warning light on", 3),
                     ("Slow engine crank", 1), ("Engine stalls while driving", 1)],
        "codes": [("P0562", 2), ("P0563", 1)],
    },
    {
        "name": "Faulty Starter Motor",
        "description": "The starter motor or solenoid is failing to turn the engine over.",
        "severity": "Medium",
        "recommended_action": "Inspect and test the starter motor and solenoid; replace if faulty.",
        "symptoms": [("Clicking noise when starting", 3), ("Engine cranks but won't start", 2),
                     ("Engine won't start", 2)],
        "codes": [],
    },
    {
        "name": "Clogged Fuel Filter",
        "description": "A clogged fuel filter is restricting fuel flow to the engine.",
        "severity": "Medium",
        "recommended_action": "Replace the fuel filter and inspect the fuel system for contamination.",
        "symptoms": [("Loss of power or acceleration", 2), ("Engine stalls while driving", 2),
                     ("Rough idle", 1), ("Engine cranks but won't start", 1)],
        "codes": [("P0171", 2), ("P0174", 1)],
    },
    {
        "name": "Failing Fuel Pump",
        "description": "The fuel pump cannot maintain adequate fuel pressure.",
        "severity": "High",
        "recommended_action": "Test fuel pressure; replace the fuel pump if pressure is below spec.",
        "symptoms": [("Engine cranks but won't start", 2), ("Engine stalls while driving", 2),
                     ("Loss of power or acceleration", 2)],
        "codes": [("P0171", 1), ("P0174", 1)],
    },
    {
        "name": "Low Engine Oil or Oil Leak",
        "description": "Engine oil level is low or leaking, risking severe engine wear.",
        "severity": "Critical",
        "recommended_action": "Check oil level immediately, inspect for leaks, and top up or repair before driving further.",
        "symptoms": [("Knocking or ticking noise from engine", 3), ("Engine overheating", 1),
                     ("Excessive exhaust smoke", 2)],
        "codes": [],
    },
    {
        "name": "Low Coolant or Coolant Leak",
        "description": "Coolant level is low or leaking, reducing the engine's ability to regulate temperature.",
        "severity": "High",
        "recommended_action": "Check coolant level, inspect hoses and radiator for leaks, and refill coolant.",
        "symptoms": [("Engine overheating", 3), ("Steam or smoke from under the hood", 3),
                     ("Sweet smell from engine bay", 2)],
        "codes": [("P0217", 2), ("P0128", 1)],
    },
    {
        "name": "Faulty Thermostat",
        "description": "The thermostat is stuck open or closed, disrupting engine temperature regulation.",
        "severity": "Medium",
        "recommended_action": "Replace the thermostat if it is stuck open or closed.",
        "symptoms": [("Engine overheating", 2)],
        "codes": [("P0128", 3), ("P0217", 1)],
    },
    {
        "name": "Failing Water Pump",
        "description": "The water pump is no longer circulating coolant effectively.",
        "severity": "High",
        "recommended_action": "Inspect the water pump for leaks or bearing wear; replace if faulty.",
        "symptoms": [("Engine overheating", 2), ("Steam or smoke from under the hood", 2),
                     ("Sweet smell from engine bay", 1)],
        "codes": [("P0217", 1)],
    },
    {
        "name": "Worn Brake Pads",
        "description": "Brake pads are worn thin and need replacement.",
        "severity": "Medium",
        "recommended_action": "Inspect brake pad thickness and replace worn pads.",
        "symptoms": [("Squealing or grinding noise when braking", 3), ("Longer stopping distance", 1)],
        "codes": [],
    },
    {
        "name": "Warped Brake Rotors",
        "description": "Brake rotors are warped, causing uneven braking.",
        "severity": "Medium",
        "recommended_action": "Inspect rotors for warping and resurface or replace as needed.",
        "symptoms": [("Vehicle pulls to one side when braking", 2), ("Squealing or grinding noise when braking", 1)],
        "codes": [],
    },
    {
        "name": "Low or Leaking Brake Fluid",
        "description": "Brake fluid is low or leaking, reducing braking effectiveness.",
        "severity": "Critical",
        "recommended_action": "Check brake fluid level and inspect for leaks; have the brake system inspected immediately.",
        "symptoms": [("Soft or spongy brake pedal", 3), ("Longer stopping distance", 2)],
        "codes": [],
    },
    {
        "name": "Faulty Oxygen (O2) Sensor",
        "description": "The oxygen sensor is giving inaccurate readings, throwing off the fuel mixture.",
        "severity": "Medium",
        "recommended_action": "Test and replace the faulty oxygen sensor.",
        "symptoms": [("Vehicle uses more fuel than usual", 2), ("Check engine light is on", 1), ("Rough idle", 1)],
        "codes": [("P0171", 2), ("P0172", 2), ("P0174", 1)],
    },
    {
        "name": "Failing Catalytic Converter",
        "description": "The catalytic converter's efficiency has dropped below acceptable limits.",
        "severity": "High",
        "recommended_action": "Inspect the catalytic converter and exhaust system; replace if efficiency is below threshold.",
        "symptoms": [("Loss of power or acceleration", 1), ("Rotten egg smell from exhaust", 3),
                     ("Check engine light is on", 1)],
        "codes": [("P0420", 3), ("P0430", 3)],
    },
    {
        "name": "Vacuum Leak (Intake)",
        "description": "An intake vacuum leak is letting unmetered air into the engine.",
        "severity": "Medium",
        "recommended_action": "Inspect intake hoses and gaskets for cracks or leaks and repair.",
        "symptoms": [("Rough idle", 2), ("Engine stalls while driving", 1), ("Vehicle uses more fuel than usual", 1)],
        "codes": [("P0171", 2), ("P0174", 2), ("P0101", 1)],
    },
    {
        "name": "Worn Transmission Fluid or Failing Transmission",
        "description": "Transmission fluid is degraded or the transmission itself is failing.",
        "severity": "High",
        "recommended_action": "Check transmission fluid level and condition; have the transmission inspected.",
        "symptoms": [("Slipping gears or delayed shifting", 3), ("Reddish fluid leaking under the car", 2),
                     ("Jerking or shuddering when shifting", 2)],
        "codes": [("P0700", 2), ("P0715", 1), ("P0730", 2)],
    },
    {
        "name": "Faulty Mass Airflow (MAF) Sensor",
        "description": "The mass airflow sensor is sending incorrect readings to the engine computer.",
        "severity": "Medium",
        "recommended_action": "Clean or replace the mass airflow sensor.",
        "symptoms": [("Rough idle", 1), ("Loss of power or acceleration", 1), ("Vehicle uses more fuel than usual", 1)],
        "codes": [("P0100", 3), ("P0101", 2)],
    },
    {
        "name": "Loose or Damaged Gas Cap (EVAP Leak)",
        "description": "A loose or damaged gas cap is letting fuel vapor escape, triggering an EVAP leak code.",
        "severity": "Low",
        "recommended_action": "Check that the gas cap is tight and undamaged; replace if cracked.",
        "symptoms": [("Check engine light is on", 1)],
        "codes": [("P0440", 2), ("P0442", 2), ("P0455", 3)],
    },
]


def seed():
    init_db()
    if is_seeded():
        print("Database already seeded, skipping.")
        return

    conn = get_connection()
    cur = conn.cursor()

    symptom_ids = {}
    for name, category in SYMPTOMS:
        cur.execute("INSERT INTO symptoms (name, category) VALUES (?, ?)", (name, category))
        symptom_ids[name] = cur.lastrowid

    code_ids = {}
    for code, description, category in DTC_CODES:
        cur.execute("INSERT INTO dtc_codes (code, description, category) VALUES (?, ?, ?)",
                    (code, description, category))
        code_ids[code] = cur.lastrowid

    for fault in FAULTS:
        cur.execute(
            "INSERT INTO faults (name, description, severity, recommended_action) VALUES (?, ?, ?, ?)",
            (fault["name"], fault["description"], fault["severity"], fault["recommended_action"]),
        )
        fault_id = cur.lastrowid

        for symptom_name, weight in fault["symptoms"]:
            cur.execute(
                "INSERT INTO fault_symptoms (fault_id, symptom_id, weight) VALUES (?, ?, ?)",
                (fault_id, symptom_ids[symptom_name], weight),
            )

        for code, weight in fault["codes"]:
            cur.execute(
                "INSERT INTO fault_dtc_codes (fault_id, dtc_code_id, weight) VALUES (?, ?, ?)",
                (fault_id, code_ids[code], weight),
            )

    conn.commit()
    conn.close()
    print(f"Seeded {len(SYMPTOMS)} symptoms, {len(DTC_CODES)} DTC codes, {len(FAULTS)} faults.")


if __name__ == "__main__":
    seed()
