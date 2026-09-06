import sys; sys.stdout.reconfigure(encoding='utf-8'); sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
from sqlalchemy import text
from app.database import SessionLocal

db = SessionLocal()

print("=" * 80)
print("F SIGNAL: DB vs CURRENT CODE MISMATCH")
print("=" * 80)

# Works with F available in DB but should be unavailable (no expenditure records)
print("\n1. F AVAILABLE IN DB, BUT SHOULD BE UNAVAILABLE (no exp records):")
rows = db.execute(text("""
    WITH exp_agg AS (
        SELECT work_id, SUM(fund_disbursed_amount) as total_disbursed
        FROM expenditures GROUP BY work_id
    )
    SELECT COUNT(*) as cnt
    FROM works w
    JOIN risk_signals rs ON w.work_id = rs.work_id AND rs.signal_code = 'F' AND rs.available = true
    LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
    LEFT JOIN exp_agg ea ON w.work_id = ea.work_id
    WHERE ea.work_id IS NULL
""")).fetchone()
print(f"  Count: {rows[0]}")

# Works with F available but disbursed = sanction (should be 65, correct)
print("\n2. F AVAILABLE IN DB, SHOULD BE UNAVAILABLE (sanction but no exp):")
rows = db.execute(text("""
    WITH exp_agg AS (
        SELECT work_id, SUM(fund_disbursed_amount) as total_disbursed
        FROM expenditures GROUP BY work_id
    )
    SELECT COUNT(*) as cnt
    FROM works w
    JOIN risk_signals rs ON w.work_id = rs.work_id AND rs.signal_code = 'F' AND rs.available = true
    LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
    LEFT JOIN exp_agg ea ON w.work_id = ea.work_id
    WHERE ws.sanction_amount > 0 AND ea.work_id IS NULL
""")).fetchone()
print(f"  Count: {rows[0]}")

# Works with F unavailable but SHOULD be available (has exp records, sanction > 0)
print("\n3. F UNAVAILABLE IN DB, BUT SHOULD BE AVAILABLE (has exp + sanction):")
rows = db.execute(text("""
    WITH exp_agg AS (
        SELECT work_id, SUM(fund_disbursed_amount) as total_disbursed
        FROM expenditures GROUP BY work_id
    )
    SELECT COUNT(*) as cnt
    FROM works w
    JOIN risk_signals rs ON w.work_id = rs.work_id AND rs.signal_code = 'F' AND rs.available = false
    LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
    LEFT JOIN exp_agg ea ON w.work_id = ea.work_id
    WHERE ws.sanction_amount > 0 AND ea.total_disbursed > 0
""")).fetchone()
print(f"  Count: {rows[0]}")

# Actual F available count
print("\n4. ACTUAL F AVAILABLE COUNT:")
rows = db.execute(text("""
    SELECT COUNT(*) FROM risk_signals 
    WHERE signal_code='F' AND available=true AND score IS NOT NULL
""")).fetchone()
print(f"  F available: {rows[0]}")

# Expected F available count (sanction > 0 AND disbursed > 0)
rows = db.execute(text("""
    WITH exp_agg AS (
        SELECT work_id, SUM(fund_disbursed_amount) as total_disbursed
        FROM expenditures GROUP BY work_id
    )
    SELECT COUNT(DISTINCT w.work_id) as cnt
    FROM works w
    LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
    LEFT JOIN exp_agg ea ON w.work_id = ea.work_id
    WHERE ws.sanction_amount > 0 AND ea.total_disbursed > 0
""")).fetchone()
print(f"  Expected F available: {rows[0]}")

# Check explanation distribution for F available works
print("\n5. F AVAILABLE WORKS: EXPLANATION DISTRIBUTION:")
rows = db.execute(text("""
    SELECT explanation, COUNT(*) as cnt
    FROM risk_signals
    WHERE signal_code='F' AND available=true
    GROUP BY explanation
    ORDER BY cnt DESC
""")).fetchall()
for r in rows:
    print(f"  [{r[1]:6d}x] {r[0][:80]}")

# Verify: works with disbursed = sanction amount (ratio=1.0)
print("\n6. VERIFY: disbursed_amount = sanction_amount IN AI INPUT:")
rows = db.execute(text("""
    SELECT w.work_id, ws.sanction_amount, COALESCE(d.total_disbursed, 0) as total_disbursed
    FROM works w
    LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
    LEFT JOIN (
        SELECT work_id, SUM(fund_disbursed_amount) as total_disbursed
        FROM expenditures GROUP BY work_id
    ) d ON w.work_id = d.work_id
    WHERE ws.sanction_amount > 0
    LIMIT 10
""")).fetchall()
for r in rows:
    ratio = r[2] / r[1] if r[1] and r[1] > 0 else None
    print(f"  {r[0][:45]:45s} sanction={r[1]:>12} disbursed={r[2]:>12} ratio={ratio}")

db.close()
