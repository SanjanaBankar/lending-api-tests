import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DB = "lending.db"
app = FastAPI()

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

with conn() as c:
    c.execute("""CREATE TABLE IF NOT EXISTS applications(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, amount REAL NOT NULL,
        term_months INTEGER NOT NULL, status TEXT NOT NULL)""")

class ApplicationIn(BaseModel):
    name: str = Field(min_length=2)
    amount: float = Field(ge=1000, le=500000)
    term_months: int = Field(ge=6, le=60)

@app.post("/applications", status_code=201)
def create(app_in: ApplicationIn):
    with conn() as c:
        cur = c.execute(
            "INSERT INTO applications(name,amount,term_months,status) VALUES(?,?,?,?)",
            (app_in.name, app_in.amount, app_in.term_months, "SUBMITTED"))
        return {"id": cur.lastrowid, "status": "SUBMITTED", **app_in.model_dump()}

@app.get("/applications/{app_id}")
def get_application(app_id: int):
    with conn() as c:
        row = c.execute("SELECT * FROM applications WHERE id=?", (app_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Not found")
    return dict(row)

@app.get("/quote")
def quote(amount: float, term_months: int, rate: float = 12.0):
    if not (1000 <= amount <= 500000) or not (6 <= term_months <= 60):
        raise HTTPException(422, "Out of range")
    r = rate / 12 / 100
    emi = amount * r * (1 + r) ** term_months / ((1 + r) ** term_months - 1)
    return {"amount": amount, "term_months": term_months, "emi": round(emi, 2)}