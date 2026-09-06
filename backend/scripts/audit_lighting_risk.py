"""
AUDIT: Risk scoring for 'Lighting of public spaces' works.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
import json
from sqlalchemy import text
from app.database import SessionLocal

db = SessionLocal()
WEIGHTS = {'F':0.15,'D':0.12,'X':0.12,'V':0.10,'C':0.10,'Q':0.10,'O':0.08,'S':0.07,'G':0.08,'B':0.04,'Rs':0.04}
AVAILABLE = ['F','D','X','V','Q','B','Rs']
UNAVAILABLE = ['C','O','S','G']
AVAIL_W = sum(WEIGHTS[c] for c in AVAILABLE)

print("=" * 80)
print("AUDIT: RISK SCORING FOR 'LIGHTING OF PUBLIC SPACES' WORKS")
print("=" * 80)

# 1. Score distribution
print("\n=== 1. RISK SCORE DISTRIBUTION ===")
rows = db.execute(text("""
    SELECT rs.composite_risk, COUNT(*) as cnt
    FROM risk_scores rs
    JOIN works w ON rs.work_id = w.work_id
    WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
    GROUP BY rs.composite_risk ORDER BY cnt DESC LIMIT 15
""")).fetchall()
for r in rows:
    bar = '#' * min(r[1] // 200, 50)
    print(f"  {r[0]:6.2f}: {r[1]:6d}  {bar}")

# 2. Sample 10 works with full signal breakdown
print("\n=== 2. SAMPLE WORKS — FULL SIGNAL BREAKDOWN ===")
rows = db.execute(text("""
    SELECT w.work_id, w.state, w.constituency, rs.composite_risk, rs.confidence_coverage
    FROM risk_scores rs
    JOIN works w ON rs.work_id = w.work_id
    WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
    ORDER BY RANDOM() LIMIT 10
""")).fetchall()

for r in rows:
    wid, state, constituency, risk, coverage = r
    print(f"\n  Work: {wid[:70]}")
    print(f"  State: {state} | Constituency: {constituency}")

    signals = db.execute(text("""
        SELECT signal_code, score, available, evidence FROM risk_signals
        WHERE work_id = :wid ORDER BY signal_code
    """), {'wid': wid}).fetchall()

    weighted_sum = 0.0
    for s in signals:
        code, score, available, evidence = s
        w = WEIGHTS.get(code, 0)
        if available and score is not None:
            score_f = float(score)
            contrib = score_f * w
            weighted_sum += contrib
            ev_str = str(evidence)[:80] if evidence else "None"
            print(f"    {code:3s}: score={score_f:6.2f}  w={w:.2f}  contrib={contrib:6.2f}  ev={ev_str}")
        else:
            print(f"    {code:3s}: score=None   w={w:.2f}  contrib= 0.00  (unavailable)")

    renorm = (weighted_sum / AVAIL_W) * 100
    print(f"  => weighted_sum={weighted_sum:.4f}, renorm=({weighted_sum:.4f}/{AVAIL_W:.2f})*100={renorm:.2f}, DB={risk:.2f}")

# 3. Are signals independent? Check evidence uniqueness
print("\n=== 3. SIGNAL INDEPENDENCE CHECK (are scores cached/reused?) ===")
for code in AVAILABLE:
    rows = db.execute(text(f"""
        SELECT rs.score, rs.evidence, rs.work_id
        FROM risk_signals rs
        JOIN works w ON rs.work_id = w.work_id
        WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
          AND rs.signal_code = '{code}'
        LIMIT 20
    """)).fetchall()
    scores = set()
    ev_hashes = set()
    for s in rows:
        scores.add(float(s[0]) if s[0] is not None else None)
        ev_hashes.add(str(s[1])[:200] if s[1] else "None")
    print(f"  {code:3s}: {len(scores)} distinct scores, {len(ev_hashes)} distinct evidence (20 samples)")

# 4. X signal deep dive — the big one
print("\n=== 4. X SIGNAL DEEP DIVE ===")
rows = db.execute(text("""
    SELECT rs.work_id, rs.score, rs.available, rs.evidence
    FROM risk_signals rs
    JOIN works w ON rs.work_id = w.work_id
    WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
      AND rs.signal_code = 'X'
    LIMIT 5
""")).fetchall()
for r in rows:
    print(f"\n  Work: {r[0][:60]}")
    print(f"  Score: {r[1]}, Available: {r[2]}")
    ev = r[3]
    score_f = float(r[1]) if r[1] is not None else None
    print(f"  Score: {score_f}, Available: {r[2]}")
    ev = r[3]
    if isinstance(ev, str) and ev.startswith('['):
        try:
            ev_list = json.loads(ev)
            print(f"  Evidence ({len(ev_list)} matched works):")
            for e in ev_list[:5]:
                print(f"    - {e}")
        except:
            print(f"  Evidence: {str(ev)[:200]}")
    elif ev is None:
        print(f"  Evidence: None")
    else:
        print(f"  Evidence: {str(ev)[:200]}")

# 5. Q signal check
print("\n=== 5. Q SIGNAL CHECK ===")
rows = db.execute(text("""
    SELECT rs.available, rs.score, COUNT(*) as cnt
    FROM risk_signals rs
    JOIN works w ON rs.work_id = w.work_id
    WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
      AND rs.signal_code = 'Q'
    GROUP BY rs.available, rs.score
""")).fetchall()
for r in rows:
    print(f"  Available={r[0]}, Score={r[1]}: {r[2]} works")

# 6. F signal — same description but different work_ids
print("\n=== 6. F SIGNAL — IS F DEPENDENT ON SANCTION AMOUNT? ===")
rows = db.execute(text("""
    SELECT w.work_id, ws.sanction_amount, rs.score as f_score
    FROM risk_signals rs
    JOIN works w ON rs.work_id = w.work_id
    LEFT JOIN work_sanctions ws ON ws.work_id = w.work_id
    WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
      AND rs.signal_code = 'F'
    ORDER BY ws.sanction_amount
    LIMIT 15
""")).fetchall()
for r in rows:
    print(f"  Sanction={r[1]:>15}  F_score={r[2]}  Work={r[0][:50]}")

# 7. Evidence for X — how many unique matched works?
print("\n=== 7. X EVIDENCE — HOW MANY UNIQUE MATCHED WORKS? ===")
rows = db.execute(text("""
    SELECT rs.evidence FROM risk_signals rs
    JOIN works w ON rs.work_id = w.work_id
    WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
      AND rs.signal_code = 'X'
    LIMIT 5
""")).fetchall()
for i, r in enumerate(rows):
    ev = r[0]
    if isinstance(ev, str) and ev.startswith('['):
        try:
            ev_list = json.loads(ev)
            matched_ids = [e.get('work_id','?') for e in ev_list if isinstance(e, dict)]
            print(f"  Sample {i+1}: {len(ev_list)} matches, {len(matched_ids)} work IDs")
            for mid in matched_ids[:3]:
                print(f"    {mid}")
        except:
            print(f"  Sample {i+1}: parse error, raw={str(ev)[:100]}")
    else:
        print(f"  Sample {i+1}: evidence={str(ev)[:100]}")

# 8. Why 47.5 specifically?
print("\n=== 8. WHY 47.5? DECOMPOSITION ===")
row = db.execute(text("""
    SELECT rs.work_id FROM risk_scores rs
    JOIN works w ON rs.work_id = w.work_id
    WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
      AND ABS(rs.composite_risk - 47.5) < 0.01
    LIMIT 1
""")).fetchone()
if row:
    wid = row[0]
    print(f"  Example work with 47.5: {wid[:60]}")
    signals = db.execute(text("""
        SELECT signal_code, score, available FROM risk_signals
        WHERE work_id = :wid ORDER BY signal_code
    """), {'wid': wid}).fetchall()
    weighted_sum = 0.0
    for s in signals:
        code, score, available = s
        score_f = float(score) if score is not None else None
        w = WEIGHTS[code]
        if available and score_f is not None:
            contrib = score_f * w
            weighted_sum += contrib
            print(f"    {code:3s}: score={score_f:6.2f}  w={w:.2f}  contrib={contrib:6.2f}")
        else:
            print(f"    {code:3s}: score=None   w={w:.2f}  (unavailable)")
    renorm = (weighted_sum / AVAIL_W) * 100
    print(f"  weighted_sum = {weighted_sum:.4f}")
    print(f"  renormalized = ({weighted_sum:.4f} / {AVAIL_W:.2f}) * 100 = {renorm:.2f}")

# 9. How many of those 7697 have EXACTLY the same signal scores?
print("\n=== 9. HOW MANY OF THE 7697 HAVE IDENTICAL SIGNAL SCORES? ===")
row = db.execute(text("""
    SELECT rs.work_id FROM risk_scores rs
    JOIN works w ON rs.work_id = w.work_id
    WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
      AND ABS(rs.composite_risk - 47.5) < 0.01
    LIMIT 1
""")).fetchone()
if row:
    wid = row[0]
    sigs = db.execute(text("""
        SELECT signal_code, score, available FROM risk_signals
        WHERE work_id = :wid ORDER BY signal_code
    """), {'wid': wid}).fetchall()
    sig_tuple = tuple((s[0], float(s[1]) if s[1] else None, s[2]) for s in sigs)
    
    # Count works with identical signal pattern
    conditions = []
    params = {}
    for code, score, avail in sigs:
        score_f = float(score) if score is not None else None
        if avail and score_f is not None:
            conditions.append(f"rs_{code}.score = :s_{code}")
            params[f's_{code}'] = score_f
        else:
            conditions.append(f"rs_{code}.available = false")
    
    join_clauses = []
    select_clauses = []
    for code in ['F','D','X','V','C','Q','O','S','G','B','Rs']:
        join_clauses.append(f"JOIN risk_signals rs_{code} ON rs_{code}.work_id = w.work_id AND rs_{code}.signal_code = '{code}'")
        select_clauses.append(f"rs_{code}.score as {code}_score")
    
    where_extra = " AND ".join(conditions)
    count_sql = f"""
        SELECT COUNT(*) FROM works w
        {' '.join(join_clauses)}
        WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
          AND {where_extra}
    """
    count = db.execute(text(count_sql), params).scalar()
    print(f"  Works with EXACT same signal pattern as {wid[:40]}: {count}")

db.close()
print("\n" + "=" * 80)
print("AUDIT COMPLETE")
