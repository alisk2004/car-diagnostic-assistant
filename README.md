# Car Diagnostic Assistant

A web-based car diagnostic assistant that uses a **rule-based expert system**
to suggest likely faults from user-reported symptoms and/or OBD-II diagnostic
trouble codes (DTCs), backed by a SQLite database of vehicle knowledge.

## Features

- **Symptom Checker** — pick from ~24 common symptoms across Engine,
  Electrical, Brakes, Transmission, Cooling, and Exhaust categories.
- **OBD-II Code Lookup** — search/browse ~28 real DTCs (e.g. `P0300`,
  `P0420`) with plain-English descriptions.
- **Combined diagnosis** — symptoms and codes are reasoned over together for
  a stronger, ranked result.
- **Explainable AI reasoning engine** — every result shows a confidence
  percentage plus exactly which symptoms/codes drove that score, and a
  recommended action with a severity rating (Low/Medium/High/Critical).
- **History** — every diagnosis is saved to the database and can be
  reviewed later.

## Tech Stack

- **Backend**: Python 3 + Flask
- **Database**: SQLite (`sqlite3`, zero setup required)
- **Frontend**: Vanilla HTML/CSS/JavaScript (no build step)
- **Tests**: `pytest`

## How the "AI" Works

`diagnosis_engine.py` implements a rule-based expert system. Each known fault
(e.g. "Worn Spark Plugs") is linked in the database to the symptoms and DTC
codes that indicate it, each with an integer **weight** representing how
strong a signal it is. When a user submits symptoms/codes:

1. The engine finds every fault linked to at least one submitted
   symptom/code.
2. For each candidate fault, it sums the weights of the *matched* links and
   divides by the sum of *all* weights defined for that fault → a confidence
   percentage.
3. Faults are ranked by confidence, highest first.

This keeps the reasoning fully transparent — you can always point to
exactly which inputs produced a given score, which is easy to explain and
demo on video.

## Project Structure

```
app.py                # Flask app + API routes
diagnosis_engine.py    # Rule-based scoring/reasoning logic (the "AI")
database.py            # SQLite connection + schema init helper
seed_data.py            # Populates symptoms, DTC codes, faults, and rules
schema.sql              # Database schema (CREATE TABLE statements)
requirements.txt
static/                 # CSS + JS for the frontend
templates/index.html    # Single-page frontend
tests/test_engine.py    # pytest tests for the reasoning engine
```

## Setup & Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd "MINI PROJECT CAR DIAGNOSTIC"

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app (creates and seeds the database automatically on first run)
python app.py
```

Then open **http://localhost:5000** in your browser.

## Usage

1. **Symptom Checker tab** — optionally enter vehicle make/model/year, then
   check off any symptoms you're experiencing.
2. **OBD-II Lookup tab** — search for and select any DTC codes you've read
   from a scan tool.
3. Click **Run Diagnosis** (visible from either tab) to get a ranked list of
   likely faults with confidence scores and recommended actions.
4. **History tab** — review any past diagnostic session.

## Running Tests

```bash
pytest
```

## Team Contributions

| Member | Contribution | Files owned |
|---|---|---|
| _Name 1_ | Backend / API | `app.py`, `database.py` |
| _Name 2_ | AI reasoning engine + testing | `diagnosis_engine.py`, `tests/test_engine.py` |
| _Name 3_ | Frontend UI | `templates/index.html`, `static/style.css`, `static/app.js` |
| _Name 4_ | Database content + docs | `schema.sql`, `seed_data.py`, `README.md` |

### Suggested video presentation split

- **Member 1**: Introduce the project, then walk through the Flask backend
  and API routes (`app.py`) that tie everything together.
- **Member 2**: Explain the rule-based reasoning engine (`diagnosis_engine.py`)
  — how confidence scores are calculated — and show the test suite (`pytest`)
  that verifies it.
- **Member 3**: Demo the frontend live — run a symptom-based diagnosis and an
  OBD-II code diagnosis.
- **Member 4**: Walk through the database schema and seed data (real
  symptoms, DTC codes, and faults) that power the whole system.
