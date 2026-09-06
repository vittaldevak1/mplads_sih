import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
from sqlalchemy import text
from app.database import SessionLocal
db = SessionLocal()
# Find sanction_amount column
r = db.execute(text("""
    SELECT table_name, column_name FROM information_schema.columns
    WHERE column_name LIKE '%sanction%'
""")).fetchall()
for row in r:
    print(f"  {row[0]:25s} {row[1]}")
db.close()
