"""Test the audit endpoint with real inference on 20 works."""
import sys
sys.path.insert(0, '.')

import requests
import time

BASE = "http://127.0.0.1:8000"

# Check if backend is running
try:
    r = requests.get(f"{BASE}/docs", timeout=5)
    print("Backend is running.")
except Exception:
    print("Backend not running. Start it first: cd backend && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000")
    sys.exit(1)

# Run audit on 20 works
print("\nStarting audit of 20 works...")
r = requests.post(f"{BASE}/api/v1/audit/run?limit=20", timeout=30)
print(f"Response: {r.json()}")

# Poll until done
for _ in range(60):
    time.sleep(2)
    r = requests.get(f"{BASE}/api/v1/audit/status", timeout=5)
    status = r.json()
    print(f"  Status: {status['works_processed']}/{status['total']} processed")
    if not status["running"]:
        break

print("\nDone. Checking database...")

# Verify results in DB
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    r = db.execute(text("SELECT count(*) FROM risk_scores"))
    print(f"  risk_scores: {r.scalar()} rows")
    r = db.execute(text("SELECT count(*) FROM risk_signals"))
    print(f"  risk_signals: {r.scalar()} rows")
    r = db.execute(text("SELECT count(*) FROM anomalies"))
    print(f"  anomalies: {r.scalar()} rows")

    # Sample a result
    r = db.execute(text("""
        SELECT work_id, composite_risk, confidence_coverage, inspection_priority
        FROM risk_scores
        ORDER BY composite_risk DESC
        LIMIT 3
    """))
    print("\n  Top 3 highest risk works:")
    for row in r:
        print(f"    {row[0][:50]}... | risk={row[1]} | coverage={row[2]} | priority={row[3]}")
finally:
    db.close()
