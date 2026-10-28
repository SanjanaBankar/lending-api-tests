import sqlite3
import pytest
import requests

BASE = "http://127.0.0.1:8000"
DB = "lending.db"
VALID = {"name": "Asha Rao", "amount": 50000, "term_months": 12}

def db_row(app_id):
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    row = c.execute("SELECT * FROM applications WHERE id=?", (app_id,)).fetchone()
    c.close()
    return row

# Positive + DB match
def test_create_application_matches_db():
    r = requests.post(f"{BASE}/applications", json=VALID)
    assert r.status_code == 201
    body = r.json()
    row = db_row(body["id"])
    assert row is not None
    assert row["name"] == body["name"]
    assert row["amount"] == body["amount"]
    assert row["term_months"] == body["term_months"]
    assert row["status"] == "SUBMITTED"

# Schema
def test_create_response_schema():
    body = requests.post(f"{BASE}/applications", json=VALID).json()
    assert set(body) == {"id", "status", "name", "amount", "term_months"}
    assert isinstance(body["id"], int)
    assert isinstance(body["amount"], (int, float))

# Boundary
@pytest.mark.parametrize("amount,expected", [(999, 422), (1000, 201), (500000, 201), (500001, 422)])
def test_amount_boundaries(amount, expected):
    r = requests.post(f"{BASE}/applications", json={**VALID, "amount": amount})
    assert r.status_code == expected

@pytest.mark.parametrize("term,expected", [(5, 422), (6, 201), (60, 201), (61, 422)])
def test_term_boundaries(term, expected):
    r = requests.post(f"{BASE}/applications", json={**VALID, "term_months": term})
    assert r.status_code == expected

# Negative
@pytest.mark.parametrize("payload", [
    {},
    {"name": "A", "amount": 5000, "term_months": 12},
    {"name": "Asha Rao", "amount": "abc", "term_months": 12},
    {"name": "Asha Rao", "amount": 5000},
])
def test_invalid_payloads_rejected(payload):
    assert requests.post(f"{BASE}/applications", json=payload).status_code == 422

def test_rejected_request_not_saved_in_db():
    c = sqlite3.connect(DB)
    before = c.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    requests.post(f"{BASE}/applications", json={**VALID, "amount": 10})
    after = c.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    c.close()
    assert before == after

# GET
def test_get_application_matches_db():
    app_id = requests.post(f"{BASE}/applications", json=VALID).json()["id"]
    r = requests.get(f"{BASE}/applications/{app_id}")
    assert r.status_code == 200
    assert r.json()["name"] == db_row(app_id)["name"]

def test_get_unknown_application_404():
    assert requests.get(f"{BASE}/applications/999999").status_code == 404

# Quote calculation
def test_quote_emi_correct():
    r = requests.get(f"{BASE}/quote", params={"amount": 12000, "term_months": 12})
    assert r.status_code == 200
    assert r.json()["emi"] == pytest.approx(1066.19, abs=0.01)

def test_quote_out_of_range():
    r = requests.get(f"{BASE}/quote", params={"amount": 100, "term_months": 12})
    assert r.status_code == 422