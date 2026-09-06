"""Check work_id format in vector index and verify self-match exclusion approach."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
import joblib, re
from pathlib import Path

models_dir = Path(r'C:\Users\alway\Downloads\sih\mplads_sih\backend\app\ai\engine\models')
vec_index = joblib.load(models_dir / "historical_vector_index.joblib")
sample_meta = vec_index['sample_meta']

# Show work_id patterns
print("=== Work ID patterns in vector index ===")
for i in range(min(20, len(sample_meta))):
    wid = sample_meta[i].get('work_id', '')
    print(f"  [{i}] {wid[:100]}")

# Check how many unique work_ids
wids = [m.get('work_id', '') for m in sample_meta]
unique_wids = set(wids)
print(f"\nTotal meta entries: {len(sample_meta)}")
print(f"Unique work_ids: {len(unique_wids)}")

# Try to extract the actual work_id (before the dash+description)
# Pattern: WS/ MP\d+/\d{4}-\d{4}/\d+ (the actual work_id)
# The meta work_id has format: "WS/ MP620/2024-2025/133190-Description..."
# The real work_id is "WS/MP620/2024-2025/133190" (note space in WS/)

# Check a few entries for the pattern
print("\n=== Extracting real work_ids ===")
pattern = re.compile(r'(WS/\s*MP\d+/\d{4}-\d{4}/\d+)')
for i in range(min(10, len(sample_meta))):
    wid = sample_meta[i].get('work_id', '')
    match = pattern.search(wid)
    if match:
        real_id = match.group(1).replace(' ', '')
        print(f"  [{i}] full: {wid[:80]}")
        print(f"       real: {real_id}")
    else:
        print(f"  [{i}] NO MATCH: {wid[:80]}")

# Check how many have the pattern
matches = sum(1 for m in sample_meta if pattern.search(m.get('work_id', '')))
print(f"\nEntries with WS/MP pattern: {matches}/{len(sample_meta)}")
