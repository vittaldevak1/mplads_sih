"""
MPLADS Future Data Inference Pipeline
SIH 2026 • PS 26102 • Team GRIT

Contract-aligned inference engine.

Available MVP signals:
    F, D, X, V, Q, B, Rs
Unavailable MVP signals:
    C, O, S, G

The composite risk uses only available signals and dynamically renormalizes
their locked weights.

NOTE:
The existing `sor_isolation_forest.joblib` artifact is used for Rs in this
MVP, as requested. It is a statistical cost/gestation outlier model rather
than a true district Schedule-of-Rates lookup. The UI explanation should
describe the evidence accurately and should not claim that an external SoR
database was consulted.

Q signal calculates constituency-level SC/ST quota compliance using
work-count share against configured thresholds (SC >= 15%, ST >= 7.5%).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Union

import joblib
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"


# Locked 11-signal order and weights.
SIGNALS = [
    ("F", "Financial/Cost Overrun", 0.15),
    ("D", "Delay/Duration", 0.12),
    ("X", "Semantic Duplicate Work", 0.12),
    ("V", "Vendor/Agency Network Risk", 0.10),
    ("C", "Citizen Complaints/Reports", 0.10),
    ("Q", "Compliance/Quota Violation", 0.10),
    ("O", "OCR/Document Mismatch", 0.08),
    ("S", "Spatial Duplication", 0.07),
    ("G", "Satellite Ground-Truth Change", 0.08),
    ("B", "Benford/Statistical", 0.04),
    ("Rs", "SoR Anomaly", 0.04),
]

UNAVAILABLE_MVP = {"C", "O", "S", "G"}
VERSION = "1.0"


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        result = float(value)
        return result if np.isfinite(result) else default
    except (TypeError, ValueError):
        return default


def _safe_date(value: Any):
    if value is None or value == "":
        return None
    try:
        import pandas as pd
        return pd.to_datetime(value, errors="coerce")
    except Exception:
        return None


def _clamp_score(value: float) -> float:
    return round(float(max(0.0, min(100.0, value))), 1)


class MPLADSForensicPredictor:
    """Scores incoming MPLADS works against the locked 11-signal contract."""

    def __init__(self, models_dir: Union[str, Path] = MODELS_DIR):
        self.models_dir = Path(models_dir)
        self._load_models()

    def _load_models(self):
        # D
        delay_payload = joblib.load(
            self.models_dir / "delay_regressor.joblib"
        )
        self.delay_model = delay_payload["model"]
        self.category_map = delay_payload["category_map"]
        self.state_map = delay_payload["state_map"]
        self.median_duration = float(
            delay_payload.get("median_duration", 120.0)
        )

        # X
        self.vectorizer = joblib.load(
            self.models_dir / "tfidf_vectorizer.joblib"
        )
        vec_index = joblib.load(
            self.models_dir / "historical_vector_index.joblib"
        )
        full_matrix = vec_index["sample_matrix"]
        full_meta = vec_index["sample_meta"]

        # Subsample to max 5000 rows for fast cosine similarity
        max_sample = 5000
        if full_matrix.shape[0] > max_sample:
            indices = np.linspace(0, full_matrix.shape[0] - 1, max_sample, dtype=int)
            self.sample_matrix = full_matrix[indices]
            self.sample_meta = [full_meta[i] for i in indices]
        else:
            self.sample_matrix = full_matrix
            self.sample_meta = full_meta

        # V
        with open(
            self.models_dir / "vendor_cartel_registry.json",
            "r",
            encoding="utf-8",
        ) as f:
            self.vendor_registry = json.load(f)

        # Rs
        self.rs_model = joblib.load(
            self.models_dir / "sor_isolation_forest.joblib"
        )

        # B
        with open(
            self.models_dir / "benford_reference_params.json",
            "r",
            encoding="utf-8",
        ) as f:
            self.benford_params = json.load(f)

    # ------------------------------------------------------------------
    # Helpers for individual signals
    # ------------------------------------------------------------------

    def _financial_signal(
        self, amount: float | None, disbursed: float | None
    ) -> tuple[bool, float | None, Dict[str, Any], str]:
        if amount is None or amount <= 0:
            return (
                False,
                None,
                {},
                "Financial signal unavailable: valid sanction amount is missing.",
            )

        if disbursed is None:
            return (
                False,
                None,
                {"sanction_amount": amount, "disbursed_amount": None},
                "Financial signal unavailable: disbursed amount is missing.",
            )

        ratio = disbursed / amount
        if ratio > 1.0:
            score = 95.0
            reason = (
                f"Disbursed amount exceeds sanctioned amount "
                f"({ratio:.1%} of sanction)."
            )
        elif ratio >= 0.90:
            score = 65.0
            reason = (
                f"Disbursement is high relative to sanction "
                f"({ratio:.1%})."
            )
        elif ratio >= 0.75:
            score = 35.0
            reason = (
                f"Disbursement is {ratio:.1%} of sanctioned amount; "
                f"within an elevated monitoring band."
            )
        else:
            score = 15.0
            reason = (
                f"Disbursement is {ratio:.1%} of sanctioned amount; "
                f"no high-ratio financial alert."
            )

        return (
            True,
            _clamp_score(score),
            {
                "sanction_amount": amount,
                "disbursed_amount": disbursed,
                "disbursement_to_sanction_ratio": round(ratio, 4),
            },
            reason,
        )

    def _delay_signal(
        self,
        category: str,
        state: str,
        amount: float,
        gestation_days: float,
        is_sc: bool,
        is_st: bool,
    ):
        cat_enc = self.category_map.get(category, 0)
        state_enc = self.state_map.get(state, 0)
        log_amt = np.log1p(max(amount, 0.0))

        X_input = np.array(
            [[
                log_amt,
                gestation_days,
                cat_enc,
                state_enc,
                int(is_sc),
                int(is_st),
            ]]
        )

        predicted_days = float(self.delay_model.predict(X_input)[0])
        predicted_days = max(30.0, round(predicted_days, 1))

        if gestation_days > 180:
            score = 85.0
            reason = (
                f"Gestation latency ({gestation_days:.0f} days) is severely "
                f"elevated."
            )
        elif gestation_days > 90:
            score = 55.0
            reason = (
                f"Gestation latency ({gestation_days:.0f} days) is "
                f"moderately elevated."
            )
        else:
            score = 20.0
            reason = (
                f"Gestation latency ({gestation_days:.0f} days) is within "
                f"the current monitoring baseline."
            )

        return (
            True,
            _clamp_score(score),
            {
                "observed_gestation_days": gestation_days,
                "predicted_completion_duration_days": predicted_days,
                "model_median_duration_days": self.median_duration,
            },
            reason,
            predicted_days,
        )

    def _duplicate_signal(self, work_id: str, desc: str):
        """Semantic similarity on work_description only.

        Self-match exclusion: the queried work's own ID is excluded from
        results. The work_id in the historical vector index may contain
        appended descriptions; we extract the real ID using a regex pattern.

        Evidence retains top matching historical Work IDs, similarity %,
        constituency, and sanction amount for manual verification.
        """
        import re

        if not desc or not desc.strip():
            return (
                False, None, {},
                "Duplicate signal unavailable: no description text.", []
            )

        # Extract real work_id from the queried work (normalize)
        q_real_id = re.sub(r'\s+', '', str(work_id))

        # Use description only (submitted spec: "dense cosine similarity
        # on descriptions")
        query_vec = self.vectorizer.transform([desc.strip()])
        sims = cosine_similarity(query_vec, self.sample_matrix).flatten()

        # Sort by similarity descending, take top 10 to allow self-exclusion
        top_indices = np.argsort(sims)[::-1][:10]

        top_matches: List[Dict[str, Any]] = []
        max_sim = 0.0
        checked = 0

        for idx in top_indices:
            sim_pct = round(float(sims[idx]) * 100.0, 1)
            meta = self.sample_meta[idx]
            hist_wid_raw = meta.get("work_id", "")

            # Extract real work_id from historical meta
            # Pattern: WS/ MP?\d+/\d{4}-\d{4}/\d+ possibly followed by -description
            id_match = re.search(
                r'(WS/\s*MP\d+/\d{4}-\d{4}/\d+)', hist_wid_raw
            )
            hist_real_id = (
                re.sub(r'\s+', '', id_match.group(1))
                if id_match
                else re.sub(r'\s+', '', hist_wid_raw)
            )

            # Self-match exclusion
            if hist_real_id == q_real_id:
                continue

            if sim_pct >= 35.0:
                top_matches.append({
                    "historical_work_id": hist_real_id,
                    "work_description": meta.get("work_description", ""),
                    "constituency": meta.get("constituency", ""),
                    "sanction_amount": meta.get("sanction_amount"),
                    "similarity_pct": sim_pct,
                })

            max_sim = max(max_sim, sim_pct)
            checked += 1
            if checked >= 3:
                break

        if max_sim >= 50.0:
            score = 95.0
            reason = (
                f"High semantic similarity ({max_sim:.1f}%) with a historical "
                f"work description; manual verification recommended."
            )
        elif max_sim >= 35.0:
            score = 65.0
            reason = (
                f"Moderate semantic similarity ({max_sim:.1f}%) with a "
                f"historical work description; manual verification recommended."
            )
        else:
            score = 15.0
            reason = (
                f"No high semantic similarity match found; highest "
                f"similarity was {max_sim:.1f}%."
            )

        return (
            True,
            _clamp_score(score),
            {
                "max_similarity_pct": max_sim,
                "top_duplicate_matches": top_matches,
                "vector_index_size": len(self.sample_meta),
                "self_match_excluded": True,
            },
            reason,
            top_matches,
        )

    def _vendor_signal(self, constituency: str, vendor: str):
        if not vendor or vendor.lower() in {
            "",
            "unassigned",
            "no payment",
        }:
            return (
                False,
                None,
                {},
                "Vendor signal unavailable: vendor is not assigned.",
            )

        c_data = self.vendor_registry.get(constituency, {})
        v_info = c_data.get("vendors", {}).get(vendor)

        if not v_info:
            return (
                True,
                20.0,
                {
                    "vendor": vendor,
                    "awards_count": 0,
                    "market_share_pct": 0.0,
                    "historical_vendor_record": False,
                },
                "No matching historical vendor record was found in the "
                "constituency registry.",
            )

        share = float(v_info.get("market_share_pct", 0.0))
        awards = int(v_info.get("awards_count", 0))

        if v_info.get("concentration_flag", v_info.get("is_monopoly", False)):
            score = 90.0
            reason = (
                f"High vendor concentration: {share:.1f}% historical "
                f"market share across {awards} awards."
            )
        elif awards >= 5:
            score = 60.0
            reason = (
                f"Elevated vendor concentration: {awards} historical "
                f"awards with {share:.1f}% market share."
            )
        else:
            score = 20.0
            reason = (
                f"Vendor has {awards} historical awards and {share:.1f}% "
                f"market share in the constituency registry."
            )

        return (
            True,
            _clamp_score(score),
            {
                "vendor": vendor,
                "awards_count": awards,
                "market_share_pct": share,
                "historical_vendor_record": True,
            },
            reason,
        )

    def _rs_signal(self, amount: float, gestation_days: float):
        if amount <= 0:
            return (
                False,
                None,
                {},
                "Rs signal unavailable: valid amount is missing.",
            )

        log_amt = np.log1p(amount)
        iso_input = np.array([[log_amt, gestation_days]])
        prediction = int(self.rs_model.predict(iso_input)[0])
        decision = float(self.rs_model.decision_function(iso_input)[0])

        if prediction == -1:
            score = 80.0
            reason = (
                "Statistical outlier detector flagged the work as an "
                "amount/gestation outlier; inspection is recommended."
            )
        else:
            score = 20.0
            reason = (
                "Statistical outlier detector did not flag the "
                "amount/gestation combination."
            )

        return (
            True,
            _clamp_score(score),
            {
                "outlier_flag": prediction == -1,
                "detector_decision_score": round(decision, 5),
                "amount_inr": amount,
                "gestation_days": gestation_days,
                "method": "IsolationForest statistical outlier model",
            },
            reason,
        )

    def _benford_signal(self, amount: float):
        if amount <= 0:
            return (
                False,
                None,
                {},
                "B signal unavailable: valid amount is missing.",
            )

        if 950000.0 <= amount <= 999999.0:
            score = 85.0
            reason = (
                f"Amount ₹{amount:,.0f} falls immediately below the "
                f"₹10 lakh threshold and warrants verification for "
                f"possible threshold-splitting behavior."
            )
        elif 450000.0 <= amount <= 499999.0:
            score = 65.0
            reason = (
                f"Amount ₹{amount:,.0f} falls in the monitored sub-₹5 lakh "
                f"threshold band."
            )
        else:
            score = 15.0
            reason = "No configured threshold-pattern alert was triggered."

        return (
            True,
            _clamp_score(score),
            {
                "amount_inr": amount,
                "sample_size": self.benford_params.get("sample_size"),
                "empirical_distribution_pct": self.benford_params.get(
                    "empirical_distribution_pct", {}
                ),
                "theoretical_distribution_pct": self.benford_params.get(
                    "theoretical_distribution_pct", {}
                ),
                "threshold_context_inr": self.benford_params.get(
                    "split_tender_threshold_inr"
                ),
            },
            reason,
        )

    # ------------------------------------------------------------------
    # Q — Compliance/Quota Violation signal
    # ------------------------------------------------------------------

    SC_THRESHOLD = 15.0
    ST_THRESHOLD = 7.5

    def load_constituency_stats(self, db_session) -> None:
        """Pre-compute per-constituency SC/ST work counts from the DB.

        Must be called once after predictor creation and before inference.
        Stores results in self.constituency_stats keyed by constituency name.
        """
        from sqlalchemy import text

        rows = db_session.execute(text("""
            SELECT
                constituency,
                COUNT(*)                                    AS total_works,
                COUNT(*) FILTER (WHERE is_sc_quota = true)  AS sc_works,
                COUNT(*) FILTER (WHERE is_st_quota = true)  AS st_works,
                SUM(sanction_amount)                        AS total_sanctioned,
                SUM(sanction_amount) FILTER (WHERE is_sc_quota = true) AS sc_sanctioned,
                SUM(sanction_amount) FILTER (WHERE is_st_quota = true) AS st_sanctioned
            FROM works w
            LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
            WHERE constituency IS NOT NULL
            GROUP BY constituency
        """)).fetchall()

        self.constituency_stats: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            self.constituency_stats[row[0]] = {
                "total_works": row[1],
                "sc_works": row[2],
                "st_works": row[3],
                "total_sanctioned": float(row[4]) if row[4] else 0.0,
                "sc_sanctioned": float(row[5]) if row[5] else 0.0,
                "st_sanctioned": float(row[6]) if row[6] else 0.0,
            }

    def _quota_signal(
        self, constituency: str
    ) -> tuple[bool, float | None, Dict[str, Any], str]:
        """Q — Compliance/Quota Violation signal.

        Calculates constituency-level SC/ST allocation share against
        configured thresholds using work-count ratio.

        Thresholds (locked):
            SC >= 15%
            ST >= 7.5%

        Returns (available, score, evidence, explanation).
        """
        stats = getattr(self, "constituency_stats", {}).get(constituency)

        if not stats or stats["total_works"] == 0:
            return (
                False,
                None,
                {},
                "Q signal unavailable: constituency data is insufficient for "
                "compliance evaluation.",
            )

        total = stats["total_works"]
        sc_works = stats["sc_works"]
        st_works = stats["st_works"]
        sc_pct = (sc_works / total) * 100.0
        st_pct = (st_works / total) * 100.0

        sc_deficit = max(0.0, self.SC_THRESHOLD - sc_pct) / self.SC_THRESHOLD
        st_deficit = max(0.0, self.ST_THRESHOLD - st_pct) / self.ST_THRESHOLD

        score = max(sc_deficit, st_deficit) * 100.0

        if sc_deficit >= st_deficit:
            limiting = "SC"
        elif st_deficit > sc_deficit:
            limiting = "ST"
        else:
            limiting = "NONE"

        # Supporting evidence: sanctioned-amount shares
        total_san = stats["total_sanctioned"]
        sc_amount_pct = (
            (stats["sc_sanctioned"] / total_san * 100.0) if total_san > 0 else None
        )
        st_amount_pct = (
            (stats["st_sanctioned"] / total_san * 100.0) if total_san > 0 else None
        )

        evidence = {
            "constituency": constituency,
            "total_works": total,
            "sc_works": sc_works,
            "st_works": st_works,
            "sc_percentage": round(sc_pct, 2),
            "st_percentage": round(st_pct, 2),
            "sc_threshold": self.SC_THRESHOLD,
            "st_threshold": self.ST_THRESHOLD,
            "sc_deficit": round(sc_deficit, 4),
            "st_deficit": round(st_deficit, 4),
            "limiting_factor": limiting,
            "sc_amount_share_pct": round(sc_amount_pct, 2) if sc_amount_pct is not None else None,
            "st_amount_share_pct": round(st_amount_pct, 2) if st_amount_pct is not None else None,
        }

        if score == 0.0:
            explanation = (
                f"Both SC ({sc_pct:.1f}%) and ST ({st_pct:.1f}%) allocations "
                f"meet configured thresholds; no compliance concern detected."
            )
        else:
            explanation = (
                f"Allocation below configured SC/ST threshold — requires "
                f"compliance verification. SC={sc_pct:.1f}% "
                f"(threshold {self.SC_THRESHOLD}%), ST={st_pct:.1f}% "
                f"(threshold {self.ST_THRESHOLD}%). "
                f"Limiting factor: {limiting}."
            )

        return (
            True,
            _clamp_score(score),
            evidence,
            explanation,
        )

    # ------------------------------------------------------------------
    # Main inference
    # ------------------------------------------------------------------

    def predict_new_work(self, work: Dict[str, Any]) -> Dict[str, Any]:
        title = str(work.get("work_title") or "")
        desc = str(work.get("work_description") or title)
        category = str(work.get("category") or "Normal/Others")
        state = str(work.get("State") or "")
        constituency = str(work.get("constituency") or "")
        vendor = str(work.get("vendor_name") or "")

        amount = _safe_float(work.get("sanction_amount"))
        disbursed = _safe_float(work.get("disbursed_amount"))

        is_sc = bool(work.get("is_sc_quota") or False)
        is_st = bool(work.get("is_st_quota") or False)

        gestation = _safe_float(work.get("gestation_days"))
        if gestation is None:
            rec = _safe_date(work.get("recommended_date"))
            sanction = _safe_date(work.get("sanction_date"))
            try:
                if rec is not None and sanction is not None and not (
                    np.isnat(rec) or np.isnat(sanction)
                ):
                    gestation = float((sanction - rec).days)
            except Exception:
                gestation = None

        if gestation is None:
            gestation = 30.0

        results: Dict[str, Dict[str, Any]] = {}

        available, score, evidence, explanation = self._financial_signal(
            amount, disbursed
        )
        results["F"] = self._signal(
            "F", score, available, evidence, explanation
        )

        if amount is None:
            results["D"] = self._signal(
                "D",
                None,
                False,
                {},
                "Delay signal unavailable: valid sanction amount is missing.",
            )
        else:
            (
                available,
                score,
                evidence,
                explanation,
                predicted_days,
            ) = self._delay_signal(
                category,
                state,
                amount,
                gestation,
                is_sc,
                is_st,
            )
            results["D"] = self._signal(
                "D", score, available, evidence, explanation
            )

        (
            available,
            score,
            evidence,
            explanation,
            top_matches,
        ) = self._duplicate_signal(
            work.get("work_id", ""), desc
        )
        results["X"] = self._signal(
            "X", score, available, evidence, explanation
        )

        (
            available,
            score,
            evidence,
            explanation,
        ) = self._vendor_signal(constituency, vendor)
        results["V"] = self._signal(
            "V", score, available, evidence, explanation
        )

        unavailable_explanations = {
            "C": "Citizen complaint/report data is unavailable in this MVP.",
            "O": "OCR/document-mismatch processing is unavailable in this MVP.",
            "S": "Spatial-coordinate duplication processing is unavailable in this MVP.",
            "G": "Satellite/ground-truth imagery processing is unavailable in this MVP.",
        }

        # Q — Compliance/Quota Violation (available)
        available, score, evidence, explanation = self._quota_signal(
            constituency
        )
        results["Q"] = self._signal(
            "Q", score, available, evidence, explanation
        )

        for code in ["C", "O", "S", "G"]:
            results[code] = self._signal(
                code,
                None,
                False,
                {},
                unavailable_explanations[code],
            )

        if amount is None:
            results["B"] = self._signal(
                "B",
                None,
                False,
                {},
                "B signal unavailable: valid sanction amount is missing.",
            )
            results["Rs"] = self._signal(
                "Rs",
                None,
                False,
                {},
                "Rs signal unavailable: valid sanction amount is missing.",
            )
        else:
            available, score, evidence, explanation = self._benford_signal(
                amount
            )
            results["B"] = self._signal(
                "B", score, available, evidence, explanation
            )

            available, score, evidence, explanation = self._rs_signal(
                amount, gestation
            )
            results["Rs"] = self._signal(
                "Rs", score, available, evidence, explanation
            )

        # Composite: dynamic renormalization over AVAILABLE signals only.
        available_signals = [
            results[code]
            for code, _, _ in SIGNALS
            if results[code]["available"]
            and results[code]["score"] is not None
        ]

        numerator = sum(
            s["weight"] * s["score"] for s in available_signals
        )
        denominator = sum(s["weight"] for s in available_signals)

        composite = round(numerator / denominator, 1) if denominator else 0.0
        coverage = (
            round(denominator / sum(w for _, _, w in SIGNALS), 4)
            if denominator
            else 0.0
        )

        priority = (
            "HIGH"
            if composite >= 65.0
            else "MEDIUM"
            if composite >= 40.0
            else "LOW"
        )

        return {
            "work_id": str(work.get("work_id") or ""),
            "work_title": title,
            "constituency": constituency,
            "sanction_amount_inr": amount,
            "vendor_name": vendor,
            "predicted_duration_days": (
                predicted_days if amount is not None else None
            ),
            "composite_risk": composite,
            "confidence_coverage": coverage,
            "inspection_priority": priority,
            "signals": [
                results[code]
                for code, _, _ in SIGNALS
            ],
            "top_duplicate_matches": top_matches,
            "explainable_reasons": [
                s["explanation"]
                for s in available_signals
                if s["score"] is not None
            ],
        }

    @staticmethod
    def _signal(
        code: str,
        score: float | None,
        available: bool,
        evidence: Dict[str, Any],
        explanation: str,
    ) -> Dict[str, Any]:
        signal_name = next(
            name for c, name, _ in SIGNALS if c == code
        )
        weight = next(
            weight for c, _, weight in SIGNALS if c == code
        )

        return {
            "signal_code": code,
            "signal_name": signal_name,
            "version": VERSION,
            "score": _clamp_score(score) if available and score is not None else None,
            "weight": weight,
            "available": bool(available),
            "evidence": evidence,
            "explanation": explanation,
        }


predictor = None  # Lazy-loaded via get_predictor()
