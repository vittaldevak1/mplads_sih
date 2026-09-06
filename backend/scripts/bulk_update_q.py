"""Bulk update Q signals using pure SQL — fast."""
import sys
sys.path.insert(0, '.')
from sqlalchemy import text
from app.database import SessionLocal

SC_THRESHOLD = 15.0
ST_THRESHOLD = 7.5

def bulk_update_q():
    db = SessionLocal()
    
    # Step 1: Create temp table with constituency Q stats
    db.execute(text("""
        DROP TABLE IF EXISTS q_constituency_stats;
        CREATE TEMP TABLE q_constituency_stats AS
        SELECT
            constituency,
            COUNT(*) AS total_works,
            COUNT(*) FILTER (WHERE w.is_sc_quota = true) AS sc_works,
            COUNT(*) FILTER (WHERE w.is_st_quota = true) AS st_works
        FROM works w
        WHERE constituency IS NOT NULL
        GROUP BY constituency
    """))
    
    # Step 2: Bulk update risk_signals using a single UPDATE with JOIN
    result = db.execute(text("""
        UPDATE risk_signals rs
        SET
            available = true,
            score = GREATEST(
                0.0,
                GREATEST(
                    GREATEST(0, :sc_thresh - cs.sc_works * 100.0 / cs.total_works) / :sc_thresh,
                    GREATEST(0, :st_thresh - cs.st_works * 100.0 / cs.total_works) / :st_thresh
                ) * 100.0
            ),
            explanation = 'Allocation below configured SC/ST threshold — requires compliance verification.',
            evidence = jsonb_build_object(
                'constituency', w.constituency,
                'total_works', cs.total_works,
                'sc_works', cs.sc_works,
                'st_works', cs.st_works,
                'sc_percentage', ROUND(cs.sc_works * 100.0 / cs.total_works, 2),
                'st_percentage', ROUND(cs.st_works * 100.0 / cs.total_works, 2),
                'sc_threshold', :sc_thresh,
                'st_threshold', :st_thresh,
                'sc_deficit', ROUND(GREATEST(0, :sc_thresh - cs.sc_works * 100.0 / cs.total_works) / :sc_thresh, 4),
                'st_deficit', ROUND(GREATEST(0, :st_thresh - cs.st_works * 100.0 / cs.total_works) / :st_thresh, 4),
                'limiting_factor', CASE
                    WHEN GREATEST(0, :sc_thresh - cs.sc_works * 100.0 / cs.total_works) / :sc_thresh
                         >= GREATEST(0, :st_thresh - cs.st_works * 100.0 / cs.total_works) / :st_thresh
                    THEN 'SC' ELSE 'ST'
                END
            ),
            updated_at = NOW()
        FROM works w
        JOIN q_constituency_stats cs ON w.constituency = cs.constituency
        WHERE rs.work_id = w.work_id
          AND rs.signal_code = 'Q'
          AND cs.total_works > 0
    """), {"sc_thresh": SC_THRESHOLD, "st_thresh": ST_THRESHOLD})
    
    db.commit()
    print(f"Updated {result.rowcount} Q signals")
    
    # Step 3: Verify
    rows = db.execute(text("""
        SELECT available, COUNT(*) FROM risk_signals WHERE signal_code='Q' GROUP BY available
    """))
    print("\nVerification:")
    for r in rows.fetchall():
        print(f"  available={r[0]}: {r[1]}")
    
    # Step 4: Sample
    rows = db.execute(text("""
        SELECT w.constituency, rs.score, rs.available, rs.explanation
        FROM risk_signals rs
        JOIN works w ON rs.work_id = w.work_id
        WHERE rs.signal_code = 'Q'
        LIMIT 5
    """))
    print("\nSample:")
    for r in rows.fetchall():
        print(f"  {r[0]}: score={r[1]} available={r[2]}")
        print(f"    {r[3][:100]}")
    
    # Cleanup
    db.execute(text("DROP TABLE IF EXISTS q_constituency_stats"))
    db.close()

if __name__ == "__main__":
    bulk_update_q()
