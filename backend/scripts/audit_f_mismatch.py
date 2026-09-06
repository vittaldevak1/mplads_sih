import sys; sys.stdout.reconfigure(encoding='utf-8'); sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
from sqlalchemy import text
from app.database import SessionLocal
db = SessionLocal()

print("=== WORKS WITH F AVAILABLE BUT MISSING SANCTION OR DISBURSED ===")
rows = db.execute(text("""
    WITH exp_agg AS (
        SELECT work_id, SUM(fund_disbursed_amount) as total_disbursed
        FROM expenditures GROUP BY work_id
    )
    SELECT 
        w.work_id,
        ws.sanction_amount,
        ea.total_disbursed,
        rs.score as f_score,
        rs.available,
        rs.explanation
    FROM works w
    JOIN risk_signals rs ON w.work_id = rs.work_id AND rs.signal_code = 'F' AND rs.available = true
    LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
    LEFT JOIN exp_agg ea ON w.work_id = ea.work_id
    WHERE ws.sanction_amount IS NULL OR ws.sanction_amount <= 0
       OR ea.total_disbursed IS NULL OR ea.total_disbursed <= 0
    LIMIT 15
""")).fetchall()

for r in rows:
    print(f"  {r[0][:50]:50s} sanction={r[1]}  disbursed={r[2]}  f_score={r[3]}  avail={r[4]}")
    print(f"    explanation: {r[5]}")

print("\n=== COUNT BY EXPLANATION (F available but shouldn't be) ===")
counts = db.execute(text("""
    WITH exp_agg AS (
        SELECT work_id, SUM(fund_disbursed_amount) as total_disbursed
        FROM expenditures GROUP BY work_id
    )
    SELECT rs.explanation, COUNT(*) as cnt
    FROM works w
    JOIN risk_signals rs ON w.work_id = rs.work_id AND rs.signal_code = 'F' AND rs.available = true
    LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
    LEFT JOIN exp_agg ea ON w.work_id = ea.work_id
    WHERE ws.sanction_amount IS NULL OR ws.sanction_amount <= 0
       OR ea.total_disbursed IS NULL OR ea.total_disbursed <= 0
    GROUP BY rs.explanation
    ORDER BY cnt DESC
""")).fetchall()
for r in counts:
    print(f"  [{r[1]:6d}x] {r[0]}")

print("\n=== WORKS WITH F AVAILABLE: BY EXPLANATION ===")
avail_expl = db.execute(text("""
    SELECT explanation, COUNT(*) as cnt
    FROM risk_signals
    WHERE signal_code = 'F' AND available = true
    GROUP BY explanation
    ORDER BY cnt DESC
""")).fetchall()
for r in avail_expl:
    print(f"  [{r[1]:6d}x] {r[0]}")

print("\n=== WORKS WITH F UNAVAILABLE: BY EXPLANATION ===")
unavail_expl = db.execute(text("""
    SELECT explanation, COUNT(*) as cnt
    FROM risk_signals
    WHERE signal_code = 'F' AND available = false
    GROUP BY explanation
    ORDER BY cnt DESC
""")).fetchall()
for r in unavail_expl:
    print(f"  [{r[1]:6d}x] {r[0]}")

db.close()
