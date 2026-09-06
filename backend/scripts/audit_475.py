"""
DEEP AUDIT: Verify the exact DB values vs formula for 47.5 works.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
import json
from sqlalchemy import text
from app.database import SessionLocal

db = SessionLocal()
WEIGHTS = {'F':0.15,'D':0.12,'X':0.12,'V':0.10,'C':0.10,'Q':0.10,'O':0.08,'S':0.07,'G':0.08,'B':0.04,'Rs':0.04}

print("=" * 80)
print("DEEP AUDIT: WHY 47.5?")
print("=" * 80)

# Get 5 works with risk=47.5
rows = db.execute(text("""
    SELECT w.work_id, rs.composite_risk, rs.confidence_coverage
    FROM risk_scores rs
    JOIN works w ON rs.work_id = w.work_id
    WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
      AND ABS(rs.composite_risk - 47.5) < 0.01
    LIMIT 5
""")).fetchall()

for wid, risk, coverage in rows:
    print(f"\n{'='*80}")
    print(f"Work: {wid}")
    print(f"DB composite_risk: {risk}")
    print(f"DB confidence_coverage: {coverage}")

    signals = db.execute(text("""
        SELECT signal_code, score, available, evidence
        FROM risk_signals WHERE work_id = :wid ORDER BY signal_code
    """), {'wid': wid}).fetchall()

    print(f"\n  {'Code':4s} {'Avail':6s} {'Score':7s} {'Weight':6s} {'Contrib':8s}")
    print(f"  {'-'*35}")

    avail_sum = 0.0
    weighted_sum = 0.0
    for code, score, available, evidence in signals:
        w = WEIGHTS[code]
        score_f = float(score) if score is not None else None
        if available and score_f is not None:
            contrib = score_f * w
            weighted_sum += contrib
            avail_sum += w
            print(f"  {code:4s} {'True':6s} {score_f:7.2f} {w:6.2f} {contrib:8.2f}")
        else:
            print(f"  {code:4s} {'False':6s} {'None':>7s} {w:6.2f} {'0.00':>8s}")

    calc_risk = weighted_sum / avail_sum if avail_sum > 0 else 0
    print(f"\n  weighted_sum = {weighted_sum:.4f}")
    print(f"  avail_weight_sum = {avail_sum:.4f}")
    print(f"  CALCULATED risk = {weighted_sum:.4f} / {avail_sum:.4f} = {calc_risk:.2f}")
    print(f"  DB risk = {risk}")
    print(f"  MATCH: {abs(calc_risk - float(risk)) < 0.1}")

# Now check: what's different about the 60.9 works?
print(f"\n{'='*80}")
print("COMPARISON: 47.5 vs 60.9 works")
print(f"{'='*80}")

for target, label in [(47.5, "47.5"), (60.9, "60.9")]:
    row = db.execute(text("""
        SELECT w.work_id FROM risk_scores rs
        JOIN works w ON rs.work_id = w.work_id
        WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
          AND ABS(rs.composite_risk - :target) < 0.01
        LIMIT 1
    """), {'target': target}).fetchone()
    if row:
        wid = row[0]
        signals = db.execute(text("""
            SELECT signal_code, score, available FROM risk_signals
            WHERE work_id = :wid ORDER BY signal_code
        """), {'wid': wid}).fetchall()
        print(f"\n  Target={label}, Work={wid[:50]}")
        for code, score, available in signals:
            score_f = float(score) if score is not None else None
            w = WEIGHTS[code]
            if available and score_f is not None:
                print(f"    {code:4s}: score={score_f:6.2f}  w={w:.2f}  contrib={score_f*w:6.2f}")
            else:
                print(f"    {code:4s}: None    w={w:.2f}  (unavail)")

db.close()
