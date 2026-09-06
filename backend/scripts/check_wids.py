import psycopg2
conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/mplads')
cur = conn.cursor()
cur.execute('SELECT work_id FROM works LIMIT 5')
for r in cur.fetchall():
    print(repr(r[0]))
cur.execute("SELECT COUNT(*) FROM works WHERE work_id LIKE '%%/%%'")
print(f"Work IDs with /: {cur.fetchone()[0]}")
cur.execute("SELECT work_id FROM works WHERE work_id LIKE '%%/%%' LIMIT 3")
for r in cur.fetchall():
    print(repr(r[0]))
conn.close()
