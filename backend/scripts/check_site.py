import requests
from urllib.parse import quote

wid = 'WS/ MP620/2024-2025/133166-Construction of buildings for community cultural activities'
enc = quote(wid, safe='')

for path in ['api/works/', 'api/risk/', 'api/inspection/']:
    r = requests.get(f'http://127.0.0.1:8000/{path}{enc}', timeout=15)
    print(f'{path:30s}: {r.status_code}')

# Check frontend pages
for page in ['', 'works', 'analytics', 'inspection', 'anomalies', 'vendors']:
    url = f'http://127.0.0.1:3000/{page}'
    r = requests.get(url, timeout=10)
    print(f'Frontend /{page:20s}: {r.status_code}')
