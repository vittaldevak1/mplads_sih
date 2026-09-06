"""
CHECK: Does X evidence contain matched work IDs?
Also check the actual TF-IDF similarity for 'Lighting of public spaces'.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
import json
from sqlalchemy import text
from app.database import SessionLocal
from app.ai.engine import get_predictor

db = SessionLocal()
predictor = get_predictor()

print("=" * 80)
print("X SIGNAL EVIDENCE ANALYSIS")
print("=" * 80)

# 1. What's in X evidence for lighting works?
print("\n=== 1. X EVIDENCE — FULL CONTENT ===")
row = db.execute(text("""
    SELECT rs.evidence, rs.explanation FROM risk_signals rs
    JOIN works w ON rs.work_id = w.work_id
    WHERE LOWER(w.work_description) LIKE '%lighting of public spaces%'
      AND rs.signal_code = 'X'
    LIMIT 1
""")).fetchone()

ev = row[0] if isinstance(row[0], dict) else (json.loads(row[0]) if row[0] else None)
print(f"  Evidence: {json.dumps(ev, indent=2)}")
print(f"  Explanation: {row[1]}")
print(f"  Keys in evidence: {list(ev.keys()) if ev else 'None'}")
print(f"  Contains matched work IDs: {'work_id' in str(ev)}")

# 2. Run live prediction and check top_duplicate_matches
print("\n=== 2. LIVE PREDICTION — top_duplicate_matches ===")
result = predictor.predict_new_work({
    "work_id": "TEST_LIGHTING",
    "work_title": "Lighting of public spaces",
    "work_description": "Lighting of public spaces",
    "category": "Normal/Others",
    "State": "Uttar Pradesh",
    "constituency": "KUSHI NAGAR",
    "is_sc_quota": False,
    "is_st_quota": False,
    "sanction_amount": 250000.0,
    "disbursed_amount": 250000.0,
    "vendor_name": "",
    "recommended_date": None,
    "sanction_date": None,
    "completion_date": None,
})

x_signal = [s for s in result["signals"] if s["signal_code"] == "X"][0]
print(f"  X score: {x_signal['score']}")
print(f"  X evidence: {json.dumps(x_signal.get('evidence'), indent=2)}")
print(f"  X top_duplicate_matches: {json.dumps(result.get('top_duplicate_matches', []), indent=2)}")

# 3. What does the TF-IDF see?
print("\n=== 3. TF-IDF SIMILARITY DETAILS ===")
from sklearn.metrics.pairwise import cosine_similarity
query_vec = predictor.vectorizer.transform(["Lighting of public spaces"])
sims = cosine_similarity(query_vec, predictor.sample_matrix).flatten()
top_indices = sims.argsort()[::-1][:5]

print(f"  Top 5 matches from {predictor.sample_matrix.shape[0]} historical works:")
for idx in top_indices:
    sim_pct = round(float(sims[idx]) * 100.0, 1)
    meta = predictor.sample_meta[idx]
    print(f"    {sim_pct:5.1f}% — {meta.get('work_id', '?')[:50]} | {meta.get('work_title', '?')[:40]}")

# 4. Check: are the matched works historical (from training) or current batch?
print("\n=== 4. MATCHED WORK SOURCE ===")
top_match_id = predictor.sample_meta[top_indices[0]].get('work_id', '')
in_db = db.execute(text("SELECT COUNT(*) FROM works WHERE work_id = :wid"), {'wid': top_match_id}).scalar()
print(f"  Top match: {top_match_id}")
print(f"  Exists in works table: {in_db > 0}")

db.close()
