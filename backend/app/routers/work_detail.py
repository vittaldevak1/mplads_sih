from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.work import Work
from ..models.work_recommendation import WorkRecommendation
from ..models.work_sanction import WorkSanction
from ..models.work_completion import WorkCompletion
from ..models.expenditure import Expenditure
from ..models.anomaly import Anomaly
from ..schemas.ai_contract import WorkDetailResponse
from ..auth.dependencies import get_current_user, get_scope_filter
from ..auth.models import DemoUser

router = APIRouter(prefix="/api", tags=["work-detail"])


@router.get("/works/{work_id:path}", response_model=WorkDetailResponse)
async def get_work_detail(
    work_id: str,
    db: Session = Depends(get_db),
    user: DemoUser = Depends(get_current_user),
):
    """Full work detail including anomalies, MP, and expenditures. Scoped to jurisdiction."""
    work = db.query(Work).filter_by(work_id=work_id).first()

    if not work:
        raise HTTPException(status_code=404, detail="Work not found")

    # Jurisdiction check — verify work belongs to user's scope
    scope = get_scope_filter(user, Work)
    if scope:
        allowed = db.query(Work).filter_by(work_id=work_id).filter(*scope).first()
        if not allowed:
            raise HTTPException(status_code=404, detail="Work not found in your jurisdiction")

    recommendation = db.query(WorkRecommendation).filter_by(work_id=work_id).first()
    sanction = db.query(WorkSanction).filter_by(work_id=work_id).first()
    completion = db.query(WorkCompletion).filter_by(work_id=work_id).first()

    # Non-duplicating disbursement hierarchy
    exp_rows = db.query(
        Expenditure.vendor_name,
        Expenditure.expenditure_date,
        Expenditure.payment_status,
        Expenditure.fund_disbursed_amount
    ).filter(
        Expenditure.work_id == work_id,
        Expenditure.fund_disbursed_amount > 0
    ).distinct().all()

    exp_total = sum(float(r.fund_disbursed_amount) for r in exp_rows if r.fund_disbursed_amount)

    if exp_total > 0:
        amount_disbursed = exp_total
    elif completion and completion.amount_disbursed and float(completion.amount_disbursed) > 0:
        amount_disbursed = float(completion.amount_disbursed)
    else:
        amount_disbursed = None

    primary_expenditure = db.query(Expenditure).filter_by(work_id=work_id).first()
    vendor_name = primary_expenditure.vendor_name if primary_expenditure else None

    # Get anomalies for this work
    anomalies = db.query(Anomaly).filter_by(work_id=work_id).order_by(Anomaly.created_at.desc()).all()
    anomaly_list = [
        {
            "id": a.id,
            "anomaly_type": a.anomaly_type,
            "severity": a.severity,
            "description": a.description,
            "evidence": a.evidence,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in anomalies
    ]

    # Get expenditure entries
    expenditures = db.query(Expenditure).filter_by(work_id=work_id).order_by(Expenditure.expenditure_date.desc()).limit(20).all()
    expenditure_list = [
        {
            "vendor_name": e.vendor_name,
            "expenditure_date": e.expenditure_date.isoformat() if e.expenditure_date else None,
            "fund_disbursed_amount": float(e.fund_disbursed_amount) if e.fund_disbursed_amount else None,
            "payment_status": e.payment_status,
        }
        for e in expenditures
    ]

    return WorkDetailResponse(
        work_id=work.work_id,
        work_title=work.work_title,
        work_category=work.work_category,
        work_description=work.work_description,
        state=work.state,
        ida=work.ida,
        constituency=work.constituency,
        parliament_house=work.parliament_house,
        recommended_date=recommendation.recommended_date.isoformat() if recommendation and recommendation.recommended_date else None,
        recommended_amount=float(recommendation.recommended_amount) if recommendation else None,
        sanction_date=sanction.sanction_date.isoformat() if sanction and sanction.sanction_date else None,
        sanction_amount=float(sanction.sanction_amount) if sanction else None,
        completion_date=completion.completion_date.isoformat() if completion and completion.completion_date else None,
        amount_disbursed=amount_disbursed,
        work_status=sanction.work_status if sanction else None,
        has_image_proof=work.has_image_proof,
        is_sc_quota=work.is_sc_quota,
        is_st_quota=work.is_st_quota,
        vendor_name=vendor_name,
        mp_name=recommendation.mp_name if recommendation else None,
        anomalies=anomaly_list,
        expenditures=expenditure_list,
    )
