"""S Signal — Step 3: Check for works with specific location details."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
from sqlalchemy import text
from app.database import SessionLocal

def check_specific():
    db = SessionLocal()

    print("=" * 70)
    print("S SIGNAL — GEOCODING FEASIBILITY CHECK")
    print("=" * 70)

    # 1. Check for works mentioning specific places (villages, towns, etc.)
    print("\n=== WORKS MENTIONING SPECIFIC PLACE NAMES ===")
    place_patterns = [
        ('village name', '%village%name%'),
        ('near landmark', '%near %'),
        ('at/at location', '% at %'),
        ('district name in desc', '%district%'),
        ('pin code', '%pin%code%'),
        ('ward number', '%ward%'),
        ('GPS/coordinates', '%GPS%'),
        ('latitude in desc', '%latitude%'),
    ]
    for label, pattern in place_patterns:
        count = db.execute(text(
            f"SELECT COUNT(*) FROM works WHERE work_description ILIKE '{pattern}'"
        )).scalar()
        if count > 0:
            print(f"  '{label}': {count} works")

    # 2. Check descriptions for unique vs repeated templates
    print("\n=== DESCRIPTION DUPLICATION ANALYSIS ===")
    rows = db.execute(text("""
        SELECT work_description, COUNT(*) as cnt
        FROM works
        WHERE work_description IS NOT NULL
        GROUP BY work_description
        ORDER BY cnt DESC
        LIMIT 15
    """)).fetchall()
    print("  Top 15 most repeated descriptions:")
    for r in rows:
        print(f"    {r[1]:5d}x: {r[0][:70]}...")

    # 3. Check if ANY description has a proper noun (place name)
    print("\n=== DESCRIPTIONS WITH PROPER NOUNS (potential place names) ===")
    rows = db.execute(text("""
        SELECT work_id, work_description, state, constituency
        FROM works
        WHERE work_description ~ '[A-Z][a-z]{3,} [A-Z][a-z]{3,}'
        LIMIT 20
    """)).fetchall()
    for r in rows:
        print(f"  {r[0][:40]:40s} {r[1][:60]}...")

    # 4. What does constituency + state give us?
    print("\n=== CONSTITUENCY-LEVEL GRANULARITY ===")
    rows = db.execute(text("""
        SELECT state, COUNT(DISTINCT constituency) as constituencies, COUNT(*) as works
        FROM works
        WHERE state IS NOT NULL
        GROUP BY state
        ORDER BY works DESC
        LIMIT 10
    """)).fetchall()
    print("  Top 10 states:")
    for r in rows:
        print(f"    {r[0]:25s}: {r[1]:3d} constituencies, {r[2]:6d} works")

    # 5. Average works per constituency
    rows = db.execute(text("""
        SELECT AVG(cnt) as avg_works, 
               MIN(cnt) as min_works, 
               MAX(cnt) as max_works
        FROM (
            SELECT constituency, COUNT(*) as cnt
            FROM works WHERE constituency IS NOT NULL
            GROUP BY constituency
        ) sub
    """)).fetchall()
    r = rows[0]
    print(f"\n  Works per constituency: avg={r[0]:.0f}, min={r[1]}, max={r[2]}")

    # 6. Check for Bhuvan/geospatial integration
    print("\n=== GEOSPATIAL INTEGRATION CHECK ===")
    rows = db.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_name ILIKE '%geo%' OR table_name ILIKE '%spatial%' 
             OR table_name ILIKE '%h3%' OR table_name ILIKE '%satellite%'
             OR table_name ILIKE '%imagery%' OR table_name ILIKE '%bhuvan%'
    """)).fetchall()
    if rows:
        for r in rows:
            print(f"  Found table: {r[0]}")
    else:
        print("  No geospatial tables found in database.")

    # 7. Check for any existing coordinate data in expenditures
    print("\n=== EXPENDITURES TABLE ===")
    rows = db.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='expenditures'
        ORDER BY ordinal_position
    """)).fetchall()
    for r in rows:
        print(f"  {r[0]}")

    db.close()

if __name__ == "__main__":
    check_specific()
