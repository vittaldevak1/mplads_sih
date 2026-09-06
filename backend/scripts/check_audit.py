import requests, time

r = requests.get("http://127.0.0.1:8000/api/v1/audit/status", timeout=5)
d = r.json()
processed = d["works_processed"]
total = d["total"]
pct = processed * 100 // total if total > 0 else 0
print(f"Progress: {processed}/{total} ({pct}%)")

if processed > 0:
    rate = processed / 30.0
    remaining = (total - processed) / rate / 60
    print(f"Rate: {rate:.1f}/sec, ETA: {remaining:.1f} min")
