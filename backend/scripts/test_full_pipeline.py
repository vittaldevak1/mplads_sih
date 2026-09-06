"""Test a work with more available signals to verify full pipeline."""
import sys
sys.path.insert(0, '.')
from sqlalchemy import text
from app.database import SessionLocal
from app.ai.engine import get_predictor_with_stats

def test_full_pipeline():
    db = SessionLocal()
    predictor = get_predictor_with_stats(db)

    # Get a work with sanction_amount AND disbursed (to get F, D, B, Rs, Q)
    row = db.execute(text("""
        SELECT w.work_id, w.work_description, w.work_category, w.state,
               w.constituency, w.is_sc_quota, w.is_st_quota,
               ws.sanction_amount, ws.sanction_date,
               wc.completion_date,
               wr.recommended_date,
               COALESCE(d.total_disbursed, 0) as total_disbursed,
               v.vendor_name
        FROM works w
        JOIN work_sanctions ws ON w.work_id = ws.work_id
        JOIN expenditures e ON w.work_id = e.work_id
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
        WHERE ws.sanction_amount > 0
        LIMIT 1
    """)).fetchone()

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

    result = predictor.predict_new_work(work_input)

    print(f"Work: {row[0]}")
    print(f"Constituency: {row[4]}")
    print(f"\n=== All 11 Signals ===")
    available_count = 0
    for s in result["signals"]:
        status = "YES" if s["available"] else "no"
        score_str = f"{s['score']:.1f}" if s["score"] is not None else "null"
        print(f"  {s['signal_code']:3s} score={score_str:>6s} weight={s['weight']:.2f} avail={status}")
        if s["available"] and s["score"] is not None:
            available_count += 1

    print(f"\n  Available: {available_count}/11")
    print(f"  Coverage: {result['confidence_coverage']:.2%}")
    print(f"  Composite: {result['composite_risk']:.1f}")
    print(f"  Priority: {result['inspection_priority']}")
    
    q_sig = next(s for s in result["signals"] if s["signal_code"] == "Q")
    print(f"\n=== Q Signal Detail ===")
    print(f"  Score: {q_sig['score']}")
    print(f"  Evidence: {q_sig['evidence']}")
    print(f"  Explanation: {q_sig['explanation']}")

    db.close()

if __name__ == "__main__":
    test_full_pipeline()
