import psycopg2
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/mplads')
cur = conn.cursor()

# Constituency-level SC/ST allocation analysis
cur.execute("""
SELECT 
    constituency,
    state,
    COUNT(*) as total_works,
    COUNT(*) FILTER (WHERE is_sc_quota) as sc_works,
    COUNT(*) FILTER (WHERE is_st_quota) as st_works,
    ROUND(COUNT(*) FILTER (WHERE is_sc_quota) * 100.0 / COUNT(*), 1) as sc_pct,
    ROUND(COUNT(*) FILTER (WHERE is_st_quota) * 100.0 / COUNT(*), 1) as st_pct,
    SUM(sanction_amount) as total_sanctioned,
    SUM(sanction_amount) FILTER (WHERE is_sc_quota) as sc_sanctioned,
    SUM(sanction_amount) FILTER (WHERE is_st_quota) as st_sanctioned
FROM works w
LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
WHERE constituency IS NOT NULL
GROUP BY constituency, state
HAVING COUNT(*) >= 10
ORDER BY sc_pct ASC
LIMIT 20
""")
print('=== BOTTOM 20 CONSTITUENCIES BY SC% (potential violators) ===')
print(f'  {"Constituency":30s} {"State":20s} {"Total":>6s} {"SC":>5s} {"SC%":>6s} {"ST%":>6s}')
for r in cur.fetchall():
    print(f'  {r[0]:30s} {r[1]:20s} {r[2]:6d} {r[3]:5d} {r[5]:5.1f}% {r[6]:5.1f}%')

# How many constituencies violate SC threshold
cur.execute("""
WITH const_data AS (
    SELECT constituency, state,
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE is_sc_quota) as sc_count,
        COUNT(*) FILTER (WHERE is_st_quota) as st_count
    FROM works
    WHERE constituency IS NOT NULL
    GROUP BY constituency, state
    HAVING COUNT(*) >= 10
)
SELECT 
    COUNT(*) as total_constituencies,
    COUNT(*) FILTER (WHERE sc_count * 100.0 / total < 15) as sc_violators,
    COUNT(*) FILTER (WHERE st_count * 100.0 / total < 7.5) as st_violators,
    COUNT(*) FILTER (WHERE sc_count * 100.0 / total < 15 AND st_count * 100.0 / total < 7.5) as both_violators
FROM const_data
""")
r = cur.fetchone()
print(f'\n=== VIOLATION SUMMARY (constituencies with 10+ works) ===')
print(f'  Total constituencies analyzed: {r[0]}')
print(f'  SC violators (SC% < 15%): {r[1]} ({r[1]*100/r[0]:.1f}%)')
print(f'  ST violators (ST% < 7.5%): {r[2]} ({r[2]*100/r[0]:.1f}%)')
print(f'  Both violators: {r[3]} ({r[3]*100/r[0]:.1f}%)')

# How many WORKS are in violating constituencies
cur.execute("""
WITH const_data AS (
    SELECT constituency,
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE is_sc_quota) as sc_count,
        COUNT(*) FILTER (WHERE is_st_quota) as st_count
    FROM works
    WHERE constituency IS NOT NULL
    GROUP BY constituency
    HAVING COUNT(*) >= 10
),
constituencies AS (
    SELECT *,
        CASE WHEN sc_count * 100.0 / total < 15 THEN true ELSE false END as sc_violation,
        CASE WHEN st_count * 100.0 / total < 7.5 THEN true ELSE false END as st_violation
    FROM const_data
)
SELECT 
    c.sc_violation, c.st_violation,
    COUNT(*) as work_count
FROM works w
JOIN constituencies c ON w.constituency = c.constituency
GROUP BY c.sc_violation, c.st_violation
""")
print(f'\n=== WORKS IN VIOLATING vs COMPLIANT CONSTITUENCIES ===')
for r in cur.fetchall():
    label = f'SC_violation={r[0]}, ST_violation={r[1]}'
    print(f'  {label}: {r[2]} works')

# Per-constituency breakdown with amounts
cur.execute("""
WITH const_data AS (
    SELECT constituency, state,
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE is_sc_quota) as sc_count,
        COUNT(*) FILTER (WHERE is_st_quota) as st_count,
        SUM(sanction_amount) as total_amt,
        SUM(sanction_amount) FILTER (WHERE is_sc_quota) as sc_amt,
        SUM(sanction_amount) FILTER (WHERE is_st_quota) as st_amt
    FROM works w
    LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
    WHERE constituency IS NOT NULL
    GROUP BY constituency, state
    HAVING COUNT(*) >= 10
)
SELECT 
    CASE 
        WHEN sc_count * 100.0 / total < 15 AND st_count * 100.0 / total < 7.5 THEN 'both'
        WHEN sc_count * 100.0 / total < 15 THEN 'sc_only'
        WHEN st_count * 100.0 / total < 7.5 THEN 'st_only'
        ELSE 'compliant'
    END as violation_type,
    COUNT(*) as const_count,
    SUM(total) as total_works,
    SUM(sc_count) as total_sc_works,
    SUM(st_count) as total_st_works
FROM const_data
GROUP BY violation_type
""")
print(f'\n=== CONSTITUENCY GROUPS ===')
for r in cur.fetchall():
    print(f'  {r[0]:12s}: {r[1]} constituencies, {r[2]} works, SC={r[3]}, ST={r[4]}')

# Check how many works are in constituencies with < 10 works (too small for meaningful stat)
cur.execute("""
SELECT COUNT(*) FROM works
WHERE constituency IN (
    SELECT constituency FROM works GROUP BY constituency HAVING COUNT(*) < 10
)
""")
print(f'\nWorks in small constituencies (<10 works): {cur.fetchone()[0]}')
print(f'Works in large constituencies (>=10 works): 88111 - above = meaningful analysis')

conn.close()
