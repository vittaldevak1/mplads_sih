import requests
import psycopg2
from urllib.parse import quote

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/mplads')
cur = conn.cursor()
cur.execute("SELECT work_id FROM works LIMIT 1")
wid = cur.fetchone()[0]
conn.close()

encoded = quote(wid, safe="")
url = f"http://127.0.0.1:8000/api/risk/{encoded}"
print(f"URL: {url[:100]}")
r = requests.get(url, timeout=15)
print(f"Status: {r.status_code}")
print(f"Headers: {dict(r.headers)}")
print(f"Body: {r.text[:1000]}")
