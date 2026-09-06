import sys; sys.stdout.reconfigure(encoding='utf-8'); sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
from sqlalchemy import text
from app.database import SessionLocal
db = SessionLocal()
rows = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='expenditures' ORDER BY ordinal_position")).fetchall()
for r in rows: print(f"  {r[0]:35s} {r[1]}")
db.close()
