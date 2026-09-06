import sys; sys.stdout.reconfigure(encoding='utf-8'); sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
from sqlalchemy import text
from app.database import SessionLocal
db = SessionLocal()

print("=== EDGE CASE: Works with expenditure records but zero aggregate disbursed ===")
edge = db.execute(text("""
    WITH exp_agg AS (
        SELECT work_id, COUNT(*) as cnt, SUM(fund_disbursed_amount) as total_disbursed
        FROM expenditures GROUP BY work_id
    )
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN total_disbursed = 0 THEN 1 END) as zero_disbursed,
        COUNT(CASE WHEN total_disbursed IS NULL THEN 1 END) as null_disbursed
    FROM exp_agg
""")).fetchone()
print(f"  Total works with exp records: {edge[0]}")
print(f"  Zero aggregate disbursed: {edge[1]}")
print(f"  Null aggregate disbursed: {edge[2]}")

print("\n=== WORKS WITH ZERO DISBURSED: F SIGNAL STATUS ===")
zero_works = db.execute(text("""
    WITH exp_agg AS (
        SELECT work_id, SUM(fund_disbursed_amount) as total_disbursed
        FROM expenditures GROUP BY work_id
    )
    SELECT w.work_id, ea.total_disbursed, rs.score as f_score, rs.available, rs.explanation
    FROM works w
    JOIN exp_agg ea ON w.work_id = ea.work_id
    LEFT JOIN risk_signals rs ON w.work_id = rs.work_id AND rs.signal_code = 'F'
    WHERE ea.total_disbursed = 0 OR ea.total_disbursed IS NULL
    LIMIT 10
""")).fetchall()
for r in zero_works:
    print(f"  {r[0][:45]:45s} exp_total={r[1]}  f_score={r[2]}  avail={r[3]}  expl={r[4][:50] if r[4] else 'None'}")

print("\n=== VERIFY: Works with valid sanction AND valid disbursed (F should be available) ===")
joint = db.execute(text("""
    WITH exp_agg AS (
        SELECT work_id, SUM(fund_disbursed_amount) as total_disbursed
        FROM expenditures GROUP BY work_id
    )
    SELECT 
        COUNT(DISTINCT w.work_id) as total,
        COUNT(DISTINCT CASE WHEN ws.sanction_amount > 0 AND ea.total_disbursed > 0 THEN w.work_id END) as both_valid,
        COUNT(DISTINCT CASE WHEN ws.sanction_amount > 0 AND ea.total_disbursed > 0 THEN w.work_id END) as f_should_be_avail
    FROM works w
    LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
    LEFT JOIN exp_agg ea ON w.work_id = ea.work_id
""")).fetchone()
print(f"  Works with both valid sanction (>0) AND valid disbursed (>0): {joint[1]}")
print(f"  Expected F available count: {joint[1]}")

print("\n=== ACTUAL F AVAILABLE COUNT ===")
f_avail = db.execute(text("""
    SELECT COUNT(*) FROM risk_signals WHERE signal_code='F' AND available=true AND score IS NOT NULL
""")).scalar()
print(f"  Actual F available: {f_avail}")
print(f"  Expected F available: {joint[1]}")
print(f"  MATCH: {f_avail == joint[1]}")

db.close()
