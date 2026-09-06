import sys; sys.path.insert(0, '.')
from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
r = db.execute(text("SELECT inspection_priority, count(*) FROM risk_scores GROUP BY inspection_priority ORDER BY count(*) DESC"))
print("Risk Distribution:")
for row in r:
    print(f"  {row[0]}: {row[1]}")
r = db.execute(text("SELECT count(*) FROM risk_signals WHERE explanation LIKE '%Signal active%'"))
print(f"Mock signals: {r.scalar()}")
r = db.execute(text("SELECT count(*) FROM risk_signals WHERE explanation NOT LIKE '%Signal active%'"))
print(f"Real signals: {r.scalar()}")
db.close()
