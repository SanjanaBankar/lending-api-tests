# Lending API Test Framework
![API Tests](https://github.com/SanjanaBankar/lending-api-tests/actions/workflows/tests.yml/badge.svg)

A mock lending API (FastAPI + SQLite) with an automated pytest suite.

## What's covered
- Positive and negative API tests
- Boundary value analysis (loan amount and term)
- Response schema validation
- SQL assertions: API response matches the database; rejected requests are not saved
- EMI calculation check on the quote endpoint
- CI: runs on every push via GitHub Actions

## Run locally
pip install -r requirements.txt
uvicorn app:app --port 8000
pytest -v