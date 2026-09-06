from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text
from typing import Optional
from ..database import get_db
from ..models.work import Work
from ..models.expenditure import Expenditure
from ..models.vendor import Vendor
from ..models.risk_score import RiskScore

router = APIRouter(prefix="/api", tags=["vendors"])


@router.get("/vendors")
async def get_vendors(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("total_works", pattern="^(total_works|total_expenditure|avg_risk|high_risk_count|distinct_works)$"),
    db: Session = Depends(get_db)
):
    """Vendor analytics with risk data using DISTINCT work counts."""
    vendors = db.query(Vendor).all()

    risk_stats = {}
    rows = db.execute(text("""
        SELECT e.vendor_name,
               AVG(r.composite_risk) as avg_risk,
               COUNT(DISTINCT CASE WHEN r.composite_risk > 65 THEN e.work_id END) as high_risk_count,
               COUNT(DISTINCT e.work_id) as distinct_works
        FROM expenditures e
        JOIN risk_scores r ON e.work_id = r.work_id
        WHERE e.vendor_name IS NOT NULL
        GROUP BY e.vendor_name
    """)).fetchall()
    for row in rows:
        risk_stats[row[0]] = {
            "avg_risk": round(float(row[1]), 1) if row[1] else None,
            "high_risk_count": row[2],
            "distinct_works": row[3],
        }

    results = []
    for v in vendors:
        stats = risk_stats.get(v.vendor_name, {"avg_risk": None, "high_risk_count": 0, "distinct_works": 0})
        results.append({
            "vendor_name": v.vendor_name,
            "total_works": v.total_works,
            "distinct_works": stats["distinct_works"],
            "total_expenditure": float(v.total_expenditure) if v.total_expenditure else 0,
            "avg_risk": stats["avg_risk"],
            "high_risk_count": stats["high_risk_count"],
        })

    sort_keys = {
        "total_works": lambda x: x["total_works"],
        "distinct_works": lambda x: x["distinct_works"],
        "total_expenditure": lambda x: x["total_expenditure"],
        "avg_risk": lambda x: x["avg_risk"] or 0,
        "high_risk_count": lambda x: x["high_risk_count"],
    }
    results.sort(key=sort_keys.get(sort_by, sort_keys["total_works"]), reverse=True)

    total = len(results)
    start = (page - 1) * size
    paginated = results[start:start + size]

    return {
        "items": paginated,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
    }


@router.get("/vendors/{vendor_name}")
async def get_vendor_detail(
    vendor_name: str,
    db: Session = Depends(get_db)
):
    """Detailed vendor info with recent works."""
    vendor = db.query(Vendor).filter_by(vendor_name=vendor_name).first()
    if not vendor:
        return None

    works_with_risk = db.query(
        Work.work_id, Work.work_description, Work.state, Work.constituency,
        RiskScore.composite_risk, RiskScore.inspection_priority
    ).join(
        Expenditure, Expenditure.work_id == Work.work_id
    ).outerjoin(
        RiskScore, RiskScore.work_id == Work.work_id
    ).filter(
        Expenditure.vendor_name == vendor_name
    ).distinct().order_by(desc(RiskScore.composite_risk)).limit(20).all()

    risk_dist = db.query(
        RiskScore.inspection_priority, func.count(func.distinct(RiskScore.work_id))
    ).join(
        Expenditure, Expenditure.work_id == RiskScore.work_id
    ).filter(
        Expenditure.vendor_name == vendor_name
    ).group_by(RiskScore.inspection_priority).all()

    return {
        "vendor_name": vendor.vendor_name,
        "total_works": vendor.total_works,
        "total_expenditure": float(vendor.total_expenditure) if vendor.total_expenditure else 0,
        "works": [
            {
                "work_id": w.work_id,
                "work_description": w.work_description,
                "state": w.state,
                "constituency": w.constituency,
                "composite_risk": float(w.composite_risk) if w.composite_risk else None,
                "inspection_priority": w.inspection_priority,
            }
            for w in works_with_risk
        ],
        "risk_distribution": {r[0]: r[1] for r in risk_dist if r[0]},
    }
