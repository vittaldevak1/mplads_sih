"""
Verify actual current state: risk_signals, risk_scores, ai_adapter behavior.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
import json
from sqlalchemy import text
from app.database import SessionLocal
from app.services.ai_adapter import AIAdapter
from app.ai.engine import get_predictor

db = SessionLocal()
WEIGHTS = {'F':0.15,'D':0.12,'X':0.12,'V':0.10,'C':0.10,'Q':0.10,'O':0.08,'S':0.07,'G':0.08,'B':0.04,'Rs':0.04}

print("=" * 80)
print("CURRENT STATE VERIFICATION")
print("=" * 80)

# 1. Check ai_adapter.py current disbursed logic
print("\n=== 1. CURRENT ai_adapter.py DISBURSED LOGIC ===")
adapter = AIAdapter()
# Read the actual source
import inspect
src = inspect.getsource(adapter.prepare_work_for_ai)
# Find the disbursed logic
lines = src.split('\n')
in_disbursed = False
for i, line in enumerate(lines):
    if 'disbursed' in line.lower() or 'total_disbursed' in line.lower():
        in_disbursed = True
    if in_disbursed:
        print(f"  {line}")
        if 'return' in line and 'AIWorkInput' in line:
            break

# 2. Check actual F signal evidence for a work with NO expenditure
print("\n=== 2. F SIGNAL EVIDENCE — WORK WITH NO EXPENDITURE ===")
no_exp_work = db.execute(text("""
    SELECT w.work_id
    FROM works w
    LEFT JOIN expenditures e ON w.work_id = e.work_id
    WHERE e.work_id IS NULL
    LIMIT 1
""")).scalar()

f_sig = db.execute(text("""
    SELECT score, available, evidence, explanation
    FROM risk_signals
    WHERE work_id = :wid AND signal_code = 'F'
"""), {'wid': no_exp_work}).fetchone()

print(f"  Work: {no_exp_work}")
print(f"  Score: {f_sig[0]}")
print(f"  Available: {f_sig[1]}")
print(f"  Evidence: {f_sig[2]}")
print(f"  Explanation: {f_sig[3]}")

# 3. Check actual F signal evidence for a work WITH expenditure
print("\n=== 3. F SIGNAL EVIDENCE — WORK WITH EXPENDITURE ===")
with_exp_work = db.execute(text("""
    SELECT w.work_id
    FROM works w
    JOIN expenditures e ON w.work_id = e.work_id
    LIMIT 1
""")).scalar()

f_sig2 = db.execute(text("""
    SELECT score, available, evidence, explanation
    FROM risk_signals
    WHERE work_id = :wid AND signal_code = 'F'
"""), {'wid': with_exp_work}).fetchone()

print(f"  Work: {with_exp_work}")
print(f"  Score: {f_sig2[0]}")
print(f"  Available: {f_sig2[1]}")
print(f"  Evidence: {f_sig2[2]}")
print(f"  Explanation: {f_sig2[3]}")

# 4. Check: how many F available have 'completion_fallback' in evidence
print("\n=== 4. F SIGNALS WITH 'completion_fallback' IN EVIDENCE ===")
cf_count = db.execute(text("""
    SELECT COUNT(*) FROM risk_signals
    WHERE signal_code = 'F'
      AND available = true
      AND evidence::text LIKE '%completion_fallback%'
""")).scalar()
print(f"  Count: {cf_count}")

# 5. Check: how many F available have NO expenditure records
print("\n=== 5. F AVAILABLE WITH NO EXPENDITURE RECORDS ===")
no_exp_f = db.execute(text("""
    WITH exp_works AS (
        SELECT DISTINCT work_id FROM expenditures
    )
    SELECT COUNT(*)
    FROM risk_signals rs
    LEFT JOIN exp_works ew ON rs.work_id = ew.work_id
    WHERE rs.signal_code = 'F'
      AND rs.available = true
      AND ew.work_id IS NULL
""")).scalar()
print(f"  Count: {no_exp_f}")

# 6. Check confidence_coverage for these works
print("\n=== 6. CONFIDENCE COVERAGE CHECK ===")
coverage = db.execute(text("""
    SELECT rs.confidence_coverage, COUNT(*) as cnt
    FROM risk_scores rs
    JOIN works w ON rs.work_id = w.work_id
    LEFT JOIN (SELECT DISTINCT work_id FROM expenditures) e ON w.work_id = e.work_id
    WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
      AND rs.signal_code = 'F' AND rs.available = true
      AND e.work_id IS NULL
    GROUP BY rs.confidence_coverage
    LIMIT 5
""")).fetchall()
# Actually check the risk_scores coverage directly
coverage2 = db.execute(text("""
    SELECT DISTINCT rs.confidence_coverage
    FROM risk_scores rs
    JOIN works w ON rs.work_id = w.work_id
    LEFT JOIN (SELECT DISTINCT work_id FROM expenditures) e ON w.work_id = e.work_id
    WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
      AND e.work_id IS NULL
    LIMIT 5
""")).fetchall()
print(f"  Coverage values for no-exp works: {[float(c) for c in coverage2]}")

# 7. Verify: run live adapter on a no-expenditure work
print("\n=== 7. LIVE ADAPTER TEST ===")
row = db.execute(text("""
    SELECT w.work_id, w.work_description, w.work_category, w.state,
           w.constituency, w.is_sc_quota, w.is_st_quota,
           ws.sanction_amount, ws.sanction_date,
           wc.completion_date, wr.recommended_date,
           COALESCE(d.total_disbursed, 0) as total_disbursed,
           v.vendor_name
    FROM works w
    LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
    LEFT JOIN work_completions wc ON w.work_id = wc.work_id
    LEFT JOIN work_recommendations wr ON w.work_id = wr.work_id
    LEFT JOIN (SELECT work_id, SUM(fund_disbursed_amount) as total_disbursed FROM expenditures GROUP BY work_id) d ON w.work_id = d.work_id
    LEFT JOIN (SELECT DISTINCT ON (work_id) work_id, vendor_name FROM expenditures) v ON w.work_id = v.work_id
    WHERE w.work_id = :wid
"""), {'wid': no_exp_work}).fetchone()

print(f"  Work: {row[0]}")
print(f"  Sanction: {row[7]}")
print(f"  COALESCE(d.total_disbursed, 0): {row[11]}")

# Build input like the adapter does
work_input = {
    "work_id": row[0] or "",
    "work_title": (row[1] or "")[:100],
    "work_description": row[1] or "",
    "category": row[2] or "Normal/Others",
    "State": row[3] or "",
    "constituency": row[4] or "",
    "is_sc_quota": bool(row[5]),
    "is_st_quota": bool(row[6]),
    "sanction_amount": float(row[7]) if row[7] else None,
    "disbursed_amount": float(row[11]) if row[11] and float(row[11]) > 0 else None,
    "vendor_name": row[12] or "",
    "recommended_date": str(row[10]) if row[10] else None,
    "sanction_date": str(row[8]) if row[8] else None,
    "completion_date": str(row[9]) if row[9] else None,
}
print(f"  disbursed_amount passed to pipeline: {work_input['disbursed_amount']}")

predictor = get_predictor()
result = predictor.predict_new_work(work_input)
f_live = [s for s in result["signals"] if s["signal_code"] == "F"][0]
print(f"  Live F: available={f_live['available']}, score={f_live['score']}")
print(f"  Live F explanation: {f_live['explanation']}")

db.close()
print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
