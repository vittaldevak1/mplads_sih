"""Inspect the X signal vector index to understand metadata structure."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
import joblib
from pathlib import Path

models_dir = Path(r'C:\Users\alway\Downloads\sih\mplads_sih\backend\app\ai\engine\models')
vec_index = joblib.load(models_dir / "historical_vector_index.joblib")

print("Keys:", list(vec_index.keys()))
print("Matrix shape:", vec_index['sample_matrix'].shape)
print("Meta length:", len(vec_index['sample_meta']))

# Show first 3 meta entries
for i in range(min(3, len(vec_index['sample_meta']))):
    m = vec_index['sample_meta'][i]
    print(f"\nMeta[{i}]:")
    for k, v in m.items():
        val = str(v)[:80] if v else v
        print(f"  {k}: {val}")

# Check if work_id is in meta
sample_meta = vec_index['sample_meta']
has_work_id = sum(1 for m in sample_meta if 'work_id' in m)
print(f"\nMeta entries with work_id: {has_work_id}/{len(sample_meta)}")

# Check a few work_ids
for i in range(0, min(5, len(sample_meta))):
    wid = sample_meta[i].get('work_id', 'MISSING')
    print(f"  [{i}] work_id: {wid}")
