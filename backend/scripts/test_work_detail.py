import requests
import psycopg2
from urllib.parse import quote

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/mplads')
cur = conn.cursor()
cur.execute('SELECT work_id FROM works LIMIT 1')
wid = cur.fetchone()[0]
conn.close()

print(f"Testing work_id: {wid[:60]}...")
encoded = quote(wid, safe="")
print(f"Encoded: {encoded[:80]}...")

r = requests.get(f"http://127.0.0.1:8000/api/works/{encoded}", timeout=15)
print(f"Work detail: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    print(f"  work_id: {d.get('work_id', '')[:50]}")
else:
    print(f"  error: {r.text[:200]}")

r2 = requests.get(f"http://127.0.0.1:8000/api/risk/{encoded}", timeout=15)
print(f"Risk score: {r2.status_code}")
if r2.status_code == 200:
    d = r2.json()
    print(f"  composite_risk: {d.get('composite_risk')}")
    print(f"  signals: {len(d.get('signals', []))}")
else:
    print(f"  error: {r2.text[:200]}")
