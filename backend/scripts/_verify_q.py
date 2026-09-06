import requests, psycopg2
from urllib.parse import quote

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/mplads')
cur = conn.cursor()
cur.execute('SELECT work_id FROM works LIMIT 1')
wid = cur.fetchone()[0]
conn.close()

r = requests.get(f'http://127.0.0.1:8000/api/risk/{quote(wid, safe="")}', timeout=15)
d = r.json()
q = [s for s in d['signals'] if s['signal_code'] == 'Q'][0]
print(f"Status: {r.status_code}")
print(f"Q available: {q['available']}")
print(f"Q score: {q['score']}")
print(f"Q explanation: {q['explanation'][:120]}")
