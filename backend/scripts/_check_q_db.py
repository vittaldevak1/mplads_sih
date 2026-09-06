import psycopg2

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/mplads')
cur = conn.cursor()

cur.execute("SELECT signal_code, available, score FROM risk_signals WHERE signal_code='Q' LIMIT 5")
print("Q signals in DB (sample):")
for r in cur.fetchall():
    print(f"  code={r[0]} available={r[1]} score={r[2]}")

cur.execute("SELECT COUNT(*) FROM risk_signals WHERE signal_code='Q'")
print(f"\nTotal Q signals in DB: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM risk_signals WHERE signal_code='Q' AND available=true")
print(f"Q signals available=true: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM risk_signals WHERE signal_code='Q' AND available=false")
print(f"Q signals available=false: {cur.fetchone()[0]}")

conn.close()
