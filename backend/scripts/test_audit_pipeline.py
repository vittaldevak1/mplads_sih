"""Test the full audit pipeline directly."""
import sys
sys.path.insert(0, '.')
import json
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    rows = db.execute(text("""
        SELECT w.work_id, w.work_description, w.work_category, w.state,
               w.constituency, w.is_sc_quota, w.is_st_quota,
               ws.sanction_amount, ws.sanction_date,
               wc.completion_date,
               wr.recommended_date,
               e.vendor_name,
               COALESCE(d.total_disbursed, 0) as total_disbursed
        FROM works w
        LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
        LEFT JOIN work_completions wc ON w.work_id = wc.work_id
        LEFT JOIN work_recommendations wr ON w.work_id = wr.work_id
        LEFT JOIN (
            SELECT work_id, SUM(fund_disbursed_amount) as total_disbursed
            FROM expenditures
            GROUP BY work_id
        ) d ON w.work_id = d.work_id
        LEFT JOIN LATERAL (
            SELECT vendor_name FROM expenditures WHERE work_id = w.work_id LIMIT 1
        ) e ON true
        ORDER BY w.id
        LIMIT 5
    """)).fetchall()

    print(f"Loaded {len(rows)} rows from bulk query")

    print("\nLoading predictor...")
    from app.ai.engine import get_predictor
    predictor = get_predictor()
    print(f"Predictor loaded. X matrix: {predictor.sample_matrix.shape}")

    for row in rows:
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
            "disbursed_amount": float(row[12]) if row[12] and float(row[12]) > 0 else None,
            "vendor_name": row[11] or "",
            "recommended_date": str(row[10]) if row[10] else None,
            "sanction_date": str(row[8]) if row[8] else None,
            "completion_date": str(row[9]) if row[9] else None,
        }

        result = predictor.predict_new_work(work_input)
        print(f"  {row[0][:40]} -> risk={result['composite_risk']}, priority={result['inspection_priority']}, coverage={result['confidence_coverage']}")

    print("\nAll 5 works processed successfully!")
except Exception as ex:
    import traceback
    traceback.print_exc()
finally:
    db.close()
