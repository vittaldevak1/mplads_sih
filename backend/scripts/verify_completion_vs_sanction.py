import sys; sys.stdout.reconfigure(encoding='utf-8'); sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
from sqlalchemy import text
from app.database import SessionLocal
db = SessionLocal()

print("=== COMPLETION vs SANCTION: DETAILED COMPARISON ===")
rows = db.execute(text("""
    SELECT 
        CASE 
            WHEN wc.amount_disbursed = ws.sanction_amount THEN 'EQUAL'
            WHEN wc.amount_disbursed < ws.sanction_amount THEN 'LESS'
            ELSE 'OTHER'
        END as cmp,
        COUNT(*) as cnt,
        ROUND(AVG(ws.sanction_amount), 0) as avg_sanction,
        ROUND(AVG(wc.amount_disbursed), 0) as avg_disbursed
    FROM work_completions wc
    LEFT JOIN work_sanctions ws ON wc.work_id = ws.work_id
    WHERE wc.amount_disbursed IS NOT NULL
    GROUP BY cmp
    ORDER BY cnt DESC
""")).fetchall()
for r in rows:
    avg_san = f"{r[2]:>15}" if r[2] is not None else "           None"
    avg_dis = f"{r[3]:>15}" if r[3] is not None else "           None"
    print(f"  {r[0]:8s}: {r[1]:6d}  avg_sanction={avg_san}  avg_disbursed={avg_dis}")

print("\n=== COMPLETION RECORDS: amount_disbursed = 0 ===")
rows = db.execute(text("""
    SELECT COUNT(*) FROM work_completions
    WHERE amount_disbursed = 0
""")).fetchone()
print(f"  Count: {rows[0]}")

print("\n=== COMPLETION RECORDS: amount_disbursed IS NULL ===")
rows = db.execute(text("""
    SELECT COUNT(*) FROM work_completions
    WHERE amount_disbursed IS NULL
""")).fetchone()
print(f"  Count: {rows[0]}")

print("\n=== NO-EXP WORKS: F AVAILABLE, completion amount = sanction ===")
rows = db.execute(text("""
    SELECT COUNT(DISTINCT w.work_id)
    FROM works w
    LEFT JOIN expenditures e ON w.work_id = e.work_id
    JOIN risk_signals rs ON w.work_id = rs.work_id AND rs.signal_code = 'F' AND rs.available = true
    JOIN work_completions wc ON w.work_id = wc.work_id
    JOIN work_sanctions ws ON w.work_id = ws.work_id
    WHERE e.work_id IS NULL
      AND wc.amount_disbursed = ws.sanction_amount
""")).fetchone()
print(f"  Count: {rows[0]}")

print("\n=== NO-EXP WORKS: F AVAILABLE, completion amount < sanction ===")
rows = db.execute(text("""
    SELECT COUNT(DISTINCT w.work_id)
    FROM works w
    LEFT JOIN expenditures e ON w.work_id = e.work_id
    JOIN risk_signals rs ON w.work_id = rs.work_id AND rs.signal_code = 'F' AND rs.available = true
    JOIN work_completions wc ON w.work_id = wc.work_id
    JOIN work_sanctions ws ON w.work_id = ws.work_id
    WHERE e.work_id IS NULL
      AND wc.amount_disbursed < ws.sanction_amount
""")).fetchone()
print(f"  Count: {rows[0]}")

print("\n=== SAMPLE: completion amount < sanction (should be F=35, not F=65) ===")
rows = db.execute(text("""
    SELECT w.work_id, ws.sanction_amount, wc.amount_disbursed, rs.score as f_score
    FROM works w
    LEFT JOIN expenditures e ON w.work_id = e.work_id
    JOIN risk_signals rs ON w.work_id = rs.work_id AND rs.signal_code = 'F' AND rs.available = true
    JOIN work_completions wc ON w.work_id = wc.work_id
    JOIN work_sanctions ws ON w.work_id = ws.work_id
    WHERE e.work_id IS NULL
      AND wc.amount_disbursed < ws.sanction_amount
    LIMIT 5
""")).fetchall()
for r in rows:
    print(f"  {r[0][:50]:50s} sanction={r[1]}  completion={r[2]}  F_score={r[3]}")

db.close()
