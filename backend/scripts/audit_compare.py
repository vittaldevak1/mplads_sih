"""
COMPARE: DB stored values vs LIVE inference pipeline output for the same work.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
import json
from sqlalchemy import text
from app.database import SessionLocal
from app.ai.engine import get_predictor_with_stats

db = SessionLocal()
predictor = get_predictor_with_stats(db)

WEIGHTS = {'F':0.15,'D':0.12,'X':0.12,'V':0.10,'C':0.10,'Q':0.10,'O':0.08,'S':0.07,'G':0.08,'B':0.04,'Rs':0.04}

# Pick a 47.5 work
wid = db.execute(text("""
    SELECT w.work_id FROM risk_scores rs
    JOIN works w ON rs.work_id = w.work_id
    WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
      AND ABS(rs.composite_risk - 47.5) < 0.01
    LIMIT 1
""")).scalar()

print(f"Work: {wid}")

# Build the input the same way run_full_audit.py does
row = db.execute(text("""
    SELECT w.work_id, w.work_description, w.work_category, w.state,
           w.constituency, w.is_sc_quota, w.is_st_quota,
           ws.sanction_amount, ws.sanction_date,
           wc.completion_date,
           wr.recommended_date,
           COALESCE(d.total_disbursed, 0) as total_disbursed,
           v.vendor_name
    FROM works w
    LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
    LEFT JOIN work_completions wc ON w.work_id = wc.work_id
    LEFT JOIN work_recommendations wr ON w.work_id = wr.work_id
    LEFT JOIN (
        SELECT work_id, SUM(fund_disbursed_amount) as total_disbursed
        FROM expenditures GROUP BY work_id
    ) d ON w.work_id = d.work_id
    LEFT JOIN (
        SELECT DISTINCT ON (work_id) work_id, vendor_name
        FROM expenditures
    ) v ON w.work_id = v.work_id
    WHERE w.work_id = :wid
"""), {'wid': wid}).fetchone()

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

# Run LIVE prediction
result = predictor.predict_new_work(work_input)

print(f"\n=== LIVE PIPELINE OUTPUT ===")
print(f"composite_risk: {result['composite_risk']}")
print(f"confidence_coverage: {result['confidence_coverage']}")
print(f"inspection_priority: {result['inspection_priority']}")

print(f"\n=== LIVE SIGNALS ===")
for sig in result["signals"]:
    code = sig["signal_code"]
    score = sig.get("score")
    avail = sig["available"]
    w = sig["weight"]
    if avail and score is not None:
        contrib = float(score) * w
        print(f"  {code:4s}: score={float(score):6.2f}  w={w:.2f}  contrib={contrib:6.2f}  avail=True")
    else:
        print(f"  {code:4s}: score=None   w={w:.2f}  contrib= 0.00  avail=False")

# Compare with DB
print(f"\n=== DB STORED VALUES ===")
db_risk = db.execute(text("""
    SELECT composite_risk, confidence_coverage, inspection_priority
    FROM risk_scores WHERE work_id = :wid
"""), {'wid': wid}).fetchone()
print(f"composite_risk: {db_risk[0]}")
print(f"confidence_coverage: {db_risk[1]}")
print(f"inspection_priority: {db_risk[2]}")

print(f"\n=== DB SIGNALS ===")
db_sigs = db.execute(text("""
    SELECT signal_code, score, available, evidence FROM risk_signals
    WHERE work_id = :wid ORDER BY signal_code
"""), {'wid': wid}).fetchall()
for code, score, avail, ev in db_sigs:
    score_f = float(score) if score is not None else None
    w = WEIGHTS[code]
    if avail and score_f is not None:
        contrib = score_f * w
        print(f"  {code:4s}: score={score_f:6.2f}  w={w:.2f}  contrib={contrib:6.2f}  avail=True")
    else:
        print(f"  {code:4s}: score=None   w={w:.2f}  contrib= 0.00  avail=False")

# X signal evidence comparison
print(f"\n=== X SIGNAL EVIDENCE COMPARISON ===")
live_x = [s for s in result["signals"] if s["signal_code"] == "X"][0]
db_x = [s for s in db_sigs if s[0] == "X"][0]
print(f"Live evidence: {json.dumps(live_x.get('evidence'), indent=2)}")
print(f"Live top_matches: {json.dumps(live_x.get('top_matches', [])[:3], indent=2)}")
print(f"DB evidence: {db_x[3]}")

db.close()
