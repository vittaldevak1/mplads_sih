"""Test Q signal implementation on real works."""
import sys
sys.path.insert(0, '.')
import json
from sqlalchemy import text
from app.database import SessionLocal
from app.ai.engine import get_predictor_with_stats
from app.ai.engine.inference_pipeline import UNAVAILABLE_MVP

def test_q_signal():
    db = SessionLocal()
    predictor = get_predictor_with_stats(db)
    
    print(f"Constituency stats loaded: {len(predictor.constituency_stats)} constituencies")
    print(f"Q signal available: {'Q' not in UNAVAILABLE_MVP}")
    print(f"Q threshold: SC >= {predictor.SC_THRESHOLD}%, ST >= {predictor.ST_THRESHOLD}%")
    print()
    
    # Test 1: Works from different constituencies
    test_works = db.execute(text("""
        SELECT w.work_id, w.work_description, w.work_category, w.state,
               w.constituency, w.is_sc_quota, w.is_st_quota,
               ws.sanction_amount, ws.sanction_date,
               wc.completion_date,
               wr.recommended_date,
               COALESCE(d.total_disbursed, 0) as total_disbursed,
               v.vendor_name
        FROM works w
        LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
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
        WHERE w.constituency IN (
            SELECT constituency FROM works 
            GROUP BY constituency 
            HAVING COUNT(*) >= 50
            ORDER BY RANDOM() LIMIT 5
        )
        ORDER BY RANDOM() LIMIT 15
    """)).fetchall()
    
    print(f"Testing {len(test_works)} works from 5 constituencies:\n")
    
    for row in test_works:
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
        
        q_signal = next(s for s in result["signals"] if s["signal_code"] == "Q")
        
        print(f"Work: {row[0][:60]}...")
        print(f"  Constituency: {row[4]}")
        print(f"  SC={row[5]}, ST={row[6]}")
        print(f"  Q available: {q_signal['available']}")
        print(f"  Q score: {q_signal['score']}")
        print(f"  Q explanation: {q_signal['explanation'][:80]}...")
        if q_signal['evidence']:
            e = q_signal['evidence']
            print(f"  Evidence: SC={e.get('sc_percentage')}% ST={e.get('st_percentage')}% "
                  f"limiting={e.get('limiting_factor')}")
        print()
    
    # Test 2: Check overall Q distribution
    print("\n=== Q Signal Distribution (all works) ===")
    q_scores = []
    for row in test_works:
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
        q_signal = next(s for s in result["signals"] if s["signal_code"] == "Q")
        if q_signal["available"] and q_signal["score"] is not None:
            q_scores.append(q_signal["score"])
    
    if q_scores:
        print(f"Available Q scores: {len(q_scores)}/{len(test_works)}")
        print(f"Mean: {sum(q_scores)/len(q_scores):.1f}")
        print(f"Min: {min(q_scores):.1f}, Max: {max(q_scores):.1f}")
    
    db.close()

if __name__ == "__main__":
    test_q_signal()
