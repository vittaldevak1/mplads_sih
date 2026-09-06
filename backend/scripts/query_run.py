import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
from sqlalchemy import text
from app.database import SessionLocal
db = SessionLocal()
r1 = db.execute(text("SELECT COUNT(*) FROM works WHERE LOWER(work_description) LIKE '%lighting of public spaces%'")).scalar()
r2 = db.execute(text("SELECT COUNT(DISTINCT work_id) FROM works WHERE LOWER(work_description) LIKE '%lighting of public spaces%'")).scalar()
print(f"COUNT(*):                {r1}")
print(f"COUNT(DISTINCT work_id): {r2}")
db.close()
