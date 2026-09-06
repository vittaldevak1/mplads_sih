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
from ..auth.dependencies import get_current_user, get_scope_filter
from ..auth.models import DemoUser

router = APIRouter(prefix="/api", tags=["dashboard"])


def _scope_join(query, user: DemoUser, *joins):
    """Apply scope filters to a query that joins through the Work table.

    Each join should be a (Model, join_condition) tuple.
    Returns the filtered query.
    """
    from ..models.work import Work
    conditions = get_scope_filter(user, Work)
    if conditions:
        for model, condition in joins:
            query = query.join(model, condition)
        query = query.filter(*conditions)
    else:
        for model, condition in joins:
            query = query.join(model, condition)
    return query


@router.get("/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    user: DemoUser = Depends(get_current_user),
):
    """Dashboard KPIs from real data, scoped to user's jurisdiction."""
    from ..models.work import Work as W

    scope = get_scope_filter(user, W)

    # Total unique works
    q = db.query(func.count(func.distinct(W.work_id)))
    if scope:
        q = q.filter(*scope)
    total_works = q.scalar() or 0

    # Works by stage — scoped via WorkRecommendation JOIN Work
    q_rec = db.query(func.count(func.distinct(WorkRecommendation.work_id)))
    if scope:
        q_rec = q_rec.join(W, WorkRecommendation.work_id == W.work_id).filter(*scope)
    works_recommended = q_rec.scalar() or 0

    q_san = db.query(func.count(func.distinct(WorkSanction.work_id)))
    if scope:
        q_san = q_san.join(W, WorkSanction.work_id == W.work_id).filter(*scope)
    works_sanctioned = q_san.scalar() or 0

    q_com = db.query(func.count(func.distinct(WorkCompletion.work_id)))
    if scope:
        q_com = q_com.join(W, WorkCompletion.work_id == W.work_id).filter(*scope)
    works_completed = q_com.scalar() or 0

    # Financial metrics — scoped
    q_sanc_amt = db.query(func.sum(WorkSanction.sanction_amount))
    if scope:
        q_sanc_amt = q_sanc_amt.join(W, WorkSanction.work_id == W.work_id).filter(*scope)
    total_sanctioned_amount = q_sanc_amt.scalar() or 0

    q_exp = db.query(func.sum(Expenditure.fund_disbursed_amount))
    if scope:
        q_exp = q_exp.join(W, Expenditure.work_id == W.work_id).filter(*scope)
    total_expenditure = q_exp.scalar() or 0

    q_alloc = db.query(func.sum(MPAllocation.allocated_amount))
    if scope:
        q_alloc = q_alloc.filter(MPAllocation.state == user.state) if user.state else q_alloc
    total_allocation = q_alloc.scalar() or 0

    budget_utilization = (
        (float(total_expenditure) / float(total_allocation) * 100)
        if total_allocation and total_allocation > 0 else 0
    )

    # Risk distribution — scoped via RiskScore JOIN Work
    q_hr = db.query(func.count(RiskScore.work_id)).join(W, RiskScore.work_id == W.work_id)
    q_mr = db.query(func.count(RiskScore.work_id)).join(W, RiskScore.work_id == W.work_id)
    q_lr = db.query(func.count(RiskScore.work_id)).join(W, RiskScore.work_id == W.work_id)
    if scope:
        q_hr = q_hr.filter(*scope)
        q_mr = q_mr.filter(*scope)
        q_lr = q_lr.filter(*scope)
    high_risk = q_hr.filter(RiskScore.inspection_priority == 'HIGH').scalar() or 0
    medium_risk = q_mr.filter(RiskScore.inspection_priority == 'MEDIUM').scalar() or 0
    low_risk = q_lr.filter(RiskScore.inspection_priority == 'LOW').scalar() or 0

    # Active vendors — scoped via Expenditure → Work
    q_vendors = db.query(func.count(func.distinct(Vendor.vendor_name)))
    if scope:
        q_vendors = q_vendors.join(Expenditure, Expenditure.vendor_name == Vendor.vendor_name)
        q_vendors = q_vendors.join(W, Expenditure.work_id == W.work_id).filter(*scope)
    active_vendors = q_vendors.scalar() or 0

    # States covered
    q_states = db.query(func.count(func.distinct(W.work_id)))
    if scope:
        q_states = q_states.filter(*scope)
    states_covered = 1 if user.state else db.query(func.count(func.distinct(W.state))).scalar() or 0

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
async def get_benford_distribution(
    db: Session = Depends(get_db),
    user: DemoUser = Depends(get_current_user),
):
    """Benford's Law first-digit distribution of sanction amounts, scoped."""
    from ..models.work import Work as W
    q = db.query(WorkSanction.sanction_amount).filter(WorkSanction.sanction_amount > 0)
    if get_scope_filter(user, W):
        q = q.join(W, WorkSanction.work_id == W.work_id).filter(*get_scope_filter(user, W))
    amounts = q.all()

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
async def get_state_risk_distribution(
    db: Session = Depends(get_db),
    user: DemoUser = Depends(get_current_user),
):
    """Risk distribution grouped by state, scoped."""
    from ..models.work import Work as W
    q = db.query(
        Work.state,
        RiskScore.inspection_priority,
        func.count(RiskScore.id)
    ).join(RiskScore, Work.work_id == RiskScore.work_id)
    if get_scope_filter(user, W):
        q = q.filter(*get_scope_filter(user, W))
    results = q.group_by(Work.state, RiskScore.inspection_priority).all()

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
async def get_category_risk_distribution(
    db: Session = Depends(get_db),
    user: DemoUser = Depends(get_current_user),
):
    """Risk distribution grouped by work category, scoped."""
    from ..models.work import Work as W
    q = db.query(
        Work.work_category,
        RiskScore.inspection_priority,
        func.count(RiskScore.id)
    ).join(RiskScore, Work.work_id == RiskScore.work_id)
    if get_scope_filter(user, W):
        q = q.filter(*get_scope_filter(user, W))
    results = q.group_by(Work.work_category, RiskScore.inspection_priority).all()

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
async def get_sankey_flow(
    db: Session = Depends(get_db),
    user: DemoUser = Depends(get_current_user),
):
    """Budget flow data for Sankey visualization, scoped."""
    from ..models.work import Work as W
    scope = get_scope_filter(user, W)

    q_rec = db.query(func.count(func.distinct(WorkRecommendation.work_id)))
    if scope:
        q_rec = q_rec.join(W, WorkRecommendation.work_id == W.work_id).filter(*scope)
    total_recommended = q_rec.scalar() or 0

    q_san = db.query(func.count(func.distinct(WorkSanction.work_id)))
    if scope:
        q_san = q_san.join(W, WorkSanction.work_id == W.work_id).filter(*scope)
    total_sanctioned = q_san.scalar() or 0

    q_com = db.query(func.count(func.distinct(WorkCompletion.work_id)))
    if scope:
        q_com = q_com.join(W, WorkCompletion.work_id == W.work_id).filter(*scope)
    total_completed = q_com.scalar() or 0

    total_ongoing = total_sanctioned - total_completed

    q_sanc_amt = db.query(func.sum(WorkSanction.sanction_amount))
    if scope:
        q_sanc_amt = q_sanc_amt.join(W, WorkSanction.work_id == W.work_id).filter(*scope)
    sanctioned_amount = q_sanc_amt.scalar() or 0

    q_disp = db.query(func.sum(Expenditure.fund_disbursed_amount))
    if scope:
        q_disp = q_disp.join(W, Expenditure.work_id == W.work_id).filter(*scope)
    disbursed_amount = q_disp.scalar() or 0

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
async def get_q_compliance_summary(
    db: Session = Depends(get_db),
    user: DemoUser = Depends(get_current_user),
):
    """Q compliance statistics, scoped to user's jurisdiction."""
    SC_THRESHOLD = 15.0
    ST_THRESHOLD = 7.5

    scope = get_scope_filter(user)

    sql = """
        SELECT
            constituency,
            COUNT(*) AS total_works,
            COUNT(*) FILTER (WHERE w.is_sc_quota = true) AS sc_works,
            COUNT(*) FILTER (WHERE w.is_st_quota = true) AS st_works
        FROM works w
        WHERE constituency IS NOT NULL
    """
    params = {}

    if scope:
        from ..models.work import Work as W
        conditions = get_scope_filter(user, W)
        if conditions:
            # Build WHERE clause from scope filters
            from sqlalchemy import and_
            where_parts = []
            for cond in conditions:
                # Convert SQLAlchemy expression to string for raw SQL
                col = cond.left.name if hasattr(cond.left, 'name') else str(cond.left)
                if hasattr(cond, 'right') and cond.right is not None:
                    val = cond.right.value if hasattr(cond.right, 'value') else cond.right
                    if col == 'state':
                        where_parts.append(f" w.state = :scope_state")
                        params['scope_state'] = val
                    elif col == 'constituency':
                        where_parts.append(f" w.constituency = :scope_constituency")
                        params['scope_constituency'] = val
                    elif col == 'ida':
                        where_parts.append(f" w.ida ILIKE :scope_ida")
                        params['scope_ida'] = f"{val}%"
            if where_parts:
                sql += " AND " + " AND ".join(where_parts)

    sql += " GROUP BY constituency HAVING COUNT(*) >= 10"

    rows = db.execute(text(sql), params).fetchall()

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
