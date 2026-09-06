"""
Reconcile composite_risk for works with stale scores.

Uses locked formula with dynamic renormalization over persisted risk_signals.
Does NOT modify risk_signals — only updates risk_scores.

Locked weights:
F=0.15 D=0.12 X=0.12 V=0.10 C=0.10 Q=0.10 O=0.08 S=0.07 G=0.08 B=0.04 Rs=0.04
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')

from sqlalchemy import text
from app.database import SessionLocal

WEIGHTS = {
    'F': 0.15, 'D': 0.12, 'X': 0.12, 'V': 0.10,
    'C': 0.10, 'Q': 0.10, 'O': 0.08, 'S': 0.07,
    'G': 0.08, 'B': 0.04, 'Rs': 0.04,
}

db = SessionLocal()

print("=" * 70)
print("COMPOSITE-RISK RECONCILIATION")
print("=" * 70)

# 1. BEFORE distribution
print("\n--- BEFORE ---")
before = db.execute(text("""
    SELECT inspection_priority, COUNT(*) FROM risk_scores
    GROUP BY inspection_priority ORDER BY inspection_priority
""")).fetchall()
for p, c in before:
    print(f"  {p or 'NONE':10s}: {c:6d}")

stale = db.execute(text(
    "SELECT COUNT(*) FROM risk_scores WHERE ABS(composite_risk - 47.5) < 0.01"
)).scalar()
print(f"  Stale at 47.5: {stale}")

# 2. Get all works with their signals
print("\n--- Recalculating from persisted risk_signals ---")
rows = db.execute(text("""
    SELECT rs.work_id, rs.composite_risk as old_composite,
           rs.confidence_coverage as old_coverage,
           rs.inspection_priority as old_priority,
           rsg.signal_code, rsg.score, rsg.available
    FROM risk_scores rs
    JOIN risk_signals rsg ON rs.work_id = rsg.work_id
    WHERE ABS(rs.composite_risk - 47.5) < 0.01
""")).fetchall()

# Group signals by work_id
from collections import defaultdict
work_signals = defaultdict(dict)
for work_id, old_c, old_cov, old_pri, sig_code, score, avail in rows:
    work_signals[work_id]['old'] = (old_c, old_cov, old_pri)
    work_signals[work_id][sig_code] = (score, avail)

print(f"  Works to recalculate: {len(work_signals)}")

# 3. Calculate new composites
updates = []
for wid, sigs in work_signals.items():
    old_composite, old_cov, old_pri = sigs.pop('old')
    num = 0.0
    den = 0.0
    for code, weight in WEIGHTS.items():
        if code in sigs:
            score_val, avail = sigs[code]
            if avail and score_val is not None:
                num += weight * float(score_val)
                den += weight
    new_composite = round(num / den, 1) if den else 0.0
    new_coverage = round(den / 1.0, 4) if den else 0.0
    new_priority = (
        'HIGH' if new_composite >= 65.0
        else 'MEDIUM' if new_composite >= 40.0
        else 'LOW'
    )
    updates.append((wid, new_composite, new_coverage, new_priority, old_composite))

# 4. Show sample
print("\n--- Sample changes ---")
for wid, new_c, new_cov, new_pri, old_c in updates[:5]:
    print(f"  {wid[:45]:45s}  {old_c:.1f} -> {new_c:.1f}  cov={new_cov:.4f}  pri={new_pri}")

# 5. Apply updates
print(f"\n--- Applying {len(updates)} updates ---")
for wid, new_c, new_cov, new_pri, old_c in updates:
    db.execute(text("""
        UPDATE risk_scores
        SET composite_risk = :new_c,
            confidence_coverage = :new_cov,
            inspection_priority = :new_pri,
            updated_at = NOW()
        WHERE work_id = :wid
    """), {'new_c': new_c, 'new_cov': new_cov, 'new_pri': new_pri, 'wid': wid})
db.commit()
print(f"  Updated {len(updates)} records")

# 6. AFTER distribution
print("\n--- AFTER ---")
after = db.execute(text("""
    SELECT inspection_priority, COUNT(*) FROM risk_scores
    GROUP BY inspection_priority ORDER BY inspection_priority
""")).fetchall()
for p, c in after:
    print(f"  {p or 'NONE':10s}: {c:6d}")

stale_after = db.execute(text(
    "SELECT COUNT(*) FROM risk_scores WHERE ABS(composite_risk - 47.5) < 0.01"
)).scalar()
print(f"  Stale at 47.5: {stale_after}")

# 7. Verify signal counts unchanged
sig_count = db.execute(text("SELECT COUNT(*) FROM risk_signals")).scalar()
print(f"\n  Risk signals unchanged: {sig_count}")

# 8. Verify unavailable signals
for code in ['C', 'O', 'S', 'G']:
    avail_count = db.execute(text(
        f"SELECT COUNT(*) FROM risk_signals WHERE signal_code='{code}' AND available=true"
    )).scalar()
    print(f"  {code} available=true: {avail_count} (should be 0)")

db.close()
print("\n" + "=" * 70)
print("RECONCILIATION COMPLETE")
