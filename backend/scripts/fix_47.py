"""Fix 29 stale 47.5 composite risk scores using persisted signals."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
from sqlalchemy import text
from app.database import SessionLocal

W = {'F':0.15,'D':0.12,'X':0.12,'V':0.10,'C':0.10,'Q':0.10,'O':0.08,'S':0.07,'G':0.08,'B':0.04,'Rs':0.04}
db = SessionLocal()

# Get stale work IDs
stale_ids = [r[0] for r in db.execute(text(
    "SELECT work_id FROM risk_scores WHERE ABS(composite_risk - 47.5) < 0.01"
)).fetchall()]
print(f"Stale works: {len(stale_ids)}")

if not stale_ids:
    print("Nothing to fix.")
    db.close()
    sys.exit(0)

# Get signals for these works
rows = db.execute(text("""
    SELECT work_id, signal_code, score, available FROM risk_signals
    WHERE work_id = ANY(:ids)
"""), {'ids': stale_ids}).fetchall()

from collections import defaultdict
sigs = defaultdict(dict)
for wid, code, score, avail in rows:
    sigs[wid][code] = (score, avail)

updated = 0
for wid in stale_ids:
    ws = sigs.get(wid, {})
    num = den = 0.0
    for code, w in W.items():
        if code in ws:
            sc, av = ws[code]
            if av and sc is not None:
                num += w * float(sc)
                den += w
    new_c = round(num/den, 1) if den else 0.0
    new_cov = round(den, 4) if den else 0.0
    new_p = 'HIGH' if new_c >= 65 else 'MEDIUM' if new_c >= 40 else 'LOW'

    db.execute(text("""
        UPDATE risk_scores SET composite_risk=:c, confidence_coverage=:v,
               inspection_priority=:p, updated_at=NOW()
        WHERE work_id=:w AND ABS(composite_risk - 47.5) < 0.01
    """), {'c': new_c, 'v': new_cov, 'p': new_p, 'w': wid})
    updated += 1

db.commit()
print(f"Updated: {updated}")

# Verify
remaining = db.execute(text(
    "SELECT COUNT(*) FROM risk_scores WHERE ABS(composite_risk - 47.5) < 0.01"
)).scalar()
print(f"Remaining at 47.5: {remaining}")

# Show distribution
rows = db.execute(text("""
    SELECT inspection_priority, COUNT(*) FROM risk_scores
    GROUP BY inspection_priority ORDER BY inspection_priority
""")).fetchall()
for p, c in rows:
    print(f"  {p or 'NONE':10s}: {c:6d}")

# Verify signals untouched
sig_count = db.execute(text("SELECT COUNT(*) FROM risk_signals")).scalar()
print(f"Risk signals total: {sig_count} (should be 969221)")
db.close()
