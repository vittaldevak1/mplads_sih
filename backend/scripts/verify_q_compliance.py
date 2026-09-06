"""Verify Q logic: check if any constituency meets both thresholds."""
import sys
sys.path.insert(0, '.')
from sqlalchemy import text
from app.database import SessionLocal
from app.ai.engine import get_predictor_with_stats

def verify_q_logic():
    db = SessionLocal()
    predictor = get_predictor_with_stats(db)

    # Count constituencies by compliance status
    compliant = 0
    sc_only = 0
    st_only = 0
    both = 0
    
    examples = []
    
    for c, s in predictor.constituency_stats.items():
        total = s["total_works"]
        if total < 10:
            continue
        
        sc_pct = s["sc_works"] * 100.0 / total
        st_pct = s["st_works"] * 100.0 / total
        
        sc_ok = sc_pct >= 15.0
        st_ok = st_pct >= 7.5
        
        if sc_ok and st_ok:
            compliant += 1
            examples.append((c, sc_pct, st_pct, total, "COMPLIANT"))
        elif sc_ok:
            st_only += 1
            if len(examples) < 3:
                examples.append((c, sc_pct, st_pct, total, "SC OK, ST FAIL"))
        elif st_ok:
            sc_only += 1
            if len(examples) < 3:
                examples.append((c, sc_pct, st_pct, total, "ST OK, SC FAIL"))
        else:
            both += 1

    print(f"=== Constituency Compliance Summary ===")
    print(f"  Both thresholds met: {compliant}")
    print(f"  SC OK, ST fails:     {sc_only}")
    print(f"  ST OK, SC fails:     {sc_only}")
    print(f"  Both fail:           {both}")
    print(f"  Total:               {compliant + st_only + sc_only + both}")
    
    print(f"\n=== Examples of compliant constituencies ===")
    for c, sc, st, t, status in examples:
        sc_deficit = max(0, 15 - sc) / 15
        st_deficit = max(0, 7.5 - st) / 7.5
        q = max(sc_deficit, st_deficit) * 100
        print(f"  {c:30s} SC={sc:5.1f}% ST={st:5.1f}% works={t:5d} Q={q:.1f} [{status}]")

    db.close()

if __name__ == "__main__":
    verify_q_logic()
