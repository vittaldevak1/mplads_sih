"""S Signal — Step 1 & 2: Inspect database for location data."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
from sqlalchemy import text
from app.database import SessionLocal

def inspect():
    db = SessionLocal()

    print("=" * 70)
    print("S SIGNAL — LOCATION DATA INVESTIGATION")
    print("=" * 70)

    # 1. All columns across all tables that might contain location info
    print("\n=== STEP 1: ALL LOCATION-RELATED COLUMNS ===")
    rows = db.execute(text("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_name IN ('works','work_recommendations','work_sanctions',
                             'work_completions','expenditures','mp_allocations')
        AND (column_name ILIKE '%lat%' OR column_name ILIKE '%lon%' 
             OR column_name ILIKE '%coord%' OR column_name ILIKE '%geo%'
             OR column_name ILIKE '%address%' OR column_name ILIKE '%location%'
             OR column_name ILIKE '%village%' OR column_name ILIKE '%ward%'
             OR column_name ILIKE '%district%' OR column_name ILIKE '%pin%'
             OR column_name ILIKE '%city%' OR column_name ILIKE '%area%'
             OR column_name ILIKE '%place%' OR column_name ILIKE '%site%'
             OR column_name ILIKE '%state%' OR column_name ILIKE '%constituency%'
             OR column_name ILIKE '%ida%')
        ORDER BY table_name, column_name
    """)).fetchall()
    for r in rows:
        print(f"  {r[0]:25s} {r[1]:25s} {r[2]}")

    # 2. Latitude/Longitude in works table
    print("\n=== STEP 2: WORKS LATITUDE/LONGITUDE ANALYSIS ===")
    rows = db.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(latitude) as has_lat,
            COUNT(longitude) as has_long,
            COUNT(*) - COUNT(latitude) as missing_lat,
            COUNT(*) FILTER (WHERE latitude IS NOT NULL AND latitude != 0) as non_zero_lat
        FROM works
    """)).fetchall()
    r = rows[0]
    print(f"  Total works: {r[0]}")
    print(f"  Has latitude: {r[1]} ({r[1]*100/r[0]:.1f}%)")
    print(f"  Has longitude: {r[2]} ({r[2]*100/r[0]:.1f}%)")
    print(f"  Missing lat: {r[3]}")
    print(f"  Non-zero lat: {r[4]} ({r[4]*100/r[0]:.1f}%)")

    # 3. Sample actual lat/long values
    print("\n=== STEP 3: SAMPLE LAT/LONG VALUES ===")
    rows = db.execute(text("""
        SELECT work_id, latitude, longitude, state, constituency
        FROM works
        WHERE latitude IS NOT NULL AND latitude != 0
        LIMIT 15
    """)).fetchall()
    for r in rows:
        print(f"  {r[0][:50]:50s} lat={r[1]:>12} lon={r[2]:>12} {r[3]} / {r[4]}")

    # 4. Latitude range check (should be ~6-37 for India)
    print("\n=== STEP 4: LAT/LONG RANGE VALIDATION ===")
    rows = db.execute(text("""
        SELECT 
            MIN(latitude) as min_lat, MAX(latitude) as max_lat,
            MIN(longitude) as min_lon, MAX(longitude) as max_lon,
            COUNT(*) FILTER (WHERE latitude BETWEEN 6 AND 37 AND longitude BETWEEN 68 AND 98) as valid_india,
            COUNT(*) FILTER (WHERE latitude IS NOT NULL AND latitude != 0) as total_with_coords
        FROM works
    """)).fetchall()
    r = rows[0]
    print(f"  Lat range: {r[0]} to {r[1]}")
    print(f"  Lon range: {r[2]} to {r[3]}")
    print(f"  Total with coords: {r[5]}")
    print(f"  Valid India range (lat 6-37, lon 68-98): {r[4]}")
    if r[5] and r[5] > 0:
        print(f"  Valid India coords: {r[4]*100/r[5]:.1f}%")

    # 5. Works with coordinates — are they real or placeholder?
    print("\n=== STEP 5: COORDINATE DIVERSITY CHECK ===")
    rows = db.execute(text("""
        SELECT 
            COUNT(DISTINCT latitude || ',' || longitude) as unique_coords,
            COUNT(*) as total_with_coords
        FROM works
        WHERE latitude IS NOT NULL AND latitude != 0
    """)).fetchall()
    r = rows[0]
    print(f"  Unique coordinate pairs: {r[0]}")
    print(f"  Total works with coords: {r[1]}")
    if r[1] and r[1] > 0:
        print(f"  Coord uniqueness: {r[0]*100/r[1]:.1f}%")

    # 6. Address/description fields
    print("\n=== STEP 6: ADDRESS/DESCRIPTION FIELDS ===")
    rows = db.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(work_description) as has_desc,
            AVG(LENGTH(work_description)) as avg_desc_len,
            COUNT(*) FILTER (WHERE work_description IS NOT NULL AND LENGTH(work_description) > 20) as desc_gt_20
        FROM works
    """)).fetchall()
    r = rows[0]
    print(f"  Total works: {r[0]}")
    print(f"  Has description: {r[1]} ({r[1]*100/r[0]:.1f}%)")
    print(f"  Avg description length: {r[2]:.0f} chars")
    print(f"  Description > 20 chars: {r[3]} ({r[3]*100/r[0]:.1f}%)")

    db.close()

if __name__ == "__main__":
    inspect()
