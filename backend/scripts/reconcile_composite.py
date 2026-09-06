import sys; sys.stdout.reconfigure(encoding='utf-8'); sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
from sqlalchemy import text
from app.database import SessionLocal

db = SessionLocal()

print("=" * 80)
print("COMPOSITE-RISK RECONCILIATION")
print("=" * 80)

# 1. BEFORE distribution
print("\n=== 1. BEFORE: CURRENT DISTRIBUTION ===")
before_dist = db.execute(text("""
    SELECT composite_risk, COUNT(*) as cnt
    FROM risk_scores GROUP BY composite_risk ORDER BY cnt DESC LIMIT 20
""")).fetchall()
for r in before_dist:
    print(f"  {float(r[0]):6.1f}: {r[1]:6d}")

stale_475 = db.execute(text("SELECT COUNT(*) FROM risk_scores WHERE ABS(composite_risk - 47.5) < 0.01")).scalar()
print(f"\n  Works at 47.5: {stale_475}")

# 2. Recalculate using locked formula
print("\n=== 2. RECALCULATING ===")

# Create pivot table
db.execute(text("DROP TABLE IF EXISTS signal_pivot"))
db.execute(text("""
    CREATE TEMP TABLE signal_pivot AS
    SELECT work_id,
        MAX(CASE WHEN signal_code='F' THEN score END) as F_score,
        MAX(CASE WHEN signal_code='D' THEN score END) as D_score,
        MAX(CASE WHEN signal_code='X' THEN score END) as X_score,
        MAX(CASE WHEN signal_code='V' THEN score END) as V_score,
        MAX(CASE WHEN signal_code='Q' THEN score END) as Q_score,
        MAX(CASE WHEN signal_code='B' THEN score END) as B_score,
        MAX(CASE WHEN signal_code='Rs' THEN score END) as Rs_score,
        MAX(CASE WHEN signal_code='F' THEN available::int END) as F_avail,
        MAX(CASE WHEN signal_code='D' THEN available::int END) as D_avail,
        MAX(CASE WHEN signal_code='X' THEN available::int END) as X_avail,
        MAX(CASE WHEN signal_code='V' THEN available::int END) as V_avail,
        MAX(CASE WHEN signal_code='Q' THEN available::int END) as Q_avail,
        MAX(CASE WHEN signal_code='B' THEN available::int END) as B_avail,
        MAX(CASE WHEN signal_code='Rs' THEN available::int END) as Rs_avail
    FROM risk_signals GROUP BY work_id
"""))
print("  Pivot table created")

# Create recalculated table
db.execute(text("DROP TABLE IF EXISTS recalculated"))
db.execute(text("""
    CREATE TEMP TABLE recalculated AS
    SELECT work_id,
        CASE WHEN (F_avail+D_avail+X_avail+V_avail+Q_avail+B_avail+Rs_avail)=0 THEN 0.0
        ELSE ROUND(
            (COALESCE(F_score,0)*CASE WHEN F_avail=1 THEN 0.15 ELSE 0 END +
             COALESCE(D_score,0)*CASE WHEN D_avail=1 THEN 0.12 ELSE 0 END +
             COALESCE(X_score,0)*CASE WHEN X_avail=1 THEN 0.12 ELSE 0 END +
             COALESCE(V_score,0)*CASE WHEN V_avail=1 THEN 0.10 ELSE 0 END +
             COALESCE(Q_score,0)*CASE WHEN Q_avail=1 THEN 0.10 ELSE 0 END +
             COALESCE(B_score,0)*CASE WHEN B_avail=1 THEN 0.04 ELSE 0 END +
             COALESCE(Rs_score,0)*CASE WHEN Rs_avail=1 THEN 0.04 ELSE 0 END) /
            (CASE WHEN F_avail=1 THEN 0.15 ELSE 0 END +
             CASE WHEN D_avail=1 THEN 0.12 ELSE 0 END +
             CASE WHEN X_avail=1 THEN 0.12 ELSE 0 END +
             CASE WHEN V_avail=1 THEN 0.10 ELSE 0 END +
             CASE WHEN Q_avail=1 THEN 0.10 ELSE 0 END +
             CASE WHEN B_avail=1 THEN 0.04 ELSE 0 END +
             CASE WHEN Rs_avail=1 THEN 0.04 ELSE 0 END)
        , 1)
        END as new_composite,
        CASE WHEN (F_avail+D_avail+X_avail+V_avail+Q_avail+B_avail+Rs_avail)=0 THEN 0.0
        ELSE ROUND(
            (CASE WHEN F_avail=1 THEN 0.15 ELSE 0 END +
             CASE WHEN D_avail=1 THEN 0.12 ELSE 0 END +
             CASE WHEN X_avail=1 THEN 0.12 ELSE 0 END +
             CASE WHEN V_avail=1 THEN 0.10 ELSE 0 END +
             CASE WHEN Q_avail=1 THEN 0.10 ELSE 0 END +
             CASE WHEN B_avail=1 THEN 0.04 ELSE 0 END +
             CASE WHEN Rs_avail=1 THEN 0.04 ELSE 0 END) / 1.0
        , 4)
        END as new_coverage,
        CASE WHEN (F_avail+D_avail+X_avail+V_avail+Q_avail+B_avail+Rs_avail)=0 THEN 'LOW'
        WHEN ROUND(
            (COALESCE(F_score,0)*CASE WHEN F_avail=1 THEN 0.15 ELSE 0 END +
             COALESCE(D_score,0)*CASE WHEN D_avail=1 THEN 0.12 ELSE 0 END +
             COALESCE(X_score,0)*CASE WHEN X_avail=1 THEN 0.12 ELSE 0 END +
             COALESCE(V_score,0)*CASE WHEN V_avail=1 THEN 0.10 ELSE 0 END +
             COALESCE(Q_score,0)*CASE WHEN Q_avail=1 THEN 0.10 ELSE 0 END +
             COALESCE(B_score,0)*CASE WHEN B_avail=1 THEN 0.04 ELSE 0 END +
             COALESCE(Rs_score,0)*CASE WHEN Rs_avail=1 THEN 0.04 ELSE 0 END) /
            (CASE WHEN F_avail=1 THEN 0.15 ELSE 0 END +
             CASE WHEN D_avail=1 THEN 0.12 ELSE 0 END +
             CASE WHEN X_avail=1 THEN 0.12 ELSE 0 END +
             CASE WHEN V_avail=1 THEN 0.10 ELSE 0 END +
             CASE WHEN Q_avail=1 THEN 0.10 ELSE 0 END +
             CASE WHEN B_avail=1 THEN 0.04 ELSE 0 END +
             CASE WHEN Rs_avail=1 THEN 0.04 ELSE 0 END)
        , 1) >= 65.0 THEN 'HIGH'
        WHEN ROUND(
            (COALESCE(F_score,0)*CASE WHEN F_avail=1 THEN 0.15 ELSE 0 END +
             COALESCE(D_score,0)*CASE WHEN D_avail=1 THEN 0.12 ELSE 0 END +
             COALESCE(X_score,0)*CASE WHEN X_avail=1 THEN 0.12 ELSE 0 END +
             COALESCE(V_score,0)*CASE WHEN V_avail=1 THEN 0.10 ELSE 0 END +
             COALESCE(Q_score,0)*CASE WHEN Q_avail=1 THEN 0.10 ELSE 0 END +
             COALESCE(B_score,0)*CASE WHEN B_avail=1 THEN 0.04 ELSE 0 END +
             COALESCE(Rs_score,0)*CASE WHEN Rs_avail=1 THEN 0.04 ELSE 0 END) /
            (CASE WHEN F_avail=1 THEN 0.15 ELSE 0 END +
             CASE WHEN D_avail=1 THEN 0.12 ELSE 0 END +
             CASE WHEN X_avail=1 THEN 0.12 ELSE 0 END +
             CASE WHEN V_avail=1 THEN 0.10 ELSE 0 END +
             CASE WHEN Q_avail=1 THEN 0.10 ELSE 0 END +
             CASE WHEN B_avail=1 THEN 0.04 ELSE 0 END +
             CASE WHEN Rs_avail=1 THEN 0.04 ELSE 0 END)
        , 1) >= 40.0 THEN 'MEDIUM'
        ELSE 'LOW' END as new_priority
    FROM signal_pivot
"""))
print("  Recalculated table created")

# 3. Update only changed records
print("\n=== 3. UPDATING ===")
updated = db.execute(text("""
    UPDATE risk_scores rs SET
        composite_risk = rc.new_composite,
        confidence_coverage = rc.new_coverage,
        inspection_priority = rc.new_priority,
        updated_at = NOW()
    FROM recalculated rc
    WHERE rs.work_id = rc.work_id
      AND (ABS(rs.composite_risk - rc.new_composite) > 0.05
           OR ABS(rs.confidence_coverage - rc.new_coverage) > 0.001
           OR rs.inspection_priority != rc.new_priority)
""")).rowcount
print(f"  Updated {updated} records")
db.commit()

# 4. AFTER distribution
print("\n=== 4. AFTER: NEW DISTRIBUTION ===")
after_dist = db.execute(text("""
    SELECT composite_risk, COUNT(*) as cnt
    FROM risk_scores GROUP BY composite_risk ORDER BY cnt DESC LIMIT 20
""")).fetchall()
for r in after_dist:
    print(f"  {float(r[0]):6.1f}: {r[1]:6d}")

# 5. Verify stale 47.5 scores
print("\n=== 5. STALE 47.5 VERIFICATION ===")
now_60 = db.execute(text("""
    SELECT COUNT(*) FROM risk_scores WHERE ABS(composite_risk - 60.0) < 0.05
""")).scalar()
print(f"  Works now at 60.0: {now_60}")

# Check specific works that were 47.5
sample = db.execute(text("""
    SELECT rs.work_id, rs.composite_risk, rs.confidence_coverage, rs.inspection_priority
    FROM risk_scores rs
    JOIN risk_signals rs_f ON rs.work_id = rs_f.work_id AND rs_f.signal_code='F' AND rs_f.available=false
    JOIN risk_signals rs_d ON rs.work_id = rs_d.work_id AND rs_d.signal_code='D' AND rs_d.available=true AND rs_d.score=20
    JOIN risk_signals rs_q ON rs.work_id = rs_q.work_id AND rs_q.signal_code='Q' AND rs_q.available=true AND rs_q.score=100
    JOIN risk_signals rs_rs ON rs.work_id = rs_rs.work_id AND rs_rs.signal_code='Rs' AND rs_rs.available=true AND rs_rs.score=20
    JOIN risk_signals rs_x ON rs.work_id = rs_x.work_id AND rs_x.signal_code='X' AND rs_x.available=true AND rs_x.score=95
    JOIN risk_signals rs_b ON rs.work_id = rs_b.work_id AND rs_b.signal_code='B' AND rs_b.available=true AND rs_b.score=15
    LIMIT 5
""")).fetchall()
print("  Sample recalculated works:")
for r in sample:
    print(f"    {r[0][:45]:45s} risk={float(r[1]):.1f}  coverage={float(r[2]):.4f}  priority={r[3]}")

# 6. Verify signal records unchanged
print("\n=== 6. SIGNAL RECORDS VERIFICATION ===")
total_sig = db.execute(text("SELECT COUNT(*) FROM risk_signals")).scalar()
print(f"  Total risk_signals: {total_sig}")

# 7. Before/after comparison
print("\n=== 7. BEFORE/AFTER COMPARISON ===")
print("  Risk  | Before | After")
print("  ------|--------|------")
all_risks = sorted(set([float(r[0]) for r in before_dist] + [float(r[0]) for r in after_dist]))
for risk_val in all_risks:
    before_cnt = next((r[1] for r in before_dist if abs(float(r[0]) - risk_val) < 0.05), 0)
    after_cnt = db.execute(text("SELECT COUNT(*) FROM risk_scores WHERE ABS(composite_risk - :risk) < 0.05"), {'risk': risk_val}).scalar()
    if before_cnt > 0 or after_cnt > 0:
        print(f"  {risk_val:5.1f} | {before_cnt:6d} | {after_cnt:5d}")

db.close()
print("\n" + "=" * 80)
print("RECONCILIATION COMPLETE")
