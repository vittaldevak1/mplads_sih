"""S Signal — Step 2 & 3: Extract work descriptions and analyze geocodability."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
from sqlalchemy import text
from app.database import SessionLocal

def analyze_descriptions():
    db = SessionLocal()

    print("=" * 70)
    print("S SIGNAL — WORK DESCRIPTION GEOCODABILITY ANALYSIS")
    print("=" * 70)

    # Get 50 representative descriptions across different states
    rows = db.execute(text("""
        SELECT work_id, work_description, state, constituency
        FROM works
        WHERE work_description IS NOT NULL 
          AND LENGTH(work_description) > 10
        ORDER BY RANDOM()
        LIMIT 50
    """)).fetchall()

    print(f"\n=== 50 REPRESENTATIVE WORK DESCRIPTIONS ===\n")

    highly_geocodable = []
    potentially_geocodable = []
    too_vague = []

    location_keywords = [
        'road', 'bridge', 'school', 'hospital', 'building', 'hall',
        'park', 'market', 'well', 'tank', 'pond', 'dam', 'canal',
        'college', 'library', 'temple', 'mosque', 'church',
        'village', 'ward', 'block', ' Gram Panchayat', 'panchayat',
        'circle', 'colony', 'nagar', 'pur', 'ganj', 'abad',
        'road', 'highway', 'station', 'terminal', 'depot',
    ]

    vague_indicators = [
        'general', 'miscellaneous', 'others', 'normal', 'various',
        'ongoing', 'pending', 'routine',
    ]

    for r in rows:
        wid, desc, state, const = r
        desc_lower = desc.lower()

        # Check for specific location keywords
        has_location = any(kw.lower() in desc_lower for kw in location_keywords)

        # Check for vague terms
        is_vague = any(kw in desc_lower for kw in vague_indicators)

        # Check for road/village names (typically geocodable)
        has_proper_noun = any(word[0].isupper() and len(word) > 3 
                            for word in desc.split() 
                            if word not in ('Construction', 'Repair', 'Building', 'Supply', 'Installation', 'Development', 'Making', 'Providing', 'Upgradation'))

        if has_location and not is_vague:
            category = "HIGHLY GEOCODABLE"
            highly_geocodable.append((wid, desc[:80], state, const))
        elif has_proper_noun and len(desc) > 30:
            category = "POTENTIALLY GEOCODABLE"
            potentially_geocodable.append((wid, desc[:80], state, const))
        else:
            category = "TOO VAGUE"
            too_vague.append((wid, desc[:80], state, const))

        print(f"  [{category:25s}] {desc[:75]}...")

    print(f"\n=== SUMMARY ===")
    print(f"  Highly geocodable:   {len(highly_geocodable)}/50 ({len(highly_geocodable)*2}%)")
    print(f"  Potentially geocodable: {len(potentially_geocodable)}/50 ({len(potentially_geocodable)*2}%)")
    print(f"  Too vague:           {len(too_vague)}/50 ({len(too_vague)*2}%)")

    # Check how many descriptions mention specific locations
    print(f"\n=== LOCATION MENTION FREQUENCY ===")
    for keyword in ['road', 'bridge', 'school', 'village', 'ward', 'building', 'well', 'tank', 'college', 'park']:
        count = db.execute(text(f"""
            SELECT COUNT(*) FROM works 
            WHERE work_description ILIKE '%{keyword}%'
        """)).scalar()
        print(f"  '{keyword}': {count} works ({count*100/88111:.1f}%)")

    # Check if any works have explicit location in work_id
    print(f"\n=== WORK_ID PATTERNS ===")
    rows = db.execute(text("""
        SELECT work_id FROM works LIMIT 10
    """)).fetchall()
    for r in rows:
        print(f"  {r[0][:70]}")

    db.close()

if __name__ == "__main__":
    analyze_descriptions()
