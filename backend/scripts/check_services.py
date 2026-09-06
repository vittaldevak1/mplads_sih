import requests
r = requests.get("http://localhost:3000", timeout=15)
print("Frontend:", "OK" if r.status_code == 200 else f"FAIL {r.status_code}")
r = requests.get("http://127.0.0.1:8000/health", timeout=15)
print("Backend:", "OK" if r.status_code == 200 else f"FAIL {r.status_code}")
r = requests.get("http://127.0.0.1:8000/api/v1/audit/status", timeout=15)
d = r.json()
print(f"Audit: {d['works_processed']}/{d['total']} running={d['running']}")
