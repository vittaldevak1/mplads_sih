"""Profile work_description field for address/geocoding potential."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
import re
from sqlalchemy import text
from app.database import SessionLocal

def profile_addresses():
    db = SessionLocal()

    print("=" * 70)
    print("WORK_DESCRIPTION ADDRESS PROFILING")
    print("=" * 70)

    # 1. Basic stats
    print("\n=== BASIC STATISTICS ===")
    rows = db.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(work_description) as has_desc,
            AVG(LENGTH(work_description)) as avg_len,
            MIN(LENGTH(work_description)) as min_len,
            MAX(LENGTH(work_description)) as max_len,
            COUNT(DISTINCT work_description) as unique_desc
        FROM works
    """)).fetchall()
    r = rows[0]
    print(f"  Total works: {r[0]}")
    print(f"  Has description: {r[1]} ({r[1]*100/r[0]:.1f}%)")
    print(f"  Avg length: {r[2]:.0f} chars")
    print(f"  Min length: {r[3]}")
    print(f"  Max length: {r[4]}")
    print(f"  Unique descriptions: {r[5]} ({r[5]*100/r[0]:.1f}%)")

    # 2. Descriptions with "at" + place name pattern
    print("\n=== ADDRESS PATTERN ANALYSIS ===")
    patterns = {
        'at [Place] Village': r'at\s+\w+\s+Village',
        'at [Place] TQ': r'at\s+\w+\s+TQ',
        'Near [Landmark]': r'Near\s+\w+',
        'Ward No': r'Ward\s+No',
        'Pry No': r'Pry\s+No',
        'Gram Panchayat': r'Gram\s+Panchayat',
        'Block': r'Block\s+\w+',
        'District': r'District\s+\w+',
        'Pin': r'Pin\s+\d{6}',
        'GPS/Coordinates': r'GPS|latitude|longitude|coordinates',
    }
    for label, pattern in patterns.items():
        count = db.execute(text(
            f"SELECT COUNT(*) FROM works WHERE work_description ~ '{pattern}'"
        )).scalar()
        print(f"  {label:25s}: {count:6d} works ({count*100/88111:.1f}%)")

    # 3. Length distribution
    print("\n=== LENGTH DISTRIBUTION ===")
    ranges = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100), (100, 150), (150, 300)]
    for low, high in ranges:
        count = db.execute(text(f"""
            SELECT COUNT(*) FROM works 
            WHERE LENGTH(work_description) >= {low} AND LENGTH(work_description) < {high}
        """)).scalar()
        bar = '#' * (count // 500)
        print(f"  {low:3d}-{high:3d} chars: {count:6d} {bar}")

    # 4. Top 20 most common descriptions
    print("\n=== TOP 20 MOST COMMON DESCRIPTIONS ===")
    rows = db.execute(text("""
        SELECT work_description, COUNT(*) as cnt
        FROM works
        WHERE work_description IS NOT NULL
        GROUP BY work_description
        ORDER BY cnt DESC
        LIMIT 20
    """)).fetchall()
    for r in rows:
        print(f"  {r[1]:5d}x: {r[0][:70]}...")

    # 5. Descriptions with specific place names (geocodable candidates)
    print("\n=== GEOCODABLE CANDIDATES (with place names) ===")
    rows = db.execute(text("""
        SELECT work_id, work_description, state, constituency
        FROM works
        WHERE work_description ~ 'at\s+[A-Z][a-z]+'
          AND LENGTH(work_description) > 60
        LIMIT 30
    """)).fetchall()
    print(f"  Sample of {len(rows)} works with 'at [Place]' pattern:")
    for r in rows:
        print(f"  {r[0][:35]:35s} {r[1][:65]}...")

    # 6. Unique place names extraction
    print("\n=== PLACE NAME EXTRACTION ===")
    rows = db.execute(text("SELECT work_description FROM works WHERE work_description IS NOT NULL")).fetchall()
    place_pattern = re.compile(r'at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Village|TQ|Town|City|Block|Gram)')
    places = []
    for r in rows:
        matches = place_pattern.findall(r[0])
        places.extend(matches)
    
    from collections import Counter
    place_counts = Counter(places)
    print(f"  Total place name mentions: {len(places)}")
    print(f"  Unique place names: {len(place_counts)}")
    print(f"\n  Top 20 places:")
    for place, count in place_counts.most_common(20):
        print(f"    {count:4d}x: {place}")

    # 7. Geographic spread
    print("\n=== GEOGRAPHIC SPREAD OF PLACE NAMES ===")
    rows = db.execute(text("""
        SELECT state, COUNT(*) as cnt
        FROM works
        WHERE work_description ~ 'at\s+[A-Z][a-z]+'
        GROUP BY state
        ORDER BY cnt DESC
        LIMIT 10
    """)).fetchall()
    for r in rows:
        print(f"  {r[0]:25s}: {r[1]:5d} geocodable works")

    db.close()

if __name__ == "__main__":
    profile_addresses()
