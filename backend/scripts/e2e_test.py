"""End-to-end verification of all backend APIs."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

base = 'http://localhost:8000/api'
passed = 0
failed = 0

def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name} {detail}")
    else:
        failed += 1
        print(f"  FAIL  {name} {detail}")

print("=" * 60)
print("E2E BACKEND API TESTS")
print("=" * 60)

# 1. Health
r = requests.get('http://localhost:8000/health', timeout=5)
test("Health", r.status_code == 200, f"status={r.json()['status']}")

# 2. Dashboard summary
r = requests.get(f'{base}/dashboard/summary', timeout=5)
s = r.json()
test("Dashboard summary", r.status_code == 200, f"works={s['total_works']} high={s['high_risk']} med={s['medium_risk']} low={s['low_risk']}")

# 3. Works
r = requests.get(f'{base}/works?page=1&size=2', timeout=5)
w = r.json()
test("Works list", r.status_code == 200 and w['total'] > 0, f"total={w['total']}")

# 4. Work detail
wid = w['items'][0]['work_id']
r = requests.get(f'{base}/works/{requests.utils.quote(wid, safe="")}', timeout=5)
wd = r.json()
test("Work detail", r.status_code == 200 and wd.get('work_id'), f"id={wd.get('work_id','FAIL')[:40]}")

# 5. Risk
r = requests.get(f'{base}/risk/{requests.utils.quote(wid, safe="")}', timeout=5)
risk = r.json()
test("Risk score", r.status_code == 200 and len(risk.get('signals', [])) == 11,
     f"composite={risk.get('composite_risk')} signals={len(risk.get('signals',[]))} priority={risk.get('inspection_priority')}")

# 6. Verify 11 signals
signals = risk.get('signals', [])
available = [s for s in signals if s['available']]
unavailable = [s for s in signals if not s['available']]
codes_available = set(s['signal_code'] for s in available)
codes_unavailable = set(s['signal_code'] for s in unavailable)
test("11 signals total", len(signals) == 11)
test("C/O/S/G unavailable", codes_unavailable >= {'C', 'O', 'S', 'G'}, f"unavailable={codes_unavailable}")
test("No zero scores for unavailable", all(s['score'] is None for s in unavailable))

# 7. Anomalies HIGH_RISK
r = requests.get(f'{base}/anomalies?anomaly_type=HIGH_RISK&size=2', timeout=5)
a = r.json()
test("Anomalies HIGH_RISK", r.status_code == 200 and a['total'] > 0, f"total={a['total']}")

# 8. Anomalies F signal
r = requests.get(f'{base}/anomalies?anomaly_type=F&size=2', timeout=10)
a = r.json()
test("Anomalies F signal", r.status_code == 200 and a['total'] > 0, f"total={a['total']}")

# 9. Anomalies Q signal
r = requests.get(f'{base}/anomalies?anomaly_type=Q&size=2', timeout=10)
a = r.json()
test("Anomalies Q signal", r.status_code == 200 and a['total'] > 0, f"total={a['total']}")

# 10. Unavailable signal C
r = requests.get(f'{base}/anomalies?anomaly_type=C&size=1', timeout=5)
u = r.json()
test("Unavailable signal C", u.get('signal_unavailable') == True)

# 11. Inspection queue
r = requests.get(f'{base}/inspection/queue?limit=3', timeout=5)
q = r.json()
test("Inspection queue", r.status_code == 200 and q['total'] > 0, f"total={q['total']} counts={q['counts']}")

# 12. Vendors
r = requests.get(f'{base}/vendors?page=1&size=2', timeout=5)
v = r.json()
test("Vendors", r.status_code == 200 and v['total'] > 0, f"total={v['total']}")

# 13. Benford
r = requests.get(f'{base}/dashboard/benford', timeout=5)
b = r.json()
test("Benford", r.status_code == 200 and b['sample_size'] > 0, f"sample={b['sample_size']}")

# 14. State risk
r = requests.get(f'{base}/dashboard/state-risk', timeout=5)
sr = r.json()
test("State risk", r.status_code == 200 and len(sr['states']) > 0, f"states={len(sr['states'])}")

# 15. Q compliance
r = requests.get(f'{base}/dashboard/q-compliance', timeout=5)
qc = r.json()
test("Q compliance", r.status_code == 200, f"constituencies={qc['total_constituencies_analyzed']}")

# 16. Sankey
r = requests.get(f'{base}/dashboard/sankey', timeout=5)
sk = r.json()
test("Sankey", r.status_code == 200, f"works_flow={sk.get('works_flow',{}).get('recommended',0)}")

# 17. Inspection assign + history
r = requests.post(f'{base}/inspection/{requests.utils.quote(wid, safe="")}/assign', timeout=5)
test("Inspection assign", r.status_code == 200)

r = requests.get(f'{base}/inspection/{requests.utils.quote(wid, safe="")}/history', timeout=5)
h = r.json()
test("Inspection history", r.status_code == 200 and len(h.get('history', [])) > 0, f"entries={len(h.get('history',[]))}")

print()
print("=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed")
print("=" * 60)
