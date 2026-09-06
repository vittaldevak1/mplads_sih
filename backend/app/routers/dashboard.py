import math
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from ..database import get_db
from ..models.work import Work
from ..models.work_recommendation import WorkRecommendation
from ..models.work_sanction import WorkSanction
from ..models.work_completion import WorkCompletion
from ..models.expenditure import Expenditure
from ..models.risk_score import RiskScore
from ..models.vendor import Vendor
from ..models.mp_allocation import MPAllocation
from ..schemas.ai_contract import DashboardSummary

router = APIRouter(prefix="/api", tags=["dashboard"])

@router.get("/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Dashboard KPIs from real data.
    Uses DISTINCT work_id counts, not raw row counts.
    """
    # Total unique works across all lifecycle tables
    total_works = db.query(func.count(func.distinct(Work.work_id))).scalar() or 0
    
    # Works by stage (snapshot counts - DISTINCT work_ids)
    works_recommended = db.query(func.count(func.distinct(WorkRecommendation.work_id))).scalar() or 0
    works_sanctioned = db.query(func.count(func.distinct(WorkSanction.work_id))).scalar() or 0
    works_completed = db.query(func.count(func.distinct(WorkCompletion.work_id))).scalar() or 0
    
    # Financial metrics
    total_sanctioned_amount = db.query(func.sum(WorkSanction.sanction_amount)).scalar() or 0
    
    # Total expenditure (raw sum)
    total_expenditure = db.query(func.sum(Expenditure.fund_disbursed_amount)).scalar() or 0
    
    # Total allocation
    total_allocation = db.query(func.sum(MPAllocation.allocated_amount)).scalar() or 0
    
    # Budget utilization (aggregate only)
    budget_utilization = (
        (float(total_expenditure) / float(total_allocation) * 100) 
        if total_allocation and total_allocation > 0 else 0
    )
    
    # Risk distribution
    high_risk = db.query(func.count(RiskScore.work_id)).filter(
        RiskScore.inspection_priority == 'HIGH'
    ).scalar() or 0
    
    medium_risk = db.query(func.count(RiskScore.work_id)).filter(
        RiskScore.inspection_priority == 'MEDIUM'
    ).scalar() or 0
    
    low_risk = db.query(func.count(RiskScore.work_id)).filter(
        RiskScore.inspection_priority == 'LOW'
    ).scalar() or 0
    
    # Active vendors
    active_vendors = db.query(func.count(func.distinct(Vendor.vendor_name))).scalar() or 0
    
    # States covered
    states_covered = db.query(func.count(func.distinct(Work.state))).scalar() or 0
    
    return DashboardSummary(
        total_works=total_works,
        works_recommended=works_recommended,
        works_sanctioned=works_sanctioned,
        works_completed=works_completed,
        total_sanctioned_amount=float(total_sanctioned_amount),
        total_expenditure=float(total_expenditure),
        total_allocation=float(total_allocation),
        budget_utilization=round(budget_utilization, 1),
        high_risk=high_risk,
        medium_risk=medium_risk,
        low_risk=low_risk,
        active_vendors=active_vendors,
        states_covered=states_covered,
    )


def _first_digit(value):
    try:
        s = f"{abs(float(value)):.10f}".replace(".", "").lstrip("0")
        return int(s[0]) if s else 0
    except Exception:
        return 0


@router.get("/dashboard/benford")
async def get_benford_distribution(db: Session = Depends(get_db)):
    """Benford's Law first-digit distribution of sanction amounts."""
    amounts = db.query(WorkSanction.sanction_amount).filter(
        WorkSanction.sanction_amount > 0
    ).all()

    digits = [_first_digit(a[0]) for a in amounts if a[0] is not None]
    digits = [d for d in digits if 1 <= d <= 9]
    n = len(digits)

    if n == 0:
        return {"sample_size": 0, "empirical": {}, "theoretical": {}}

    empirical = {str(d): round(digits.count(d) / n * 100, 2) for d in range(1, 10)}
    theoretical = {str(d): round(math.log10(1 + 1 / d) * 100, 2) for d in range(1, 10)}

    return {
        "sample_size": n,
        "empirical": empirical,
        "theoretical": theoretical,
    }


@router.get("/dashboard/state-risk")
async def get_state_risk_distribution(db: Session = Depends(get_db)):
    """Risk distribution grouped by state."""
    results = db.query(
        Work.state,
        RiskScore.inspection_priority,
        func.count(RiskScore.id)
    ).join(RiskScore, Work.work_id == RiskScore.work_id).group_by(
        Work.state, RiskScore.inspection_priority
    ).all()

    state_data = {}
    for state, priority, count in results:
        if state not in state_data:
            state_data[state] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "total": 0}
        p = priority or "LOW"
        if p in state_data[state]:
            state_data[state][p] = count
        state_data[state]["total"] += count

    sorted_states = sorted(state_data.items(), key=lambda x: x[1]["total"], reverse=True)[:20]
    return {"states": [{"state": s, **d} for s, d in sorted_states]}


@router.get("/dashboard/category-risk")
async def get_category_risk_distribution(db: Session = Depends(get_db)):
    """Risk distribution grouped by work category."""
    results = db.query(
        Work.work_category,
        RiskScore.inspection_priority,
        func.count(RiskScore.id)
    ).join(RiskScore, Work.work_id == RiskScore.work_id).group_by(
        Work.work_category, RiskScore.inspection_priority
    ).all()

    cat_data = {}
    for cat, priority, count in results:
        c = cat or "Unknown"
        if c not in cat_data:
            cat_data[c] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "total": 0}
        p = priority or "LOW"
        if p in cat_data[c]:
            cat_data[c][p] = count
        cat_data[c]["total"] += count

    sorted_cats = sorted(cat_data.items(), key=lambda x: x[1]["total"], reverse=True)[:15]
    return {"categories": [{"category": c, **d} for c, d in sorted_cats]}


@router.get("/dashboard/sankey")
async def get_sankey_flow(db: Session = Depends(get_db)):
    """Budget flow data for Sankey visualization."""
    total_recommended = db.query(func.count(func.distinct(WorkRecommendation.work_id))).scalar() or 0
    total_sanctioned = db.query(func.count(func.distinct(WorkSanction.work_id))).scalar() or 0
    total_completed = db.query(func.count(func.distinct(WorkCompletion.work_id))).scalar() or 0
    total_ongoing = total_sanctioned - total_completed

    sanctioned_amount = db.query(func.sum(WorkSanction.sanction_amount)).scalar() or 0
    disbursed_amount = db.query(func.sum(Expenditure.fund_disbursed_amount)).scalar() or 0
    unspent = float(sanctioned_amount) - float(disbursed_amount) if sanctioned_amount else 0

    return {
        "works_flow": {
            "recommended": total_recommended,
            "sanctioned": total_sanctioned,
            "completed": total_completed,
            "ongoing": max(0, total_ongoing),
        },
        "amount_flow": {
            "sanctioned": float(sanctioned_amount),
            "disbursed": float(disbursed_amount),
            "unspent": max(0, unspent),
        },
    }


@router.get("/dashboard/q-compliance")
async def get_q_compliance_summary(db: Session = Depends(get_db)):
    """Aggregate Q compliance statistics across all constituencies.

    Reports how many constituencies meet the configured SC/ST thresholds.
    Does NOT claim legal violation or discrimination — only threshold comparison.
    """
    SC_THRESHOLD = 15.0
    ST_THRESHOLD = 7.5

    rows = db.execute(text("""
        SELECT
            constituency,
            COUNT(*) AS total_works,
            COUNT(*) FILTER (WHERE w.is_sc_quota = true) AS sc_works,
            COUNT(*) FILTER (WHERE w.is_st_quota = true) AS st_works
        FROM works w
        WHERE constituency IS NOT NULL
        GROUP BY constituency
        HAVING COUNT(*) >= 10
    """)).fetchall()

    total_constituencies = len(rows)
    sc_met = 0
    st_met = 0
    both_met = 0
    neither_met = 0

    for row in rows:
        total = row[1]
        sc_pct = (row[2] / total) * 100.0
        st_pct = (row[3] / total) * 100.0
        sc_ok = sc_pct >= SC_THRESHOLD
        st_ok = st_pct >= ST_THRESHOLD
        if sc_ok and st_ok:
            both_met += 1
        elif sc_ok:
            sc_met += 1
        elif st_ok:
            st_met += 1
        else:
            neither_met += 1

    return {
        "description": "Q compliance summary — threshold comparison only, not a legal determination",
        "thresholds": {
            "sc_threshold_pct": SC_THRESHOLD,
            "st_threshold_pct": ST_THRESHOLD,
        },
        "total_constituencies_analyzed": total_constituencies,
        "sc_threshold_met": sc_met + both_met,
        "st_threshold_met": st_met + both_met,
        "both_thresholds_met": both_met,
        "neither_threshold_met": neither_met,
    }
