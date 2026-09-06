import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

# Risk distribution
r = db.execute(text("""
    SELECT inspection_priority, count(*) as cnt
    FROM risk_scores
    WHERE composite_risk IS NOT NULL
    GROUP BY inspection_priority
    ORDER BY cnt DESC
"""))
print("=== Risk Distribution ===")
for row in r:
    print(f"  {row[0]}: {row[1]}")

# Check signal quality - are explanations from real inference or mock?
r = db.execute(text("""
    SELECT explanation, count(*) as cnt
    FROM risk_signals
    WHERE explanation IS NOT NULL
    GROUP BY explanation
    ORDER BY cnt DESC
    LIMIT 15
"""))
print()
print("=== Top Signal Explanations (to detect mock vs real) ===")
for row in r:
    print(f"  [{row[1]}] {row[0][:100]}")

# Composite risk bands
r = db.execute(text("""
    SELECT
        CASE
            WHEN composite_risk >= 80 THEN '80-100'
            WHEN composite_risk >= 65 THEN '65-79'
            WHEN composite_risk >= 50 THEN '50-64'
            WHEN composite_risk >= 40 THEN '40-49'
            WHEN composite_risk >= 25 THEN '25-39'
            ELSE '0-24'
        END as band,
        count(*) as cnt
    FROM risk_scores
    WHERE composite_risk IS NOT NULL
    GROUP BY band
    ORDER BY band DESC
"""))
print()
print("=== Composite Risk Bands ===")
for row in r:
    print(f"  {row[0]}: {row[1]}")

# Check the frontend API calls
r = db.execute(text("""
    SELECT count(*) FROM risk_signals WHERE explanation LIKE '%Signal active%'
"""))
mock_count = r.scalar()
r = db.execute(text("""
    SELECT count(*) FROM risk_signals WHERE explanation LIKE '%unavailable%' OR explanation LIKE '%threshold%' OR explanation LIKE '%similarity%' OR explanation LIKE '%vendor%' OR explanation LIKE '%gestation%' OR explanation LIKE '%outlier%' OR explanation LIKE '%disbursement%'
"""))
real_count = r.scalar()
print(f"\n=== Data Quality ===")
print(f"  Mock signals (old): {mock_count}")
print(f"  Real signals (AI): {real_count}")

db.close()
