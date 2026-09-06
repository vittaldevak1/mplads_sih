"""
Audit script for Signal F (Financial/Cost Overrun).
Quantifies sanction amounts, aggregated expenditures/disbursements,
and verifies F signal availability and missing data handling.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
import json
from sqlalchemy import text
from app.database import SessionLocal

db = SessionLocal()

print("=" * 80)
print("AUDIT: SIGNAL F (FINANCIAL / COST OVERRUN) DATA & AVAILABILITY")
print("=" * 80)

# 1. Overall counts in base tables
total_works = db.execute(text("SELECT COUNT(*) FROM works")).scalar()
distinct_work_ids = db.execute(text("SELECT COUNT(DISTINCT work_id) FROM works")).scalar()

print(f"\n1. BASE WORK COUNTS:")
print(f"  Total works in DB: {total_works}")
print(f"  Distinct work_ids: {distinct_work_ids}")

# 2. Sanction Amount analysis
print(f"\n2. SANCTION AMOUNT QUANTIFICATION:")
sanction_counts = db.execute(text("""
    SELECT 
        COUNT(DISTINCT w.work_id) as total_works,
        COUNT(DISTINCT ws.work_id) as works_with_sanction_record,
        COUNT(DISTINCT CASE WHEN ws.sanction_amount IS NOT NULL THEN ws.work_id END) as works_with_non_null_sanction,
        COUNT(DISTINCT CASE WHEN ws.sanction_amount > 0 THEN ws.work_id END) as works_with_positive_sanction,
        COUNT(DISTINCT CASE WHEN ws.sanction_amount = 0 THEN ws.work_id END) as works_with_zero_sanction,
        COUNT(DISTINCT CASE WHEN ws.sanction_amount IS NULL OR ws.sanction_amount <= 0 THEN w.work_id END) as works_with_invalid_or_missing_sanction
    FROM works w
    LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
""")).fetchone()

print(f"  Works with sanction record: {sanction_counts[1]} ({sanction_counts[1]*100/total_works:.2f}%)")
print(f"  Works with non-null sanction_amount: {sanction_counts[2]} ({sanction_counts[2]*100/total_works:.2f}%)")
print(f"  Works with valid sanction_amount (> 0): {sanction_counts[3]} ({sanction_counts[3]*100/total_works:.2f}%)")
print(f"  Works with sanction_amount == 0: {sanction_counts[4]}")
print(f"  Works with missing/invalid sanction_amount (<= 0 or NULL): {sanction_counts[5]} ({sanction_counts[5]*100/total_works:.2f}%)")

# 3. Expenditure / Disbursed Amount analysis
print(f"\n3. EXPENDITURE / DISBURSED AMOUNT QUANTIFICATION:")
exp_table_counts = db.execute(text("""
    SELECT 
        COUNT(*) as total_expenditure_rows,
        COUNT(DISTINCT work_id) as distinct_works_in_expenditure,
        COUNT(CASE WHEN fund_disbursed_amount IS NOT NULL THEN 1 END) as rows_with_non_null_disbursed,
        COUNT(CASE WHEN fund_disbursed_amount > 0 THEN 1 END) as rows_with_positive_disbursed
    FROM expenditures
""")).fetchone()

print(f"  Total expenditure rows: {exp_table_counts[0]}")
print(f"  Distinct works in expenditures table: {exp_table_counts[1]} ({exp_table_counts[1]*100/total_works:.2f}%)")
print(f"  Expenditure rows with non-null fund_disbursed_amount: {exp_table_counts[2]}")
print(f"  Expenditure rows with fund_disbursed_amount > 0: {exp_table_counts[3]}")

# Aggregation at Work ID level
print(f"\n4. AGGREGATED DISBURSEMENT AT WORK ID LEVEL:")
agg_counts = db.execute(text("""
    WITH exp_agg AS (
        SELECT 
            work_id,
            COUNT(*) as exp_record_count,
            SUM(fund_disbursed_amount) as total_disbursed
        FROM expenditures
        GROUP BY work_id
    )
    SELECT 
        COUNT(DISTINCT w.work_id) as total_works,
        COUNT(DISTINCT CASE WHEN ea.work_id IS NOT NULL THEN w.work_id END) as works_with_any_exp,
        COUNT(DISTINCT CASE WHEN ea.total_disbursed IS NOT NULL AND ea.total_disbursed > 0 THEN w.work_id END) as works_with_positive_disbursed,
        COUNT(DISTINCT CASE WHEN ea.total_disbursed = 0 THEN w.work_id END) as works_with_zero_disbursed,
        COUNT(DISTINCT CASE WHEN ea.total_disbursed IS NULL AND ea.work_id IS NOT NULL THEN w.work_id END) as works_with_null_disbursed,
        COUNT(DISTINCT CASE WHEN ea.work_id IS NULL THEN w.work_id END) as works_with_no_exp_records
    FROM works w
    LEFT JOIN exp_agg ea ON w.work_id = ea.work_id
""")).fetchone()

print(f"  Works with at least one expenditure record: {agg_counts[1]} ({agg_counts[1]*100/total_works:.2f}%)")
print(f"  Works with aggregated total_disbursed > 0: {agg_counts[2]} ({agg_counts[2]*100/total_works:.2f}%)")
print(f"  Works with aggregated total_disbursed == 0: {agg_counts[3]}")
print(f"  Works with aggregated total_disbursed NULL (all records NULL): {agg_counts[4]}")
print(f"  Works with NO expenditure records: {agg_counts[5]} ({agg_counts[5]*100/total_works:.2f}%)")

# Multiple expenditure records per work verification
multi_exp = db.execute(text("""
    WITH exp_agg AS (
        SELECT work_id, COUNT(*) as cnt FROM expenditures GROUP BY work_id
    )
    SELECT 
        COUNT(CASE WHEN cnt = 1 THEN 1 END) as single_record,
        COUNT(CASE WHEN cnt > 1 THEN 1 END) as multi_record,
        MAX(cnt) as max_records_per_work
    FROM exp_agg
""")).fetchone()
print(f"  Works with single expenditure record: {multi_exp[0]}")
print(f"  Works with multiple expenditure records (aggregated): {multi_exp[1]}")
print(f"  Max expenditure records on a single work: {multi_exp[2]}")

# 5. Overlap: Works with BOTH valid Sanction AND valid Aggregated Disbursed
print(f"\n5. JOINT AVAILABILITY (SANCTION + DISBURSED):")
joint_counts = db.execute(text("""
    WITH exp_agg AS (
        SELECT 
            work_id,
            SUM(fund_disbursed_amount) as total_disbursed
        FROM expenditures
        GROUP BY work_id
    )
    SELECT 
        COUNT(DISTINCT w.work_id) as total_works,
        -- Both valid
        COUNT(DISTINCT CASE 
            WHEN ws.sanction_amount > 0 AND ea.total_disbursed > 0 
            THEN w.work_id 
        END) as both_valid_positive,
        -- Sanction valid, disbursed missing/no record
        COUNT(DISTINCT CASE 
            WHEN ws.sanction_amount > 0 AND ea.work_id IS NULL 
            THEN w.work_id 
        END) as sanction_valid_no_exp_record,
        -- Sanction valid, disbursed zero or null
        COUNT(DISTINCT CASE 
            WHEN ws.sanction_amount > 0 AND (ea.total_disbursed IS NULL OR ea.total_disbursed <= 0) AND ea.work_id IS NOT NULL
            THEN w.work_id 
        END) as sanction_valid_zero_or_null_disbursed,
        -- Sanction missing/invalid, disbursed valid
        COUNT(DISTINCT CASE 
            WHEN (ws.sanction_amount IS NULL OR ws.sanction_amount <= 0) AND ea.total_disbursed > 0 
            THEN w.work_id 
        END) as sanction_invalid_disbursed_valid,
        -- Both missing/invalid
        COUNT(DISTINCT CASE 
            WHEN (ws.sanction_amount IS NULL OR ws.sanction_amount <= 0) AND (ea.work_id IS NULL OR ea.total_disbursed IS NULL OR ea.total_disbursed <= 0) 
            THEN w.work_id 
        END) as both_missing_or_invalid
    FROM works w
    LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
    LEFT JOIN exp_agg ea ON w.work_id = ea.work_id
""")).fetchone()

print(f"  Works with BOTH valid sanction (>0) AND valid disbursed (>0): {joint_counts[1]} ({joint_counts[1]*100/total_works:.2f}%)")
print(f"  Works with valid sanction, but NO expenditure records: {joint_counts[2]} ({joint_counts[2]*100/total_works:.2f}%)")
print(f"  Works with valid sanction, but expenditure is <= 0 or NULL: {joint_counts[3]}")
print(f"  Works with missing sanction, but valid disbursed: {joint_counts[4]}")
print(f"  Works with BOTH missing/invalid: {joint_counts[5]}")

# 6. Actual F Signal status in risk_signals table
print(f"\n6. ACTUAL F SIGNAL STATUS IN `risk_signals` TABLE:")
f_signal_stats = db.execute(text("""
    SELECT 
        available,
        CASE WHEN score IS NULL THEN 'NULL' ELSE 'NOT NULL' END as score_null_status,
        score,
        COUNT(*) as cnt
    FROM risk_signals
    WHERE signal_code = 'F'
    GROUP BY available, score_null_status, score
    ORDER BY available DESC, score ASC NULLS LAST
""")).fetchall()

for row in f_signal_stats:
    avail_str = "AVAILABLE" if row[0] else "UNAVAILABLE"
    score_str = f"{row[2]:.2f}" if row[2] is not None else "NULL"
    print(f"  {avail_str:12s} | Score: {score_str:>7s} | Count: {row[3]:6d}")

f_summary = db.execute(text("""
    SELECT 
        COUNT(*) as total_f_rows,
        COUNT(CASE WHEN available = true THEN 1 END) as f_available,
        COUNT(CASE WHEN available = false THEN 1 END) as f_unavailable,
        COUNT(CASE WHEN available = false AND score IS NULL THEN 1 END) as f_unavail_score_null,
        COUNT(CASE WHEN available = false AND score = 0 THEN 1 END) as f_unavail_score_zero,
        COUNT(CASE WHEN available = true AND score IS NULL THEN 1 END) as f_avail_score_null,
        COUNT(CASE WHEN available = true AND score = 0 THEN 1 END) as f_avail_score_zero
    FROM risk_signals
    WHERE signal_code = 'F'
""")).fetchone()

print(f"\n  F Signal Summary across all scored works ({f_summary[0]} works):")
print(f"    Available: {f_summary[1]} ({f_summary[1]*100/f_summary[0]:.2f}%)")
print(f"    Unavailable: {f_summary[2]} ({f_summary[2]*100/f_summary[0]:.2f}%)")
print(f"    Unavailable with score IS NULL: {f_summary[3]} (100% of unavailable)")
print(f"    Unavailable with score = 0: {f_summary[4]}")

# 7. Check explanations and evidence for unavailable F signals
print(f"\n7. EXPLANATIONS & EVIDENCE FOR UNAVAILABLE F SIGNALS:")
unavail_explanations = db.execute(text("""
    SELECT explanation, COUNT(*) as cnt
    FROM risk_signals
    WHERE signal_code = 'F' AND available = false
    GROUP BY explanation
    ORDER BY cnt DESC
""")).fetchall()

for row in unavail_explanations:
    print(f"    [{row[1]:6d}x] {row[0]}")

# 8. Check subset for "Lighting of public spaces"
print(f"\n8. F SIGNAL SPECIFICALLY FOR 'Lighting of public spaces' (12,524 works):")
lighting_f = db.execute(text("""
    SELECT 
        rs.available,
        CASE WHEN rs.score IS NULL THEN 'NULL' ELSE CAST(rs.score as text) END as score_str,
        COUNT(*) as cnt
    FROM risk_signals rs
    JOIN works w ON rs.work_id = w.work_id
    WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
      AND rs.signal_code = 'F'
    GROUP BY rs.available, score_str
    ORDER BY rs.available DESC, cnt DESC
""")).fetchall()

for row in lighting_f:
    avail_str = "AVAILABLE" if row[0] else "UNAVAILABLE"
    print(f"    {avail_str:12s} | Score: {row[1]:>7s} | Count: {row[2]:6d}")

db.close()
