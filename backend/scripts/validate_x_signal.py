"""Validate X signal fix: self-match exclusion, description-only, evidence storage."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')

import joblib, re
import numpy as np
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity

models_dir = Path(r'C:\Users\alway\Downloads\sih\mplads_sih\backend\app\ai\engine\models')
vectorizer = joblib.load(models_dir / "tfidf_vectorizer.joblib")
vec_index = joblib.load(models_dir / "historical_vector_index.joblib")

full_matrix = vec_index['sample_matrix']
full_meta = vec_index['sample_meta']

# Subsample like the predictor does
max_sample = 5000
if full_matrix.shape[0] > max_sample:
    indices = np.linspace(0, full_matrix.shape[0] - 1, max_sample, dtype=int)
    sample_matrix = full_matrix[indices]
    sample_meta = [full_meta[i] for i in indices]
else:
    sample_matrix = full_matrix
    sample_meta = full_meta

print(f"Sample matrix: {sample_matrix.shape}")

# Test with a real work from the DB
from sqlalchemy import text
from app.database import SessionLocal
db = SessionLocal()

# Get a few works with their descriptions
works = db.execute(text("""
    SELECT w.work_id, w.work_description, w.state, w.constituency
    FROM works w
    JOIN risk_signals rs ON w.work_id = rs.work_id AND rs.signal_code='X'
    WHERE rs.available = true AND rs.score >= 95
    LIMIT 5
""")).fetchall()

print(f"\n=== Testing {len(works)} high-X works ===")

for wid, desc, state, const in works:
    print(f"\n--- {wid} ---")
    print(f"  Description: {str(desc)[:100]}...")

    q_real_id = re.sub(r'\s+', '', wid)
    query_vec = vectorizer.transform([desc.strip()])
    sims = cosine_similarity(query_vec, sample_matrix).flatten()
    top_indices = np.argsort(sims)[::-1][:10]

    max_sim = 0.0
    self_matches = 0
    non_self_matches = 0
    top_matches = []

    for idx in top_indices:
        sim_pct = round(float(sims[idx]) * 100.0, 1)
        meta = sample_meta[idx]
        hist_wid_raw = meta.get("work_id", "")

        id_match = re.search(r'(WS/\s*MP\d+/\d{4}-\d{4}/\d+)', hist_wid_raw)
        hist_real_id = re.sub(r'\s+', '', id_match.group(1)) if id_match else re.sub(r'\s+', '', hist_wid_raw)

        if hist_real_id == q_real_id:
            self_matches += 1
            continue

        non_self_matches += 1
        max_sim = max(max_sim, sim_pct)

        if sim_pct >= 35.0 and len(top_matches) < 3:
            top_matches.append({
                "work_id": hist_real_id,
                "similarity": sim_pct,
                "desc": meta.get('work_description', '')[:80],
            })
        if non_self_matches >= 3:
            break

    print(f"  Self-matches excluded: {self_matches}")
    print(f"  Max similarity (non-self): {max_sim:.1f}%")
    print(f"  Top matches: {len(top_matches)}")
    for m in top_matches:
        print(f"    {m['work_id'][:40]}: {m['similarity']:.1f}% - {m['desc'][:60]}")

db.close()

# Also test: find works that are genuinely distinctive (low similarity)
print("\n=== Testing 3 low-X works ===")
db = SessionLocal()
works = db.execute(text("""
    SELECT w.work_id, w.work_description
    FROM works w
    JOIN risk_signals rs ON w.work_id = rs.work_id AND rs.signal_code='X'
    WHERE rs.available = true AND rs.score <= 15
    LIMIT 3
""")).fetchall()

for wid, desc in works:
    if not desc:
        continue
    print(f"\n--- {wid} ---")
    print(f"  Description: {str(desc)[:100]}...")
    q_real_id = re.sub(r'\s+', '', wid)
    query_vec = vectorizer.transform([desc.strip()])
    sims = cosine_similarity(query_vec, sample_matrix).flatten()
    top_indices = np.argsort(sims)[::-1][:10]
    max_sim = 0.0
    for idx in top_indices:
        sim_pct = round(float(sims[idx]) * 100.0, 1)
        meta = sample_meta[idx]
        hist_wid_raw = meta.get("work_id", "")
        id_match = re.search(r'(WS/\s*MP\d+/\d{4}-\d{4}/\d+)', hist_wid_raw)
        hist_real_id = re.sub(r'\s+', '', id_match.group(1)) if id_match else re.sub(r'\s+', '', hist_wid_raw)
        if hist_real_id == q_real_id:
            continue
        max_sim = max(max_sim, sim_pct)
        break
    print(f"  Max similarity (non-self): {max_sim:.1f}%")
db.close()
