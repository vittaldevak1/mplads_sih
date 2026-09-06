"""Verify signal quality for a high-risk work."""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Get highest risk work with signals
    r = db.execute(text("""
        SELECT rs.work_id, rs.composite_risk, rs.confidence_coverage, rs.inspection_priority
        FROM risk_scores rs
        WHERE rs.composite_risk > 80
        ORDER BY rs.composite_risk DESC
        LIMIT 1
    """))
    row = r.fetchone()
    if row:
        work_id = row[0]
        print(f"Work: {work_id}")
        print(f"Composite: {row[1]}")
        print(f"Coverage: {row[2]}")
        print(f"Priority: {row[3]}")

        # Get signals
        r2 = db.execute(text("""
            SELECT signal_code, signal_name, score, weight, available, explanation, evidence
            FROM risk_signals
            WHERE work_id = :wid
            ORDER BY signal_code
        """), {"wid": work_id})

        print("\nSignals:")
        for sig in r2:
            score_str = f"{sig[2]}" if sig[2] is not None else "N/A"
            print(f"  {sig[0]} ({sig[1]}): score={score_str}, weight={sig[3]}, available={sig[4]}")
            if sig[5]:
                print(f"    Explanation: {sig[5][:120]}")
            if sig[6]:
                print(f"    Evidence: {str(sig[6])[:150]}")

        # Get anomalies
        r3 = db.execute(text("""
            SELECT anomaly_type, severity, description
            FROM anomalies
            WHERE work_id = :wid
        """), {"wid": work_id})
        print("\nAnomalies:")
        for a in r3:
            print(f"  {a[0]} ({a[1]}): {a[2][:100]}")

finally:
    db.close()
