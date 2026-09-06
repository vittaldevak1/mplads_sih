"""Check if the vectorizer was trained on description-only or title+desc."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
import joblib
from pathlib import Path

models_dir = Path(r'C:\Users\alway\Downloads\sih\mplads_sih\backend\app\ai\engine\models')
vectorizer = joblib.load(models_dir / "tfidf_vectorizer.joblib")

print("Vectorizer type:", type(vectorizer).__name__)
print("Max features:", vectorizer.max_features)
print("Vocabulary size:", len(vectorizer.vocabulary_))

# Show top 20 feature names
features = vectorizer.get_feature_names_out()
print("\nSample features:", list(features[:30]))

# Test: transform a sample description
vec_index = joblib.load(models_dir / "historical_vector_index.joblib")
sample_meta = vec_index['sample_meta']

# Get a real description
desc = sample_meta[2]['work_description']
title = sample_meta[2].get('work_title', '')
print(f"\nSample work_description: {desc[:120]}...")
print(f"Sample work_title: {title[:120] if title else 'N/A'}...")

# Transform with description only
desc_vec = vectorizer.transform([desc])
print(f"\nDescription-only vector shape: {desc_vec.shape}")
print(f"Non-zero features: {desc_vec.nnz}")

# Transform with title+desc combined
combined = f"{title} {desc}".strip()
combined_vec = vectorizer.transform([combined])
print(f"\nTitle+Desc vector shape: {combined_vec.shape}")
print(f"Non-zero features: {combined_vec.nnz}")

# Check what the vectorizer was trained on by looking at feature patterns
print("\n--- Checking ifVectorizer was trained on desc-only ---")
# If desc-only, features should look like natural language terms
# If title+desc, features might include work-title-specific terms
print("First 50 features:")
print(list(features[:50]))
