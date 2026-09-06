"""Q Score Distribution Analysis — real database, no code changes."""
import sys
sys.path.insert(0, '.')
import json
from sqlalchemy import text
from app.database import SessionLocal
from app.ai.engine import get_predictor_with_stats

def analyze():
    db = SessionLocal()
    predictor = get_predictor_with_stats(db)

    print("=" * 70)
    print("Q SIGNAL — SCORE DISTRIBUTION ANALYSIS")
    print("=" * 70)

    stats = predictor.constituency_stats

    # 1. Basic counts
    total_constituencies = len([s for s in stats.values() if s["total_works"] > 0])
    print(f"\nTotal unique constituencies (with >0 works): {total_constituencies}")

    # 2. Compute Q for every constituency
    q_buckets = {"0": 0, "0-25": 0, "25-50": 0, "50-75": 0, "75-99": 0, "100": 0}
    all_data = []
    total_works = 0
    works_q100 = 0
    works_q0 = 0

    for c, s in stats.items():
        total = s["total_works"]
        if total == 0:
            continue
        sc_pct = s["sc_works"] * 100.0 / total
        st_pct = s["st_works"] * 100.0 / total
        sc_deficit = max(0.0, 15.0 - sc_pct) / 15.0
        st_deficit = max(0.0, 7.5 - st_pct) / 7.5
        q = round(max(sc_deficit, st_deficit) * 100.0, 1)

        all_data.append({
            "constituency": c,
            "total": total,
            "sc_works": s["sc_works"],
            "st_works": s["st_works"],
            "sc_pct": round(sc_pct, 2),
            "st_pct": round(st_pct, 2),
            "q": q,
        })

        total_works += total
        if q == 100.0:
            works_q100 += total
            q_buckets["100"] += 1
        elif q == 0.0:
            works_q0 += total
            q_buckets["0"] += 1
        elif q <= 25:
            q_buckets["0-25"] += 1
        elif q <= 50:
            q_buckets["25-50"] += 1
        elif q <= 75:
            q_buckets["50-75"] += 1
        else:
            q_buckets["75-99"] += 1

    # 3. Q distribution by constituency count
    print(f"\n--- Q Score Distribution (by constituency count) ---")
    for bucket, count in q_buckets.items():
        pct = count * 100.0 / total_constituencies
        print(f"  Q = {bucket:>5s}: {count:5d} constituencies ({pct:5.1f}%)")

    # 4. Works-level percentages
    print(f"\n--- Works-Level Q Distribution ---")
    print(f"  Total works across all constituencies: {total_works}")
    print(f"  Works receiving Q = 100: {works_q100} ({works_q100*100.0/total_works:.1f}%)")
    print(f"  Works receiving Q = 0:   {works_q0} ({works_q0*100.0/total_works:.1f}%)")

    # 5. SC% and ST% distribution
    sc_vals = [d["sc_pct"] for d in all_data]
    st_vals = [d["st_pct"] for d in all_data]

    sc_zero = sum(1 for v in sc_vals if v == 0)
    st_zero = sum(1 for v in st_vals if v == 0)
    sc_100 = sum(1 for v in sc_vals if v == 100)
    st_100 = sum(1 for v in st_vals if v == 100)

    print(f"\n--- SC% Distribution across constituencies ---")
    print(f"  SC% = 0%:     {sc_zero} ({sc_zero*100.0/total_constituencies:.1f}%)")
    print(f"  SC% = 100%:   {sc_100} ({sc_100*100.0/total_constituencies:.1f}%)")
    print(f"  SC% 0-15%:    {sum(1 for v in sc_vals if 0 < v < 15)}")
    print(f"  SC% 15-50%:   {sum(1 for v in sc_vals if 15 <= v < 50)}")
    print(f"  SC% 50-100%:  {sum(1 for v in sc_vals if 50 <= v < 100)}")
    print(f"  Mean SC%:     {sum(sc_vals)/len(sc_vals):.2f}%")
    print(f"  Median SC%:   {sorted(sc_vals)[len(sc_vals)//2]:.2f}%")

    print(f"\n--- ST% Distribution across constituencies ---")
    print(f"  ST% = 0%:     {st_zero} ({st_zero*100.0/total_constituencies:.1f}%)")
    print(f"  ST% = 100%:   {st_100} ({st_100*100.0/total_constituencies:.1f}%)")
    print(f"  ST% 0-7.5%:   {sum(1 for v in st_vals if 0 < v < 7.5)}")
    print(f"  ST% 7.5-50%:  {sum(1 for v in st_vals if 7.5 <= v < 50)}")
    print(f"  ST% 50-100%:  {sum(1 for v in st_vals if 50 <= v < 100)}")
    print(f"  Mean ST%:     {sum(st_vals)/len(st_vals):.2f}%")
    print(f"  Median ST%:   {sorted(st_vals)[len(st_vals)//2]:.2f}%")

    # 6. Verify "zero constituencies meet both thresholds"
    both_met = [d for d in all_data if d["sc_pct"] >= 15.0 and d["st_pct"] >= 7.5]
    print(f"\n--- Threshold Verification ---")
    print(f"  Constituencies meeting BOTH SC >= 15% AND ST >= 7.5%: {len(both_met)}")
    if both_met:
        for d in both_met:
            print(f"    {d['constituency']}: SC={d['sc_pct']}% ST={d['st_pct']}% Q={d['q']}")

    sc_met = [d for d in all_data if d["sc_pct"] >= 15.0]
    st_met = [d for d in all_data if d["st_pct"] >= 7.5]
    print(f"  Constituencies meeting SC >= 15%: {len(sc_met)}")
    print(f"  Constituencies meeting ST >= 7.5%: {len(st_met)}")

    # 7. 10 example constituencies
    print(f"\n--- 10 Example Constituencies ---")
    print(f"  {'Constituency':30s} {'Total':>6s} {'SC':>5s} {'ST':>5s} {'SC%':>6s} {'ST%':>6s} {'Q':>6s}")
    print(f"  {'-'*30} {'-'*6} {'-'*5} {'-'*5} {'-'*6} {'-'*6} {'-'*6}")

    # Pick 10 diverse examples: some SC-designated, some ST-designated, some general
    sc_designated = [d for d in all_data if d["sc_pct"] == 100]
    st_designated = [d for d in all_data if d["st_pct"] == 100 and d["sc_pct"] == 0]
    general = [d for d in all_data if d["sc_pct"] == 0 and d["st_pct"] == 0]

    examples = sc_designated[:3] + st_designated[:3] + general[:4]
    examples.sort(key=lambda x: x["constituency"])

    for d in examples:
        print(f"  {d['constituency']:30s} {d['total']:6d} {d['sc_works']:5d} {d['st_works']:5d} {d['sc_pct']:5.1f}% {d['st_pct']:5.1f}% {d['q']:6.1f}")

    print(f"\n{'=' * 70}")
    db.close()

if __name__ == "__main__":
    analyze()
