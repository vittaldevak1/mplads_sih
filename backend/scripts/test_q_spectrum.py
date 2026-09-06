"""Test Q signal on SC/ST-heavy constituencies to verify varying scores."""
import sys
sys.path.insert(0, '.')
from sqlalchemy import text
from app.database import SessionLocal
from app.ai.engine import get_predictor_with_stats

def test_q_varied():
    db = SessionLocal()
    predictor = get_predictor_with_stats(db)

    # Show constituency stats for a few known SC-heavy constituencies
    test_constituencies = ["PUNJABI BAGH", "AMBEDKAR NAGAR", "PURNIA", "ADILABAD(ST)", "ALIPURDUARS(ST)"]
    
    print("=== Constituency Stats for Known SC/ST Areas ===\n")
    for c in test_constituencies:
        stats = predictor.constituency_stats.get(c)
        if stats:
            total = stats["total_works"]
            sc = stats["sc_works"]
            st = stats["st_works"]
            sc_pct = sc * 100.0 / total if total else 0
            st_pct = st * 100.0 / total if total else 0
            print(f"  {c}: total={total}, SC={sc} ({sc_pct:.1f}%), ST={st} ({st_pct:.1f}%)")
        else:
            print(f"  {c}: NOT FOUND")

    print("\n=== Testing works from SC-heavy constituencies ===\n")
    
    # Get works from constituencies that actually have SC/ST allocation
    rows = db.execute(text("""
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
            WHERE is_sc_quota = true
            GROUP BY constituency
            HAVING COUNT(*) FILTER (WHERE is_sc_quota) * 100.0 / COUNT(*) > 10
            LIMIT 5
        )
        ORDER BY RANDOM() LIMIT 10
    """)).fetchall()

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
            "disbursed_amount": float(row[11]) if row[11] and float(row[11]) > 0 else None,
            "vendor_name": row[12] or "",
            "recommended_date": str(row[10]) if row[10] else None,
            "sanction_date": str(row[8]) if row[8] else None,
            "completion_date": str(row[9]) if row[9] else None,
        }
        result = predictor.predict_new_work(work_input)
        q_signal = next(s for s in result["signals"] if s["signal_code"] == "Q")
        e = q_signal["evidence"] or {}
        print(f"  {row[4]:25s} | SC={e.get('sc_percentage', '?')}% ST={e.get('st_percentage', '?')}% | Q={q_signal['score']} | limiting={e.get('limiting_factor', '?')}")

    # Show the full spectrum of Q scores
    print("\n=== Full Q Spectrum Across All Constituencies ===\n")
    all_stats = predictor.constituency_stats
    scores = []
    for c, s in all_stats.items():
        total = s["total_works"]
        if total == 0:
            continue
        sc_pct = s["sc_works"] * 100.0 / total
        st_pct = s["st_works"] * 100.0 / total
        sc_deficit = max(0.0, 15.0 - sc_pct) / 15.0
        st_deficit = max(0.0, 7.5 - st_pct) / 7.5
        q = max(sc_deficit, st_deficit) * 100.0
        scores.append((c, q, sc_pct, st_pct, total))

    scores.sort(key=lambda x: x[1])
    
    print(f"{'Constituency':30s} {'Q':>6s} {'SC%':>6s} {'ST%':>6s} {'Works':>6s}")
    print("-" * 60)
    
    # Show bottom 5 (lowest Q = best compliance)
    print("--- LOWEST Q (best compliance) ---")
    for c, q, sc, st, t in scores[:5]:
        print(f"  {c:28s} {q:6.1f} {sc:5.1f}% {st:5.1f}% {t:6d}")
    
    # Show middle 5
    mid = len(scores) // 2
    print(f"\n--- MIDDLE Q (index ~{mid}) ---")
    for c, q, sc, st, t in scores[mid-2:mid+3]:
        print(f"  {c:28s} {q:6.1f} {sc:5.1f}% {st:5.1f}% {t:6d}")
    
    # Show top 5 (highest Q = worst compliance)
    print(f"\n--- HIGHEST Q (worst compliance) ---")
    for c, q, sc, st, t in scores[-5:]:
        print(f"  {c:28s} {q:6.1f} {sc:5.1f}% {st:5.1f}% {t:6d}")
    
    print(f"\nTotal constituencies: {len(scores)}")
    print(f"Q range: {min(s[1] for s in scores):.1f} - {max(s[1] for s in scores):.1f}")
    
    db.close()

if __name__ == "__main__":
    test_q_varied()
