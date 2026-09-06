from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, asc, desc
from typing import Optional
from ..database import get_db
from ..models.work import Work
from ..models.work_sanction import WorkSanction
from ..models.work_completion import WorkCompletion
from ..models.expenditure import Expenditure
from ..models.risk_score import RiskScore
from ..schemas.ai_contract import PaginatedResponse, WorkListResponse
from ..auth.dependencies import get_current_user, get_scope_filter
from ..auth.models import DemoUser

router = APIRouter(prefix="/api", tags=["works"])

SORT_COLUMNS = {
    "work_id": Work.work_id,
    "state": Work.state,
    "constituency": Work.constituency,
    "category": Work.work_category,
    "risk": RiskScore.composite_risk,
    "priority": RiskScore.inspection_priority,
}


@router.get("/works", response_model=PaginatedResponse)
async def get_works(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    state: Optional[str] = None,
    parliament: Optional[str] = None,
    category: Optional[str] = None,
    risk_level: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    user: DemoUser = Depends(get_current_user),
):
    query = db.query(Work)

    # 1. JURISDICTION — apply scope filter FIRST
    scope = get_scope_filter(user, Work)
    if scope:
        query = query.filter(*scope)

    # 2. RISK JOIN (if needed for sorting or filtering)
    needs_risk_join = (
        (sort_by in ("risk", "priority") and risk_level is None) or
        risk_level is not None
    )
    if needs_risk_join:
        query = query.outerjoin(RiskScore, Work.work_id == RiskScore.work_id)

    # 3. SEARCH / FILTER
    if state:
        query = query.filter(Work.state == state)
    if parliament:
        query = query.filter(Work.parliament_house == parliament)
    if category:
        query = query.filter(Work.work_category == category)
    if risk_level:
        query = query.filter(RiskScore.inspection_priority == risk_level)
    if search:
        query = query.filter(or_(
            Work.work_id.ilike(f"%{search}%"),
            Work.work_description.ilike(f"%{search}%"),
            Work.constituency.ilike(f"%{search}%"),
        ))

    # 4. SORT
    if sort_by and sort_by in SORT_COLUMNS:
        col = SORT_COLUMNS[sort_by]
        query = query.order_by(desc(col) if sort_dir == "desc" else asc(col))

    # 5. PAGINATE
    total = query.count()
    works = query.offset((page - 1) * size).limit(size).all()

    items = []
    for work in works:
        sanction = db.query(WorkSanction).filter_by(work_id=work.work_id).first()

        exp_rows = db.query(
            Expenditure.vendor_name,
            Expenditure.expenditure_date,
            Expenditure.payment_status,
            Expenditure.fund_disbursed_amount
        ).filter(
            Expenditure.work_id == work.work_id,
            Expenditure.fund_disbursed_amount > 0
        ).distinct().all()

        exp_total = sum(float(r.fund_disbursed_amount) for r in exp_rows if r.fund_disbursed_amount)

        if exp_total > 0:
            amount_disbursed = exp_total
        else:
            completion = db.query(WorkCompletion).filter_by(work_id=work.work_id).first()
            if completion and completion.amount_disbursed and float(completion.amount_disbursed) > 0:
                amount_disbursed = float(completion.amount_disbursed)
            else:
                amount_disbursed = None

        risk = db.query(RiskScore).filter_by(work_id=work.work_id).first()

        items.append(WorkListResponse(
            work_id=work.work_id,
            work_description=work.work_description,
            state=work.state,
            constituency=work.constituency,
            work_category=work.work_category,
            parliament_house=work.parliament_house,
            sanction_amount=float(sanction.sanction_amount) if sanction else None,
            work_status=sanction.work_status if sanction else None,
            amount_disbursed=amount_disbursed,
            composite_risk=float(risk.composite_risk) if risk else None,
            inspection_priority=risk.inspection_priority if risk else None,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )
