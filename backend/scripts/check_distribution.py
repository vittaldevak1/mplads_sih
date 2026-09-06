import sys; sys.stdout.reconfigure(encoding='utf-8'); sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
from sqlalchemy import text
from app.database import SessionLocal

db = SessionLocal()

print("=== FULL DISTRIBUTION ===")
rows = db.execute(text("""
    SELECT composite_risk, COUNT(*) as cnt
    FROM risk_scores
    GROUP BY composite_risk
    ORDER BY cnt DESC
""")).fetchall()
for r in rows:
    bar = '#' * min(r[1] // 500, 50)
    print(f"  {float(r[0]):6.1f}: {r[1]:6d}  {bar}")

print("\n=== WORKS AT 47.5 ===")
rows = db.execute(text("""
    SELECT rs.work_id, rs.composite_risk, rs.confidence_coverage
    FROM risk_scores rs
    WHERE ABS(rs.composite_risk - 47.5) < 0.01
    LIMIT 10
""")).fetchall()
for r in rows:
    print(f"  {r[0][:50]:50s} risk={float(r[1]):.1f}  coverage={float(r[2]):.4f}")

print("\n=== WORKS AT 60.0 ===")
rows = db.execute(text("""
    SELECT COUNT(*) FROM risk_scores WHERE ABS(composite_risk - 60.0) < 0.05
""")).scalar()
print(f"  Count: {rows}")

print("\n=== WORKS AT 47.5 WITH THEIR SIGNALS ===")
rows = db.execute(text("""
    SELECT rs.work_id, rs.composite_risk, rs.confidence_coverage
    FROM risk_scores rs
    WHERE ABS(rs.composite_risk - 47.5) < 0.01
    LIMIT 3
""")).fetchall()
for wid, risk, cov in rows:
    sigs = db.execute(text("""
        SELECT signal_code, score, available FROM risk_signals
        WHERE work_id = :wid ORDER BY signal_code
    """), {'wid': wid}).fetchall()
    print(f"\n  {wid[:50]:50s} risk={float(risk):.1f}  coverage={float(cov):.4f}")
    for code, score, avail in sigs:
        score_f = float(score) if score is not None else None
        print(f"    {code:3s}: score={score_f}  avail={avail}")

db.close()
