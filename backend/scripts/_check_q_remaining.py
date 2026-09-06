import psycopg2

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/mplads')
cur = conn.cursor()

cur.execute("""
    SELECT w.constituency IS NULL as no_constituency, COUNT(*)
    FROM risk_signals rs
    JOIN works w ON rs.work_id = w.work_id
    WHERE rs.signal_code = 'Q' AND rs.available = false
    GROUP BY 1
""")
print("Q signals still unavailable:")
for r in cur.fetchall():
    print(f"  constituency IS NULL={r[0]}: {r[1]}")

cur.execute("SELECT COUNT(*) FROM risk_signals WHERE signal_code='Q'")
print(f"\nTotal Q signals: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM risk_signals WHERE signal_code='Q' AND available=true")
print(f"Q available=true: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM risk_signals WHERE signal_code='Q' AND available=false")
print(f"Q available=false: {cur.fetchone()[0]}")

conn.close()
