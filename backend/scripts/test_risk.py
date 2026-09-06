import requests
import psycopg2
from urllib.parse import quote

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/mplads')
cur = conn.cursor()
cur.execute('SELECT work_id FROM works LIMIT 1')
wid = cur.fetchone()[0]
conn.close()

encoded = quote(wid, safe="")

r = requests.get(f"http://127.0.0.1:8000/api/risk/{encoded}", timeout=15)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")
