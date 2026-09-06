import sys; sys.stdout.reconfigure(encoding='utf-8'); sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
from sqlalchemy import text
from app.database import SessionLocal
db = SessionLocal()

print("=== WORK COMPLETIONS SCHEMA ===")
rows = db.execute(text("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'work_completions'
    ORDER BY ordinal_position
""")).fetchall()
for r in rows:
    print(f"  {r[0]:30s} {r[1]}")

print("\n=== SAMPLE COMPLETION RECORDS (no-expenditure works) ===")
rows = db.execute(text("""
    SELECT wc.work_id, wc.amount_disbursed, wc.completion_date
    FROM work_completions wc
    LEFT JOIN expenditures e ON wc.work_id = e.work_id
    WHERE e.work_id IS NULL
    LIMIT 10
""")).fetchall()
for r in rows:
    print(f"  {r[0][:45]:45s} amount_disbursed={r[1]}  date={r[2]}")

print("\n=== COMPLETION amount_disbursed vs SANCTION ===")
rows = db.execute(text("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN wc.amount_disbursed = ws.sanction_amount THEN 1 END) as equal_to_sanction,
        COUNT(CASE WHEN wc.amount_disbursed < ws.sanction_amount THEN 1 END) as less_than_sanction,
        COUNT(CASE WHEN wc.amount_disbursed > ws.sanction_amount THEN 1 END) as greater_than_sanction,
        COUNT(CASE WHEN wc.amount_disbursed IS NULL THEN 1 END) as null_disbursed
    FROM work_completions wc
    LEFT JOIN work_sanctions ws ON wc.work_id = ws.work_id
    WHERE wc.amount_disbursed IS NOT NULL
""")).fetchone()
print(f"  Total with amount_disbursed: {rows[0]}")
print(f"  = sanction_amount: {rows[1]} ({rows[1]*100/rows[0]:.1f}%)")
print(f"  < sanction_amount: {rows[2]} ({rows[2]*100/rows[0]:.1f}%)")
print(f"  > sanction_amount: {rows[3]} ({rows[3]*100/rows[0]:.1f}%)")
print(f"  NULL: {rows[4]}")

print("\n=== NO-EXP WORKS: F AVAILABLE vs COMPLETION ===")
rows = db.execute(text("""
    WITH no_exp_works AS (
        SELECT w.work_id
        FROM works w
        LEFT JOIN expenditures e ON w.work_id = e.work_id
        WHERE e.work_id IS NULL
    )
    SELECT 
        COUNT(DISTINCT CASE WHEN rs.available = true THEN w.work_id END) as f_available,
        COUNT(DISTINCT CASE WHEN rs.available = false THEN w.work_id END) as f_unavailable,
        COUNT(DISTINCT wc.work_id) as has_completion,
        COUNT(DISTINCT CASE WHEN wc.amount_disbursed > 0 THEN w.work_id END) as completion_has_disbursed
    FROM no_exp_works w
    LEFT JOIN risk_signals rs ON w.work_id = rs.work_id AND rs.signal_code = 'F'
    LEFT JOIN work_completions wc ON w.work_id = wc.work_id
""")).fetchone()
print(f"  F available: {rows[0]}")
print(f"  F unavailable: {rows[1]}")
print(f"  Has completion record: {rows[2]}")
print(f"  Completion has amount_disbursed > 0: {rows[3]}")

db.close()
