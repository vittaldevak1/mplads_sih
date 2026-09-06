import sys
sys.path.insert(0, '.')
from app.database import engine
from sqlalchemy import text

conn = engine.connect()

tables = ['works', 'work_sanctions', 'work_completions', 'work_recommendations', 'expenditures']
for t in tables:
    r = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{t}' ORDER BY ordinal_position"))
    print(f"=== {t} ===")
    for row in r:
        print(f"  {row[0]}")

# Sample joins
r = conn.execute(text("""
    SELECT w.work_id, w.work_description, w.constituency, w.state, w.parliament_house,
           w.is_sc_quota, w.is_st_quota, w.has_image_proof,
           ws.sanction_amount, ws.sanction_date, ws.work_status,
           wc.completion_date, wc.amount_disbursed,
           wr.recommended_date, wr.mp_name,
           e.vendor_name
    FROM works w
    LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
    LEFT JOIN work_completions wc ON w.work_id = wc.work_id
    LEFT JOIN work_recommendations wr ON w.work_id = wr.work_id
    LEFT JOIN expenditures e ON w.work_id = e.work_id
    LIMIT 3
"""))
print("\n=== sample joined ===")
for row in r:
    print(f"  {row}")

# Check date ranges
r = conn.execute(text("""
    SELECT
        count(*) as total,
        count(ws.sanction_amount) as has_amount,
        count(wc.completion_date) as has_completion,
        count(CASE WHEN ws.sanction_date IS NOT NULL AND wc.completion_date IS NOT NULL THEN 1 END) as has_both_dates
    FROM works w
    LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
    LEFT JOIN work_completions wc ON w.work_id = wc.work_id
"""))
print("\n=== data availability ===")
for row in r:
    print(f"  total={row[0]}, has_amount={row[1]}, has_completion={row[2]}, has_both_dates={row[3]}")

conn.close()
