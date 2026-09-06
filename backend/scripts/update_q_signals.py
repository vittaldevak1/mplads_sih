"""Update existing Q signals in risk_signals table to use new available=true with scores."""
import sys
sys.path.insert(0, '.')
import json
from sqlalchemy import text
from app.database import SessionLocal
from app.ai.engine import get_predictor_with_stats

def update_q_signals():
    db = SessionLocal()
    predictor = get_predictor_with_stats(db)
    
    print(f"Loaded {len(predictor.constituency_stats)} constituency stats")
    
    # Get all works that have Q signals
    rows = db.execute(text("""
        SELECT rs.id, rs.work_id, w.constituency
        FROM risk_signals rs
        JOIN works w ON rs.work_id = w.work_id
        WHERE rs.signal_code = 'Q'
    """)).fetchall()
    
    print(f"Found {len(rows)} Q signals to update")
    
    updated = 0
    for row in rows:
        rs_id = row[0]
        work_id = row[1]
        constituency = row[2]
        
        # Get Q signal from predictor
        available, score, evidence, explanation = predictor._quota_signal(constituency or "")
        
        evidence_json = json.dumps(evidence) if evidence else None
        
        db.execute(text("""
            UPDATE risk_signals
            SET available = :avail, score = :score, explanation = :expl, 
                evidence = CAST(:ev AS jsonb), updated_at = NOW()
            WHERE id = :id
        """), {
            "id": rs_id,
            "avail": available,
            "score": score,
            "expl": explanation,
            "ev": evidence_json,
        })
        
        updated += 1
        if updated % 5000 == 0:
            db.commit()
            print(f"  Updated {updated}/{len(rows)}")
    
    db.commit()
    print(f"Done. Updated {updated} Q signals.")
    
    # Verify
    cur = db.execute(text("""
        SELECT available, COUNT(*) FROM risk_signals WHERE signal_code='Q' GROUP BY available
    """))
    print("\nVerification:")
    for r in cur.fetchall():
        print(f"  available={r[0]}: {r[1]}")
    
    db.close()

if __name__ == "__main__":
    update_q_signals()
