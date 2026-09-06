"""Find newly available address field in the database."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
from sqlalchemy import text
from app.database import SessionLocal

def find_address_field():
    db = SessionLocal()

    print("=" * 70)
    print("SEARCHING FOR ADDRESS FIELD IN DATABASE")
    print("=" * 70)

    # 1. Check all columns in works table
    print("\n=== WORKS TABLE — ALL COLUMNS ===")
    rows = db.execute(text("""
        SELECT column_name, data_type, 
               CASE WHEN is_nullable = 'YES' THEN 'nullable' ELSE 'NOT NULL' END as nullable
        FROM information_schema.columns 
        WHERE table_name = 'works' 
        ORDER BY ordinal_position
    """)).fetchall()
    for r in rows:
        print(f"  {r[0]:30s} {r[1]:25s} {r[2]}")

    # 2. Search ALL tables for address-related columns
    print("\n=== ALL ADDRESS-RELATED COLUMNS ACROSS ALL TABLES ===")
    rows = db.execute(text("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE (column_name ILIKE '%address%' OR column_name ILIKE '%location%' 
               OR column_name ILIKE '%place%' OR column_name ILIKE '%area%'
               OR column_name ILIKE '%street%' OR column_name ILIKE '%house%'
               OR column_name ILIKE '%building%' OR column_name ILIKE '%site%'
               OR column_name ILIKE '%village_name%' OR column_name ILIKE '%town%'
               OR column_name ILIKE '%post%' OR column_name ILIKE '%pincode%'
               OR column_name ILIKE '%gps%' OR column_name ILIKE '%coord%')
        AND table_name NOT LIKE '%%pg%%'
        AND table_name NOT LIKE '%%sql%%'
        ORDER BY table_name, column_name
    """)).fetchall()
    for r in rows:
        print(f"  {r[0]:25s} {r[1]:25s} {r[2]}")

    # 3. Check if work_description has been updated with address data
    print("\n=== WORK_DESCRIPTION — SAMPLE WITH LENGTH > 80 ===")
    rows = db.execute(text("""
        SELECT work_id, work_description, LENGTH(work_description) as len
        FROM works
        WHERE LENGTH(work_description) > 80
        LIMIT 10
    """)).fetchall()
    for r in rows:
        print(f"  [{r[2]:3d} chars] {r[0][:40]}: {r[1][:80]}...")

    # 4. Check for any recent schema changes
    print("\n=== ALL TABLES IN DATABASE ===")
    rows = db.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)).fetchall()
    for r in rows:
        print(f"  {r[0]}")

    # 5. Check works table row structure
    print("\n=== SINGLE WORK ROW — ALL FIELDS ===")
    rows = db.execute(text("SELECT * FROM works LIMIT 1")).fetchall()
    cols = [d[0] for d in db.execute(text("SELECT * FROM works LIMIT 1")).cursor.description]
    if rows:
        for col, val in zip(cols, rows[0]):
            val_str = str(val)[:80] if val else "NULL"
            print(f"  {col:30s}: {val_str}")

    db.close()

if __name__ == "__main__":
    find_address_field()
