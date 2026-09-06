import sys
sys.path.insert(0, '.')
from app.database import engine
from sqlalchemy import text
conn = engine.connect()
r = conn.execute(text("SELECT conname, contype FROM pg_constraint WHERE conrelid = 'risk_signals'::regclass"))
for row in r:
    print(row)
conn.close()
