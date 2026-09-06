import sys
sys.path.insert(0, '.')
from app.database import engine
from sqlalchemy import text
conn = engine.connect()
# Add missing unique constraint
conn.execute(text("ALTER TABLE risk_signals ADD CONSTRAINT uq_risk_signals_work_signal UNIQUE (work_id, signal_code)"))
conn.commit()
print("Added unique constraint")
r = conn.execute(text("SELECT conname, contype FROM pg_constraint WHERE conrelid = 'risk_signals'::regclass"))
for row in r:
    print(row)
conn.close()
