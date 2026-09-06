import psycopg2

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/mplads')
cur = conn.cursor()

print('=== Q SIGNAL DATA INVESTIGATION ===\n')

# 1. SC/ST works with sanction amounts
cur.execute("""
SELECT 
    w.is_sc_quota, w.is_st_quota,
    COUNT(*) as work_count,
    SUM(ws.sanction_amount) as total_sanctioned,
    SUM(COALESCE(d.total_disbursed, 0)) as total_disbursed
FROM works w
LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
LEFT JOIN (
    SELECT work_id, SUM(fund_disbursed_amount) as total_disbursed
    FROM expenditures GROUP BY work_id
) d ON w.work_id = d.work_id
GROUP BY w.is_sc_quota, w.is_st_quota
""")
print('=== SC/ST FINANCIAL SUMMARY ===')
print(f'  {"is_sc":>6s} {"is_st":>6s} {"count":>8s} {"sanctioned":>15s} {"disbursed":>15s}')
for r in cur.fetchall():
    sc, st, cnt, san, disb = r
    print(f'  {str(sc):>6s} {str(st):>6s} {cnt:8d} {san or 0:15,.0f} {disb:15,.0f}')

# 2. Total sanctioned amount
cur.execute('SELECT SUM(sanction_amount) FROM work_sanctions')
total_sanc = cur.fetchone()[0] or 0
print(f'\nTotal sanctioned across all works: {total_sanc:,.0f}')

# 3. SC works percentage by count and by amount
cur.execute("""
SELECT 
    COUNT(*) FILTER (WHERE is_sc_quota = true) as sc_count,
    COUNT(*) FILTER (WHERE is_st_quota = true) as st_count,
    COUNT(*) as total_count,
    SUM(sanction_amount) FILTER (WHERE is_sc_quota = true) as sc_amount,
    SUM(sanction_amount) FILTER (WHERE is_st_quota = true) as st_amount,
    SUM(sanction_amount) as total_amount
FROM works w
LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
""")
r = cur.fetchone()
sc_count, st_count, total_count, sc_amount, st_amount, total_amount = r
print(f'\n=== PERCENTAGES ===')
print(f'SC works: {sc_count}/{total_count} = {sc_count*100/total_count:.1f}%')
print(f'ST works: {st_count}/{total_count} = {st_count*100/total_count:.1f}%')
print(f'SC amount: {(sc_amount or 0):,.0f}/{(total_amount or 0):,.0f} = {(sc_amount or 0)*100/(total_amount or 1):.1f}%')
print(f'ST amount: {(st_amount or 0):,.0f}/{(total_amount or 0):,.0f} = {(st_amount or 0)*100/(total_amount or 1):.1f}%')

# 4. Check work_recommendations for MP info
cur.execute("""
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name='work_recommendations' ORDER BY ordinal_position
""")
print('\n=== WORK_RECOMMENDATIONS SCHEMA ===')
for r in cur.fetchall():
    print(f'  {r[0]:30s} {r[1]}')

# 5. Check if there are any other SC/ST/quota fields anywhere
cur.execute("""
SELECT table_name, column_name 
FROM information_schema.columns 
WHERE (column_name ILIKE '%%sc%%' OR column_name ILIKE '%%st%%' 
       OR column_name ILIKE '%%quota%%' OR column_name ILIKE '%%caste%%' 
       OR column_name ILIKE '%%tribe%%' OR column_name ILIKE '%%beneficiary%%')
AND table_name NOT LIKE '%%pg%%'
ORDER BY table_name, column_name
""")
print('\n=== ALL SC/ST/QUOTA COLUMNS ACROSS ALL TABLES ===')
for r in cur.fetchall():
    print(f'  {r[0]}.{r[1]}')

# 6. Check mp_allocations table
cur.execute("""
SELECT table_name FROM information_schema.tables 
WHERE table_name LIKE '%%alloc%%' OR table_name LIKE '%%mp%%'
""")
print('\n=== MP/ALLOCATION TABLES ===')
for r in cur.fetchall():
    print(f'  {r[0]}')

# 7. work_sanctions schema
cur.execute("""
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name='work_sanctions' ORDER BY ordinal_position
""")
print('\n=== WORK_SANCTIONS SCHEMA ===')
for r in cur.fetchall():
    print(f'  {r[0]:30s} {r[1]}')

# 8. expenditures schema
cur.execute("""
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name='expenditures' ORDER BY ordinal_position
""")
print('\n=== EXPENDITURES SCHEMA ===')
for r in cur.fetchall():
    print(f'  {r[0]:30s} {r[1]}')

# 9. Top states by SC work count
cur.execute("""
SELECT state, COUNT(*) as sc_count
FROM works
WHERE is_sc_quota = true
GROUP BY state
ORDER BY sc_count DESC
LIMIT 10
""")
print('\n=== TOP 10 STATES BY SC WORK COUNT ===')
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]}')

# 10. Top states by ST work count
cur.execute("""
SELECT state, COUNT(*) as st_count
FROM works
WHERE is_st_quota = true
GROUP BY state
ORDER BY st_count DESC
LIMIT 10
""")
print('\n=== TOP 10 STATES BY ST WORK COUNT ===')
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]}')

# 11. Average sanction amount for SC vs non-SC
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
print('\n=== SC vs NON-SC SANCTION AMOUNTS ===')
for r in cur.fetchall():
    print(f'  SC={r[0]}: avg=₹{r[1]:,.0f}, median=₹{r[2]:,.0f}')

conn.close()
