"""
MPLADS AI Training Engine — Database Edition
Trains all 6 model artifacts from PostgreSQL data.
"""
import sys
sys.path.insert(0, '.')

import json
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sqlalchemy import text
from app.database import engine

from sklearn.ensemble import HistGradientBoostingRegressor, IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "ai" / "engine" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
MAX_VECTOR_FEATURES = 25_000


def first_digit(value):
    try:
        s = f"{abs(float(value)):.10f}".replace(".", "").lstrip("0")
        return int(s[0]) if s else 0
    except Exception:
        return 0


def load_data():
    print("Loading data from PostgreSQL...")
    conn = engine.connect()
    df = pd.read_sql(text("""
        SELECT w.work_id, w.work_description, w.work_category,
               w.constituency, w.state, w.parliament_house,
               w.is_sc_quota, w.is_st_quota, w.has_image_proof,
               ws.sanction_amount, ws.sanction_date, ws.work_status,
               wc.completion_date, wc.amount_disbursed,
               wr.recommended_date, wr.mp_name,
               e.vendor_name
        FROM works w
        LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
        LEFT JOIN work_completions wc ON w.work_id = wc.work_id
        LEFT JOIN work_recommendations wr ON w.work_id = wr.work_id
        LEFT JOIN expenditures e ON w.work_id = e.work_id
    """), conn)
    conn.close()
    print(f"Loaded {len(df):,} rows.")
    return df


def train_delay_model(df):
    """Train D — completion duration model."""
    print("\n[D] Training completion-duration model...")

    for col in ["recommended_date", "sanction_date", "completion_date"]:
        df[f"{col}_parsed"] = pd.to_datetime(df[col], errors="coerce")

    df["gestation_days"] = (
        df["sanction_date_parsed"] - df["recommended_date_parsed"]
    ).dt.days
    df["gestation_days"] = df["gestation_days"].fillna(30.0).clip(1.0, 730.0)

    completed = df[
        df["completion_date_parsed"].notna()
        & df["sanction_date_parsed"].notna()
    ].copy()

    completed["actual_duration_days"] = (
        completed["completion_date_parsed"] - completed["sanction_date_parsed"]
    ).dt.days

    completed = completed[
        completed["actual_duration_days"].between(15, 1500, inclusive="both")
    ].copy()

    if len(completed) < 20:
        print(f"WARNING: Only {len(completed)} completed works. Using all available.")
        if len(completed) == 0:
            print("Skipping delay model training.")
            return None

    category_map = {
        v: i for i, v in enumerate(
            df["work_category"].dropna().astype(str).unique()
        )
    }
    state_map = {
        v: i for i, v in enumerate(
            df["state"].dropna().astype(str).unique()
        )
    }

    completed["log_amount"] = np.log1p(
        pd.to_numeric(completed["sanction_amount"], errors="coerce")
        .fillna(0).clip(lower=0)
    )
    completed["cat_encoded"] = (
        completed["work_category"].astype(str).map(category_map).fillna(0)
    )
    completed["state_encoded"] = (
        completed["state"].astype(str).map(state_map).fillna(0)
    )
    completed["is_sc"] = (
        completed["is_sc_quota"].fillna(False).astype(bool).astype(int)
    )
    completed["is_st"] = (
        completed["is_st_quota"].fillna(False).astype(bool).astype(int)
    )

    feature_cols = ["log_amount", "gestation_days", "cat_encoded", "state_encoded", "is_sc", "is_st"]
    X = completed[feature_cols].to_numpy()
    y = completed["actual_duration_days"].to_numpy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_STATE
    )

    model = HistGradientBoostingRegressor(
        max_iter=150, learning_rate=0.08, max_leaf_nodes=31, random_state=RANDOM_STATE
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = r2_score(y_test, y_pred)

    print(f"D test: MAE={mae:.1f} days | RMSE={rmse:.1f} days | R2={r2:.3f}")

    joblib.dump({
        "model": model,
        "category_map": category_map,
        "state_map": state_map,
        "feature_cols": feature_cols,
        "mae": round(float(mae), 1),
        "rmse": round(rmse, 1),
        "r2": round(float(r2), 3),
        "median_duration": round(float(completed["actual_duration_days"].median()), 1),
    }, MODELS_DIR / "delay_regressor.joblib")

    print(f"Saved delay_regressor.joblib ({len(completed):,} training samples)")
    return completed


def train_duplicate_index(df):
    """Train X — text similarity index."""
    print("\n[X] Building historical text similarity index...")

    full_text = (
        df["work_description"].fillna("").astype(str)
        + " "
        + df.get("work_category", pd.Series([""]*len(df))).fillna("").astype(str)
    ).str.strip()

    valid_mask = full_text.str.strip().str.len() > 5
    full_text = full_text[valid_mask]
    meta_df = df[valid_mask]

    vectorizer = TfidfVectorizer(
        max_features=MAX_VECTOR_FEATURES,
        ngram_range=(1, 2),
        stop_words="english",
        sublinear_tf=True,
    )

    tfidf_matrix = vectorizer.fit_transform(full_text)

    joblib.dump(vectorizer, MODELS_DIR / "tfidf_vectorizer.joblib", compress=3)

    sample_meta = meta_df[
        ["work_id", "work_description", "constituency", "sanction_amount"]
    ].to_dict(orient="records")

    # Convert sparse matrix to dense for storage
    joblib.dump({
        "sample_matrix": tfidf_matrix,
        "sample_meta": sample_meta,
    }, MODELS_DIR / "historical_vector_index.joblib", compress=3)

    print(f"X index: {tfidf_matrix.shape[0]:,} works x {tfidf_matrix.shape[1]:,} features")
    return full_text


def train_vendor_registry(df):
    """Build V — vendor concentration registry."""
    print("\n[V] Building vendor concentration registry...")

    vendors = df[
        df["vendor_name"].notna()
        & ~df["vendor_name"].astype(str).str.strip().str.lower().isin({"", "unassigned", "no payment", "nan", "none"})
    ].copy()

    registry = {}

    for constituency, group in vendors.groupby(vendors["constituency"].astype(str)):
        total_outlay = float(
            pd.to_numeric(group["sanction_amount"], errors="coerce").fillna(0).sum()
        )

        counts = group["vendor_name"].astype(str).value_counts()
        sums = (
            group.assign(
                _amount=pd.to_numeric(group["sanction_amount"], errors="coerce").fillna(0)
            )
            .groupby(group["vendor_name"].astype(str))["_amount"]
            .sum()
        )

        registry[constituency] = {
            "total_works": int(len(group)),
            "total_outlay": total_outlay,
            "vendors": {},
        }

        for vendor, count in counts.items():
            outlay = float(sums.get(vendor, 0.0))
            share = outlay / total_outlay * 100.0 if total_outlay > 0 else 0.0
            registry[constituency]["vendors"][vendor] = {
                "awards_count": int(count),
                "total_won_inr": outlay,
                "market_share_pct": round(share, 1),
                "concentration_flag": bool(share >= 35.0 or int(count) >= 15),
            }

    with open(MODELS_DIR / "vendor_cartel_registry.json", "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print(f"V registry: {len(registry):,} constituencies")
    return registry


def train_rs_model(df):
    """Train supporting statistical outlier model."""
    print("\n[Rs] Training amount/gestation outlier detector...")

    amounts = pd.to_numeric(df["sanction_amount"], errors="coerce")
    median_amount = float(amounts[amounts > 0].median()) if (amounts > 0).any() else 100000.0

    for col in ["recommended_date", "sanction_date"]:
        if f"{col}_parsed" not in df.columns:
            df[f"{col}_parsed"] = pd.to_datetime(df[col], errors="coerce")

    gestation = (
        df["sanction_date_parsed"] - df["recommended_date_parsed"]
    ).dt.days.fillna(30.0).clip(1.0, 730.0)

    support_features = np.column_stack([
        np.log1p(amounts.fillna(median_amount).clip(lower=0).to_numpy()),
        gestation.to_numpy(),
    ])

    support_iso = IsolationForest(contamination=0.04, random_state=RANDOM_STATE)
    support_iso.fit(support_features)

    joblib.dump(support_iso, MODELS_DIR / "sor_isolation_forest.joblib", compress=3)
    print("Rs model saved.")


def train_benford(df):
    """Build B — Benford reference parameters."""
    print("\n[B] Building Benford population reference...")

    amounts = pd.to_numeric(df["sanction_amount"], errors="coerce")
    valid_amounts = amounts[amounts > 0].dropna()

    digits = [first_digit(v) for v in valid_amounts]
    digits = [d for d in digits if 1 <= d <= 9]

    n = len(digits)
    empirical = {
        str(d): round(digits.count(d) / n * 100, 2)
        for d in range(1, 10)
    }
    theoretical = {
        str(d): round(np.log10(1 + 1 / d) * 100, 2)
        for d in range(1, 10)
    }

    with open(MODELS_DIR / "benford_reference_params.json", "w", encoding="utf-8") as f:
        json.dump({
            "sample_size": n,
            "empirical_distribution_pct": empirical,
            "theoretical_distribution_pct": theoretical,
            "digit_9_baseline_pct": empirical.get("9", 0.0),
            "split_tender_threshold_inr": 1_000_000.0,
        }, f, indent=2)

    print(f"B params: {n:,} amounts analyzed")


def main():
    print("=" * 70)
    print("MPLADS AI TRAINING — DATABASE EDITION")
    print(f"Output: {MODELS_DIR}")
    print("=" * 70)

    df = load_data()

    train_delay_model(df)
    train_duplicate_index(df)
    train_vendor_registry(df)
    train_rs_model(df)
    train_benford(df)

    print("\n" + "=" * 70)
    print("ALL TRAINING COMPLETE.")
    print(f"Artifacts written to: {MODELS_DIR}")
    print("=" * 70)

    # Verify all artifacts exist
    artifacts = [
        "delay_regressor.joblib",
        "tfidf_vectorizer.joblib",
        "historical_vector_index.joblib",
        "vendor_cartel_registry.json",
        "sor_isolation_forest.joblib",
        "benford_reference_params.json",
    ]
    for a in artifacts:
        path = MODELS_DIR / a
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        status = f"OK ({size:,} bytes)" if exists else "MISSING"
        print(f"  {a}: {status}")


if __name__ == "__main__":
    main()
