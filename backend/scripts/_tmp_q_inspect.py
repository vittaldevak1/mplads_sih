import psycopg2
conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/mplads')
cur = conn.cursor()

cur.execute("""SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name='works' ORDER BY ordinal_position""")
print('=== WORKS TABLE SCHEMA ===')
for r in cur.fetchall():
    print(f'  {r[0]:30s} {r[1]:25s} nullable={r[2]}')

cur.execute('SELECT COUNT(*) FROM works')
print(f'\nTotal works: {cur.fetchone()[0]}')

cur.execute('SELECT is_sc_quota, COUNT(*) FROM works GROUP BY is_sc_quota')
print('\nis_sc_quota distribution:')
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]}')

cur.execute('SELECT is_st_quota, COUNT(*) FROM works GROUP BY is_st_quota')
print('\nis_st_quota distribution:')
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]}')

cur.execute('SELECT work_category, COUNT(*) FROM works GROUP BY work_category ORDER BY COUNT(*) DESC LIMIT 20')
print('\nwork_category distribution:')
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]}')

conn.close()
