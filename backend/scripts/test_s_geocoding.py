"""S Signal — Step 4: Test geocoding on small sample of works with specific place names."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
from sqlalchemy import text
from app.database import SessionLocal

def test_geocoding():
    db = SessionLocal()

    # Get 20 works with specific place names in descriptions
    rows = db.execute(text("""
        SELECT work_id, work_description, state, constituency
        FROM works
        WHERE work_description ~ '[A-Z][a-z]{3,} [A-Z][a-z]{3,}'
          AND work_description ILIKE '%village%'
        LIMIT 20
    """)).fetchall()

    print(f"Testing geocoding on {len(rows)} works with village names...\n")

    try:
        from geopy.geocoders import Nominatim
        from geopy.exc import GeocoderTimedOut
        import time

        geolocator = Nominatim(user_agent="mplads_s signal_test")

        success = 0
        fail = 0
        results = []

        for r in rows:
            wid, desc, state, constituency = r

            # Extract potential place name from description
            # Look for patterns like "at X Village" or "at X Near Y"
            import re
            match = re.search(r'at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Village|village)', desc)
            if not match:
                match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Village|village)', desc)

            if match:
                place = match.group(1)
                query = f"{place}, {state}, India"
            else:
                # Fallback: use constituency + state
                query = f"{constituency}, {state}, India"

            try:
                location = geolocator.geocode(query, timeout=10)
                if location:
                    lat, lon = location.latitude, location.longitude
                    # Validate India bounds
                    if 6 <= lat <= 37 and 68 <= lon <= 98:
                        success += 1
                        results.append((wid, desc[:60], place if match else constituency, lat, lon, "SUCCESS"))
                        print(f"  OK    {place if match else constituency:25s} -> ({lat:.4f}, {lon:.4f})")
                    else:
                        fail += 1
                        results.append((wid, desc[:60], place if match else constituency, lat, lon, "OUT_OF_INDIA"))
                        print(f"  FAIL  {place if match else constituency:25s} -> ({lat:.4f}, {lon:.4f}) [out of India]")
                else:
                    fail += 1
                    results.append((wid, desc[:60], place if match else constituency, None, None, "NOT_FOUND"))
                    print(f"  FAIL  {place if match else constituency:25s} -> NOT FOUND")
            except GeocoderTimedOut:
                fail += 1
                results.append((wid, desc[:60], place if match else constituency, None, None, "TIMEOUT"))
                print(f"  FAIL  {place if match else constituency:25s} -> TIMEOUT")
            except Exception as e:
                fail += 1
                results.append((wid, desc[:60], place if match else constituency, None, None, f"ERROR: {e}"))
                print(f"  FAIL  {place if match else constituency:25s} -> {e}")

            time.sleep(1.1)  # Rate limit

        print(f"\n=== GEOCODING RESULTS ===")
        print(f"  Success: {success}/{len(rows)} ({success*100/len(rows):.0f}%)")
        print(f"  Failed: {fail}/{len(rows)}")

        # Check if any geocoded points are within 70m of each other
        if success >= 2:
            print(f"\n=== PROXIMITY CHECK (70m threshold) ===")
            from geopy.distance import geodesic
            coords = [(r[3], r[4]) for r in results if r[5] == "SUCCESS"]
            close_pairs = []
            for i in range(len(coords)):
                for j in range(i+1, len(coords)):
                    dist = geodesic(coords[i], coords[j]).meters
                    if dist < 70:
                        close_pairs.append((i, j, dist))
            if close_pairs:
                print(f"  Found {len(close_pairs)} pairs within 70m:")
                for i, j, d in close_pairs:
                    print(f"    {results[i][2]} <-> {results[j][2]}: {d:.1f}m")
            else:
                print(f"  No pairs found within 70m in this sample")

    except ImportError:
        print("  geopy not installed. Install with: pip install geopy")
        print("  Skipping geocoding test.")

    db.close()

if __name__ == "__main__":
    test_geocoding()
