import sys; sys.stdout.reconfigure(encoding='utf-8'); sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
from sqlalchemy import text
from app.database import SessionLocal

db = SessionLocal()

print("=== FINAL SUMMARY ===")

# 1. Total F available by source
print("\n1. F AVAILABLE BY SOURCE:")
rows = db.execute(text("""
    SELECT 
        CASE 
            WHEN EXISTS (SELECT 1 FROM expenditures e WHERE e.work_id = rs.work_id) THEN 'expenditure'
            ELSE 'completion_fallback'
        END as source,
        COUNT(*) as cnt
    FROM risk_signals rs
    WHERE rs.signal_code = 'F' AND rs.available = true
    GROUP BY source
""")).fetchall()
for r in rows:
    print(f"  {r[0]:25s}: {r[1]:6d}")

# 2. F available with completion_fallback, broken down by ratio
print("\n2. COMPLETION_FALLBACK F SIGNALS:")
rows = db.execute(text("""
    SELECT 
        CASE 
            WHEN wc.amount_disbursed = ws.sanction_amount THEN 'equal_to_sanction'
            WHEN wc.amount_disbursed < ws.sanction_amount THEN 'less_than_sanction'
            ELSE 'other'
        END as ratio_type,
        COUNT(*) as cnt
    FROM risk_signals rs
    JOIN works w ON rs.work_id = w.work_id
    LEFT JOIN expenditures e ON w.work_id = e.work_id
    JOIN work_completions wc ON w.work_id = wc.work_id
    LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
    WHERE rs.signal_code = 'F' AND rs.available = true
      AND e.work_id IS NULL
    GROUP BY ratio_type
""")).fetchall()
for r in rows:
    print(f"  {r[0]:25s}: {r[1]:6d}")

# 3. Total scored works
print("\n3. TOTAL SCORED WORKS:")
total_scored = db.execute(text("SELECT COUNT(*) FROM risk_scores")).scalar()
print(f"  Works with risk scores: {total_scored}")

# 4. Frontend pages
print("\n4. FRONTEND PAGES:")
import requests
for page in ['', 'works', 'analytics', 'inspection', 'anomalies', 'vendors']:
    try:
        r = requests.get(f'http://127.0.0.1:3000/{page}', timeout=5)
        print(f"  /{page:20s}: {r.status_code}")
    except Exception as e:
        print(f"  /{page:20s}: ERROR")

# 5. API endpoints
print("\n5. API ENDPOINTS:")
endpoints = [
    'http://127.0.0.1:8000/health',
    'http://127.0.0.1:8000/api/dashboard/summary',
    'http://127.0.0.1:8000/api/works?limit=3',
    'http://127.0.0.1:8000/api/inspection/queue',
]
for url in endpoints:
    try:
        r = requests.get(url, timeout=5)
        print(f"  {url:50s}: {r.status_code}")
    except Exception as e:
        print(f"  {url:50s}: ERROR {e}")

db.close()
