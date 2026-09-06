"""
VERIFY: The audit ran before Q was implemented. Q was bulk-updated afterwards.
Check: (1) are ALL 47.5 works missing Q weight in composite?
       (2) X evidence — does it show matched work IDs?
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
print("VERIFICATION: Q IMPLEMENTATION TIMING")
print("=" * 80)

# 1. For 47.5 works: what is the sum of available weights EXCLUDING Q?
print("\n=== 1. COVERAGE ANALYSIS FOR 47.5 WORKS ===")
rows = db.execute(text("""
    SELECT rs.work_id, rs.composite_risk, rs.confidence_coverage
    FROM risk_scores rs
    JOIN works w ON rs.work_id = w.work_id
    WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
      AND ABS(rs.composite_risk - 47.5) < 0.01
    LIMIT 5
""")).fetchall()

for wid, risk, coverage in rows:
    sigs = db.execute(text("""
        SELECT signal_code, score, available FROM risk_signals
        WHERE work_id = :wid ORDER BY signal_code
    """), {'wid': wid}).fetchall()

    avail_without_q = sum(WEIGHTS[s[0]] for s in sigs if s[2] and s[1] is not None and s[0] != 'Q')
    avail_with_q = sum(WEIGHTS[s[0]] for s in sigs if s[2] and s[1] is not None)

    print(f"  Work: {wid[:50]}")
    print(f"    DB coverage: {coverage}")
    print(f"    Avail weights (excl Q): {avail_without_q:.2f}")
    print(f"    Avail weights (incl Q): {avail_with_q:.2f}")
    print(f"    Coverage matches excl Q: {abs(float(coverage) - avail_without_q) < 0.01}")
    print(f"    Coverage matches incl Q: {abs(float(coverage) - avail_with_q) < 0.01}")

# 2. Recomposite WITHOUT Q to verify 47.5
print("\n=== 2. RECOMPOSITE WITHOUT Q ===")
wid = db.execute(text("""
    SELECT w.work_id FROM risk_scores rs
    JOIN works w ON rs.work_id = w.work_id
    WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
      AND ABS(rs.composite_risk - 47.5) < 0.01
    LIMIT 1
""")).scalar()

sigs = db.execute(text("""
    SELECT signal_code, score, available FROM risk_signals
    WHERE work_id = :wid ORDER BY signal_code
"""), {'wid': wid}).fetchall()

ws_no_q = 0.0
denom_no_q = 0.0
for code, score, avail in sigs:
    if code == 'Q':
        continue
    w = WEIGHTS[code]
    if avail and score is not None:
        ws_no_q += float(score) * w
        denom_no_q += w

composite_no_q = round(ws_no_q / denom_no_q, 1) if denom_no_q > 0 else 0
print(f"  Work: {wid[:50]}")
print(f"  Composite WITHOUT Q: {composite_no_q}")
print(f"  DB value: 47.5")
print(f"  MATCH: {abs(composite_no_q - 47.5) < 0.1}")

# 3. X signal evidence check — do we have matched work IDs?
print("\n=== 3. X SIGNAL EVIDENCE CHECK ===")
rows = db.execute(text("""
    SELECT rs.evidence, rs.explanation FROM risk_signals rs
    JOIN works w ON rs.work_id = w.work_id
    WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
      AND rs.signal_code = 'X'
    LIMIT 3
""")).fetchall()

for ev, expl in rows:
    print(f"\n  Evidence: {ev}")
    print(f"  Explanation: {expl}")
    if isinstance(ev, str) and ev.startswith('{'):
        ev_dict = json.loads(ev)
        print(f"  Keys: {list(ev_dict.keys())}")
        has_matched_ids = any('work_id' in str(v) for v in ev_dict.values())
        print(f"  Contains matched work IDs: {has_matched_ids}")

# 4. Check: are X signals truly independent per work?
print("\n=== 4. X SIGNAL INDEPENDENCE CHECK ===")
# Pick 3 different works with same description
rows = db.execute(text("""
    SELECT w.work_id, rs.score, rs.evidence
    FROM risk_signals rs
    JOIN works w ON rs.work_id = w.work_id
    WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
      AND rs.signal_code = 'X'
    LIMIT 10
""")).fetchall()

unique_evidence = set()
for wid, score, ev in rows:
    unique_evidence.add(str(ev))
    print(f"  {wid[:45]:45s} score={score} ev={str(ev)[:60]}")

print(f"\n  Total samples: {len(rows)}")
print(f"  Unique evidence values: {len(unique_evidence)}")
print(f"  All identical: {len(unique_evidence) == 1}")

# 5. Why are ALL lighting works getting X=95?
print("\n=== 5. WHY X=95 FOR ALL LIGHTING WORKS? ===")
# The TF-IDF vectorizer sees 'Lighting of public spaces' as identical text
# Cosine similarity of a text with itself = 100%, but it's comparing
# against a HISTORICAL sample of 5000 works, not the current batch.
# If 'Lighting of public spaces' exists in the historical sample,
# max_similarity = ~90% (the TF-IDF isn't perfect but very high).

db.close()
print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
