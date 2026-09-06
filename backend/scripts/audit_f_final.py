import sys; sys.stdout.reconfigure(encoding='utf-8'); sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
from sqlalchemy import text
from app.database import SessionLocal

db = SessionLocal()
WEIGHTS = {'F':0.15,'D':0.12,'X':0.12,'V':0.10,'C':0.10,'Q':0.10,'O':0.08,'S':0.07,'G':0.08,'B':0.04,'Rs':0.04}

print("=" * 80)
print("F SIGNAL: FINAL AUDIT REPORT")
print("=" * 80)

# 1. Overall counts
print("\n=== 1. BASE DATA ===")
total_works = db.execute(text("SELECT COUNT(*) FROM works")).scalar()
print(f"  Total works: {total_works}")

has_sanction = db.execute(text("""
    SELECT COUNT(*) FROM works w
    JOIN work_sanctions ws ON w.work_id = ws.work_id
    WHERE ws.sanction_amount > 0
""")).scalar()
print(f"  Works with valid sanction (>0): {has_sanction} ({has_sanction*100/total_works:.2f}%)")

has_exp = db.execute(text("""
    SELECT COUNT(DISTINCT work_id) FROM expenditures
""")).scalar()
print(f"  Works with expenditure records: {has_exp} ({has_exp*100/total_works:.2f}%)")

has_disbursed = db.execute(text("""
    WITH exp_agg AS (
        SELECT work_id, SUM(fund_disbursed_amount) as total_disbursed
        FROM expenditures GROUP BY work_id
    )
    SELECT COUNT(*) FROM exp_agg WHERE total_disbursed > 0
""")).scalar()
print(f"  Works with aggregated disbursed > 0: {has_disbursed} ({has_disbursed*100/total_works:.2f}%)")

both_valid = db.execute(text("""
    WITH exp_agg AS (
        SELECT work_id, SUM(fund_disbursed_amount) as total_disbursed
        FROM expenditures GROUP BY work_id
    )
    SELECT COUNT(DISTINCT w.work_id)
    FROM works w
    LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
    LEFT JOIN exp_agg ea ON w.work_id = ea.work_id
    WHERE ws.sanction_amount > 0 AND ea.total_disbursed > 0
""")).scalar()
print(f"  Works with BOTH valid sanction AND disbursed: {both_valid} ({both_valid*100/total_works:.2f}%)")

# 2. F signal status
print("\n=== 2. F SIGNAL STATUS IN DB ===")
f_stats = db.execute(text("""
    SELECT 
        available,
        COUNT(*) as cnt,
        ROUND(AVG(score), 1) as avg_score
    FROM risk_signals
    WHERE signal_code = 'F'
    GROUP BY available
    ORDER BY available DESC
""")).fetchall()
for r in f_stats:
    status = "AVAILABLE" if r[0] else "UNAVAILABLE"
    print(f"  {status:12s}: {r[1]:6d}  avg_score={r[2]}")

# 3. F available works: by explanation
print("\n=== 3. F AVAILABLE WORKS: EXPLANATION ===")
f_avail_expl = db.execute(text("""
    SELECT explanation, COUNT(*) as cnt
    FROM risk_signals
    WHERE signal_code = 'F' AND available = true
    GROUP BY explanation
    ORDER BY cnt DESC
""")).fetchall()
for r in f_avail_expl:
    print(f"  [{r[1]:6d}x] {r[0][:80]}")

# 4. F unavailable works: by explanation
print("\n=== 4. F UNAVAILABLE WORKS: EXPLANATION ===")
f_unavail_expl = db.execute(text("""
    SELECT explanation, COUNT(*) as cnt
    FROM risk_signals
    WHERE signal_code = 'F' AND available = false
    GROUP BY explanation
    ORDER BY cnt DESC
""")).fetchall()
for r in f_unavail_expl:
    print(f"  [{r[1]:6d}x] {r[0][:80]}")

# 5. Stale F signals (available but should be unavailable)
print("\n=== 5. STALE F SIGNALS (F available but no expenditure records) ===")
stale = db.execute(text("""
    WITH exp_agg AS (
        SELECT work_id, SUM(fund_disbursed_amount) as total_disbursed
        FROM expenditures GROUP BY work_id
    )
    SELECT COUNT(*) as cnt
    FROM works w
    JOIN risk_signals rs ON w.work_id = rs.work_id AND rs.signal_code = 'F' AND rs.available = true
    LEFT JOIN exp_agg ea ON w.work_id = ea.work_id
    WHERE ea.work_id IS NULL
""")).fetchone()
print(f"  F available works with NO expenditure records: {stale[0]}")
print(f"  These are STALE — current code would mark them unavailable")

# 6. F available works where sanction = disbursed (ratio=1.0, score=65)
print("\n=== 6. F=65 (disbursed = sanction, ratio=100%) ===")
f65 = db.execute(text("""
    SELECT COUNT(*) FROM risk_signals
    WHERE signal_code = 'F' AND available = true AND score = 65
""")).fetchone()
print(f"  Count: {f65[0]}")

# 7. Check evidence for stale F signals
print("\n=== 7. EVIDENCE FOR STALE F SIGNALS ===")
stale_ev = db.execute(text("""
    SELECT rs.evidence
    FROM works w
    JOIN risk_signals rs ON w.work_id = rs.work_id AND rs.signal_code = 'F' AND rs.available = true
    LEFT JOIN (
        SELECT work_id, SUM(fund_disbursed_amount) as total_disbursed
        FROM expenditures GROUP BY work_id
    ) ea ON w.work_id = ea.work_id
    WHERE ea.work_id IS NULL
    LIMIT 3
""")).fetchall()
for r in stale_ev:
    print(f"  Evidence: {r[0]}")

# 8. F signal for 'Lighting of public spaces'
print("\n=== 8. F SIGNAL FOR LIGHTING WORKS ===")
lighting_f = db.execute(text("""
    SELECT rs.available, rs.score, COUNT(*) as cnt
    FROM risk_signals rs
    JOIN works w ON rs.work_id = w.work_id
    WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
      AND rs.signal_code = 'F'
    GROUP BY rs.available, rs.score
    ORDER BY rs.available DESC, rs.score ASC
""")).fetchall()
for r in lighting_f:
    status = "AVAILABLE" if r[0] else "UNAVAILABLE"
    print(f"  {status:12s} Score={r[1]}  Count={r[2]}")

db.close()
