"""Test geocoding on 50 works with specific place names."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
import re
import time
from sqlalchemy import text
from app.database import SessionLocal

def test_geocoding():
    db = SessionLocal()

    # Get 50 works with 'at [Place]' pattern
    rows = db.execute(text("""
        SELECT work_id, work_description, state, constituency
        FROM works
        WHERE work_description ~ 'at\\s+[A-Z][a-z]+'
          AND LENGTH(work_description) > 60
        ORDER BY RANDOM()
        LIMIT 50
    """)).fetchall()

    print(f"Testing geocoding on {len(rows)} works with place names...\n")

    from geopy.geocoders import Nominatim
    from geopy.distance import geodesic
    from geopy.exc import GeocoderTimedOut

    geolocator = Nominatim(user_agent="mplads_s_v2_test")

    success = 0
    fail = 0
    results = []

    for r in rows:
        wid, desc, state, constituency = r

        # Extract place name: "at [Place] Village/TQ/..."
        match = re.search(r'at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Village|TQ|Town|City|Block|Gram)', desc)
        if match:
            place = match.group(1)
            query = f"{place}, {state}, India"
        else:
            place = constituency
            query = f"{constituency}, {state}, India"

        try:
            location = geolocator.geocode(query, timeout=10)
            if location:
                lat, lon = location.latitude, location.longitude
                if 6 <= lat <= 37 and 68 <= lon <= 98:
                    success += 1
                    results.append((wid[:40], desc[:50], place, lat, lon, "OK"))
                    print(f"  OK    {place:25s} -> ({lat:.4f}, {lon:.4f})")
                else:
                    fail += 1
                    results.append((wid[:40], desc[:50], place, lat, lon, "OUT_OF_INDIA"))
                    print(f"  FAIL  {place:25s} -> OUT OF INDIA")
            else:
                fail += 1
                results.append((wid[:40], desc[:50], place, None, None, "NOT_FOUND"))
                print(f"  FAIL  {place:25s} -> NOT FOUND")
        except GeocoderTimedOut:
            fail += 1
            results.append((wid[:40], desc[:50], place, None, None, "TIMEOUT"))
            print(f"  FAIL  {place:25s} -> TIMEOUT")
        except Exception as e:
            fail += 1
            results.append((wid[:40], desc[:50], place, None, None, f"ERROR"))
            print(f"  FAIL  {place:25s} -> {e}")

        time.sleep(1.1)

    print(f"\n=== GEOCODING RESULTS ===")
    print(f"  Success: {success}/{len(rows)} ({success*100/len(rows):.0f}%)")
    print(f"  Failed: {fail}/{len(rows)}")

    # Proximity check
    coords = [(r[3], r[4], r[2]) for r in results if r[5] == "OK"]
    if len(coords) >= 2:
        print(f"\n=== PROXIMITY CHECK (70m threshold) ===")
        close_pairs = []
        for i in range(len(coords)):
            for j in range(i+1, len(coords)):
                dist = geodesic((coords[i][0], coords[i][1]), (coords[j][0], coords[j][1])).meters
                if dist < 70:
                    close_pairs.append((coords[i][2], coords[j][2], dist))
        
        if close_pairs:
            print(f"  Found {len(close_pairs)} pairs within 70m:")
            for p1, p2, d in close_pairs:
                print(f"    {p1} <-> {p2}: {d:.1f}m")
        else:
            print(f"  No pairs found within 70m in this sample")

        # Show distance distribution
        all_dists = []
        for i in range(len(coords)):
            for j in range(i+1, min(i+10, len(coords))):
                dist = geodesic((coords[i][0], coords[i][1]), (coords[j][0], coords[j][1])).meters
                all_dists.append(dist)
        
        if all_dists:
            all_dists.sort()
            print(f"\n  Distance distribution (sample of pairwise distances):")
            print(f"    Min: {min(all_dists):.0f}m")
            print(f"    Median: {all_dists[len(all_dists)//2]:.0f}m")
            print(f"    Max: {max(all_dists):.0f}m")
            print(f"    <100m: {sum(1 for d in all_dists if d < 100)}")
            print(f"    <1km: {sum(1 for d in all_dists if d < 1000)}")
            print(f"    >10km: {sum(1 for d in all_dists if d > 10000)}")

    db.close()

if __name__ == "__main__":
    test_geocoding()
