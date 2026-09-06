"""Check signals for the 20 newly-audited works."""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Get the 20 most recently updated works
    r = db.execute(text("""
        SELECT work_id, composite_risk, inspection_priority
        FROM risk_scores
        WHERE work_id IN (
            SELECT work_id FROM risk_signals
            WHERE updated_at > NOW() - INTERVAL '5 minutes'
        )
        ORDER BY composite_risk DESC
        LIMIT 5
    """))
    print("=== Recently audited works ===")
    for row in r:
        work_id = row[0]
        print(f"\nWork: {work_id[:60]}...")
        print(f"  Risk: {row[1]} | Priority: {row[2]}")

        r2 = db.execute(text("""
            SELECT signal_code, score, available, explanation
            FROM risk_signals
            WHERE work_id = :wid
            ORDER BY signal_code
        """), {"wid": work_id})

        for sig in r2:
            code, score, available, explanation = sig
            score_str = f"{score}" if score is not None else "null"
            avail_str = "available" if available else "unavailable"
            expl_short = (explanation or "")[:80]
            print(f"  {code}: score={score_str}, {avail_str} | {expl_short}")

finally:
    db.close()
