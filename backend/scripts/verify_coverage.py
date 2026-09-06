"""
Verify confidence_coverage and frontend state for no-expenditure works.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
from sqlalchemy import text
from app.database import SessionLocal

db = SessionLocal()

print("=== CONFIDENCE COVERAGE FOR NO-EXPENDITURE WORKS ===")
rows = db.execute(text("""
    SELECT rs.confidence_coverage, COUNT(*) as cnt
    FROM risk_scores rs
    JOIN works w ON rs.work_id = w.work_id
    LEFT JOIN (SELECT DISTINCT work_id FROM expenditures) e ON w.work_id = e.work_id
    WHERE e.work_id IS NULL
    GROUP BY rs.confidence_coverage
    ORDER BY rs.confidence_coverage DESC
""")).fetchall()
for r in rows:
    print(f"  coverage={float(r[0]):.4f}: {r[1]} works")

print("\n=== SAMPLE NO-EXP WORKS WITH F AVAILABLE ===")
rows = db.execute(text("""
    SELECT w.work_id, rs.confidence_coverage, rs.inspection_priority
    FROM risk_scores rs
    JOIN works w ON rs.work_id = w.work_id
    LEFT JOIN (SELECT DISTINCT work_id FROM expenditures) e ON w.work_id = e.work_id
    WHERE e.work_id IS NULL
      AND EXISTS (
          SELECT 1 FROM risk_signals rs2
          WHERE rs2.work_id = rs.work_id AND rs2.signal_code = 'F' AND rs2.available = true
      )
    LIMIT 5
""")).fetchall()
for r in rows:
    print(f"  {r[0][:50]:50s} coverage={float(r[1]):.4f} priority={r[2]}")

print("\n=== F EVIDENCE FOR THESE WORKS ===")
rows = db.execute(text("""
    SELECT rs.evidence
    FROM risk_signals rs
    JOIN works w ON rs.work_id = w.work_id
    LEFT JOIN (SELECT DISTINCT work_id FROM expenditures) e ON w.work_id = e.work_id
    WHERE e.work_id IS NULL
      AND rs.signal_code = 'F' AND rs.available = true
    LIMIT 3
""")).fetchall()
for r in rows:
    print(f"  {r[0]}")

print("\n=== FRONTEND/API CHECK ===")
import requests
try:
    r = requests.get('http://127.0.0.1:3000', timeout=5)
    print(f"  Frontend: {r.status_code}")
except Exception as e:
    print(f"  Frontend: ERROR {e}")

try:
    r = requests.get('http://127.0.0.1:8000/health', timeout=5)
    print(f"  Backend: {r.status_code} {r.json()}")
except Exception as e:
    print(f"  Backend: ERROR {e}")

db.close()
