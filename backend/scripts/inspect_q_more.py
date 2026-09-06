import psycopg2
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/mplads')
cur = conn.cursor()

# SC vs NON-SC SANCTION AMOUNTS
cur.execute("""
SELECT 
    is_sc_quota,
    AVG(sanction_amount) as avg_sanction,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sanction_amount) as median_sanction
FROM works w
LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
WHERE sanction_amount IS NOT NULL
GROUP BY is_sc_quota
""")
print('=== SC vs NON-SC SANCTION AMOUNTS ===')
for r in cur.fetchall():
    print(f'  SC={r[0]}: avg=INR {r[1]:,.0f}, median=INR {r[2]:,.0f}')

# mp_allocations table
cur.execute("""
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name='mp_allocations' ORDER BY ordinal_position
""")
print('\n=== MP_ALLOCATIONS SCHEMA ===')
for r in cur.fetchall():
    print(f'  {r[0]:30s} {r[1]}')

cur.execute('SELECT COUNT(*) FROM mp_allocations')
print(f'\nTotal mp_allocations rows: {cur.fetchone()[0]}')

# Check if mp_allocations has any SC/ST data
cur.execute("SELECT * FROM mp_allocations LIMIT 3")
cols = [d[0] for d in cur.description]
print(f'\nmp_allocations columns: {cols}')
for r in cur.fetchall():
    print(f'  {dict(zip(cols, r))}')

# Are there works with BOTH SC and ST?
cur.execute("SELECT COUNT(*) FROM works WHERE is_sc_quota = true AND is_st_quota = true")
print(f'\nWorks with BOTH SC and ST: {cur.fetchone()[0]}')

# Works with NEITHER SC nor ST
cur.execute("SELECT COUNT(*) FROM works WHERE is_sc_quota = false AND is_st_quota = false")
print(f'Works with NEITHER SC nor ST: {cur.fetchone()[0]}')

# Check null percentages for is_sc_quota and is_st_quota
cur.execute("SELECT COUNT(*) FROM works WHERE is_sc_quota IS NULL")
print(f'\nis_sc_quota NULL: {cur.fetchone()[0]}')
cur.execute("SELECT COUNT(*) FROM works WHERE is_st_quota IS NULL")
print(f'is_st_quota NULL: {cur.fetchone()[0]}')

# Works where SC/ST is true but no sanction amount
cur.execute("""
SELECT 
    w.is_sc_quota, w.is_st_quota,
    COUNT(*) as total,
    COUNT(ws.sanction_amount) as has_sanction,
    COUNT(*) - COUNT(ws.sanction_amount) as missing_sanction
FROM works w
LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
WHERE w.is_sc_quota = true OR w.is_st_quota = true
GROUP BY w.is_sc_quota, w.is_st_quota
""")
print('\n=== SC/ST WORKS MISSING SANCTION DATA ===')
for r in cur.fetchall():
    print(f'  SC={r[0]} ST={r[1]}: total={r[2]}, has_sanction={r[3]}, missing={r[4]}')

# District/constituency level SC allocation analysis
cur.execute("""
SELECT state, 
    COUNT(*) as total_works,
    COUNT(*) FILTER (WHERE is_sc_quota) as sc_works,
    ROUND(COUNT(*) FILTER (WHERE is_sc_quota) * 100.0 / COUNT(*), 1) as sc_pct
FROM works
WHERE state IS NOT NULL
GROUP BY state
HAVING COUNT(*) > 100
ORDER BY sc_pct DESC
LIMIT 15
""")
print('\n=== TOP 15 STATES BY SC WORK PERCENTAGE ===')
for r in cur.fetchall():
    print(f'  {r[0]:25s}: {r[3]:5.1f}% SC ({r[2]}/{r[1]})')

# What is the overall SC national average we should compare against?
cur.execute("""
SELECT 
    SUM(sanction_amount) FILTER (WHERE is_sc_quota) * 100.0 / SUM(sanction_amount) as sc_amount_pct,
    SUM(sanction_amount) FILTER (WHERE is_st_quota) * 100.0 / SUM(sanction_amount) as st_amount_pct
FROM works w
JOIN work_sanctions ws ON w.work_id = ws.work_id
WHERE ws.sanction_amount IS NOT NULL
""")
r = cur.fetchone()
print(f'\n=== NATIONAL SC/ST SANCTION AMOUNT SHARE ===')
print(f'  SC share of total sanctioned: {r[0]:.2f}%')
print(f'  ST share of total sanctioned: {r[1]:.2f}%')

conn.close()
