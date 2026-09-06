"""Test the inference pipeline with real DB data."""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.work import Work
from app.models.work_sanction import WorkSanction
from app.models.work_completion import WorkCompletion
from app.models.work_recommendation import WorkRecommendation
from app.models.expenditure import Expenditure
from app.ai.engine.inference_pipeline import predictor
from sqlalchemy import func

print("Loading predictor models...")
print(f"  D model: {type(predictor.delay_model).__name__}")
print(f"  X index: {predictor.sample_matrix.shape}")
print(f"  V registry: {len(predictor.vendor_registry)} constituencies")
print(f"  Rs model: {type(predictor.rs_model).__name__}")
print(f"  B params: {predictor.benford_params.get('sample_size', 0)} amounts")

db = SessionLocal()
try:
    # Get 5 works with full data for testing
    works = db.query(Work).limit(5).all()

    for i, work in enumerate(works):
        sanction = db.query(WorkSanction).filter_by(work_id=work.work_id).first()
        completion = db.query(WorkCompletion).filter_by(work_id=work.work_id).first()
        recommendation = db.query(WorkRecommendation).filter_by(work_id=work.work_id).first()

        total_disbursed = db.query(
            func.sum(Expenditure.fund_disbursed_amount)
        ).filter(Expenditure.work_id == work.work_id).scalar() or 0

        primary_vendor_exp = db.query(Expenditure).filter(
            Expenditure.work_id == work.work_id
        ).first()

        work_input = {
            "work_id": work.work_id,
            "work_title": work.work_description[:100] if work.work_description else "",
            "work_description": work.work_description or "",
            "category": work.work_category or "Normal/Others",
            "State": work.state or "",
            "constituency": work.constituency or "",
            "vendor_name": primary_vendor_exp.vendor_name if primary_vendor_exp else "",
            "sanction_amount": float(sanction.sanction_amount) if sanction and sanction.sanction_amount else None,
            "disbursed_amount": float(total_disbursed) if total_disbursed and total_disbursed > 0 else None,
            "is_sc_quota": work.is_sc_quota or False,
            "is_st_quota": work.is_st_quota or False,
            "recommended_date": str(recommendation.recommended_date) if recommendation and recommendation.recommended_date else None,
            "sanction_date": str(sanction.sanction_date) if sanction and sanction.sanction_date else None,
            "completion_date": str(completion.completion_date) if completion and completion.completion_date else None,
        }

        result = predictor.predict_new_work(work_input)

        print(f"\n=== Work {i+1}: {work.work_id[:60]}... ===")
        print(f"  Composite: {result['composite_risk']}")
        print(f"  Priority: {result['inspection_priority']}")
        print(f"  Coverage: {result['confidence_coverage']}")
        print(f"  Signals:")
        for sig in result["signals"]:
            status = "N/A" if not sig["available"] else f"{sig['score']}"
            print(f"    {sig['signal_code']}: {status} (weight={sig['weight']})")

finally:
    db.close()

print("\n\nSingle-work inference test PASSED.")
