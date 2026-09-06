from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, asc, desc
from typing import Optional
from datetime import datetime
from ..database import get_db
from ..models.work import Work
from ..models.work_sanction import WorkSanction
from ..models.work_recommendation import WorkRecommendation
from ..models.risk_score import RiskScore
from ..models.risk_signal import RiskSignal
from ..models.inspection_task import InspectionTask
from ..models.activity_log import ActivityLog

router = APIRouter(prefix="/api", tags=["inspection"])

PRIORITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, None: 3}

SORT_COLUMNS = {
    "work_id": Work.work_id,
    "state": Work.state,
    "constituency": Work.constituency,
    "risk": RiskScore.composite_risk,
    "priority": RiskScore.inspection_priority,
}


class NotesRequest(BaseModel):
    notes: str = ""


class InspectorRequest(BaseModel):
    inspector_name: str = "Field Officer"


@router.get("/inspection/queue")
async def get_inspection_queue(
    priority: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    sort_by: Optional[str] = Query(None, pattern="^(work_id|state|constituency|risk|priority)$"),
    sort_dir: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    query = db.query(Work).join(
        RiskScore, Work.work_id == RiskScore.work_id
    )

    if priority:
        query = query.filter(RiskScore.inspection_priority == priority)

    if sort_by and sort_by in SORT_COLUMNS:
        col = SORT_COLUMNS[sort_by]
        query = query.order_by(desc(col) if sort_dir == "desc" else asc(col))
    else:
        query = query.order_by(RiskScore.composite_risk.desc())
    works = query.limit(limit).all()

    items = []
    for work in works:
        risk = db.query(RiskScore).filter_by(work_id=work.work_id).first()
        sanction = db.query(WorkSanction).filter_by(work_id=work.work_id).first()
        recommendation = db.query(WorkRecommendation).filter_by(work_id=work.work_id).first()

        signal_count = db.query(func.count(RiskSignal.id)).filter(
            RiskSignal.work_id == work.work_id,
            RiskSignal.available == True
        ).scalar() or 0

        # Get top triggered signals
        top_signals = db.query(
            RiskSignal.signal_code,
            RiskSignal.score,
        ).filter(
            RiskSignal.work_id == work.work_id,
            RiskSignal.available == True,
            RiskSignal.score >= 35.0,
        ).order_by(RiskSignal.score.desc()).limit(4).all()

        task = db.query(InspectionTask).filter_by(work_id=work.work_id).first()

        items.append({
            "work_id": work.work_id,
            "work_description": work.work_description,
            "work_category": work.work_category,
            "state": work.state,
            "constituency": work.constituency,
            "parliament_house": work.parliament_house,
            "mp_name": recommendation.mp_name if recommendation else None,
            "sanction_amount": float(sanction.sanction_amount) if sanction and sanction.sanction_amount else None,
            "composite_risk": float(risk.composite_risk) if risk and risk.composite_risk is not None else None,
            "inspection_priority": risk.inspection_priority if risk else None,
            "confidence_coverage": float(risk.confidence_coverage) if risk and risk.confidence_coverage is not None else None,
            "signal_count": signal_count,
            "top_signals": [{"code": s.signal_code, "score": float(s.score)} for s in top_signals],
            "task_status": task.status if task else "pending",
            "assigned_to": task.assigned_to if task else None,
            "notes": task.notes if task else None,
        })

    counts_query = db.query(
        RiskScore.inspection_priority,
        func.count(RiskScore.id)
    ).group_by(RiskScore.inspection_priority).all()

    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unanalyzed": 0}
    for priority_level, count in counts_query:
        key = priority_level.lower() if priority_level else "low"
        if key in counts:
            counts[key] = count

    total_works = db.query(func.count(Work.id)).scalar() or 0
    analyzed = sum(counts.values())
    counts["unanalyzed"] = max(0, total_works - analyzed)

    return {"items": items, "total": len(items), "counts": counts}


@router.post("/inspection/{work_id:path}/assign")
async def assign_inspection(
    work_id: str,
    body: InspectorRequest = InspectorRequest(),
    db: Session = Depends(get_db)
):
    task = db.query(InspectionTask).filter_by(work_id=work_id).first()
    if not task:
        task = InspectionTask(work_id=work_id)
        db.add(task)

    task.status = "assigned"
    task.assigned_to = body.inspector_name
    task.assigned_at = datetime.now()
    task.updated_at = datetime.now()

    log = ActivityLog(
        work_id=work_id,
        action="assign_inspection",
        actor=body.inspector_name,
        details={"status": "assigned", "inspector": body.inspector_name}
    )
    db.add(log)
    db.commit()
    return {"status": "success", "work_id": work_id, "assigned_to": body.inspector_name}


@router.post("/inspection/{work_id:path}/review")
async def review_inspection(work_id: str, db: Session = Depends(get_db)):
    task = db.query(InspectionTask).filter_by(work_id=work_id).first()
    if not task:
        task = InspectionTask(work_id=work_id)
        db.add(task)

    task.status = "in_progress"
    task.updated_at = datetime.now()

    log = ActivityLog(
        work_id=work_id, action="start_review",
        actor=task.assigned_to,
        details={"status": "in_progress"}
    )
    db.add(log)
    db.commit()
    return {"status": "success", "work_id": work_id}


@router.post("/inspection/{work_id:path}/request_docs")
async def request_documents(work_id: str, db: Session = Depends(get_db)):
    task = db.query(InspectionTask).filter_by(work_id=work_id).first()
    if not task:
        task = InspectionTask(work_id=work_id)
        db.add(task)

    task.status = "request_documents"
    task.updated_at = datetime.now()

    log = ActivityLog(
        work_id=work_id, action="request_documents",
        actor=task.assigned_to,
        details={"status": "request_documents"}
    )
    db.add(log)
    db.commit()
    return {"status": "success", "work_id": work_id}


@router.post("/inspection/{work_id:path}/field_inspect")
async def field_inspection(work_id: str, db: Session = Depends(get_db)):
    task = db.query(InspectionTask).filter_by(work_id=work_id).first()
    if not task:
        task = InspectionTask(work_id=work_id)
        db.add(task)

    task.status = "field_inspection"
    task.updated_at = datetime.now()

    log = ActivityLog(
        work_id=work_id, action="field_inspection",
        actor=task.assigned_to,
        details={"status": "field_inspection"}
    )
    db.add(log)
    db.commit()
    return {"status": "success", "work_id": work_id}


@router.post("/inspection/{work_id:path}/dismiss")
async def dismiss_inspection(
    work_id: str,
    body: NotesRequest = NotesRequest(),
    db: Session = Depends(get_db)
):
    task = db.query(InspectionTask).filter_by(work_id=work_id).first()
    if not task:
        task = InspectionTask(work_id=work_id)
        db.add(task)

    task.status = "dismissed"
    task.notes = body.notes or "No issues found"
    task.updated_at = datetime.now()

    log = ActivityLog(
        work_id=work_id, action="dismiss_inspection",
        actor=task.assigned_to,
        details={"status": "dismissed", "reason": body.notes}
    )
    db.add(log)
    db.commit()
    return {"status": "success", "work_id": work_id}


@router.post("/inspection/{work_id:path}/complete")
async def complete_inspection(
    work_id: str,
    body: NotesRequest = NotesRequest(),
    db: Session = Depends(get_db)
):
    task = db.query(InspectionTask).filter_by(work_id=work_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="No inspection task found")

    task.status = "completed"
    task.notes = body.notes or task.notes
    task.updated_at = datetime.now()

    log = ActivityLog(
        work_id=work_id, action="complete_inspection",
        actor=task.assigned_to,
        details={"status": "completed", "notes": body.notes}
    )
    db.add(log)
    db.commit()
    return {"status": "success", "work_id": work_id}


@router.put("/inspection/{work_id:path}/notes")
async def update_notes(
    work_id: str,
    body: NotesRequest,
    db: Session = Depends(get_db)
):
    task = db.query(InspectionTask).filter_by(work_id=work_id).first()
    if not task:
        task = InspectionTask(work_id=work_id)
        db.add(task)

    task.notes = body.notes
    task.updated_at = datetime.now()

    log = ActivityLog(
        work_id=work_id, action="update_notes",
        actor=task.assigned_to,
        details={"notes": body.notes}
    )
    db.add(log)
    db.commit()
    return {"status": "success", "work_id": work_id}


@router.get("/inspection/{work_id:path}/history")
async def get_inspection_history(work_id: str, db: Session = Depends(get_db)):
    logs = db.query(ActivityLog).filter_by(
        work_id=work_id
    ).order_by(ActivityLog.created_at.desc()).limit(50).all()

    return {
        "work_id": work_id,
        "history": [
            {
                "id": log.id,
                "action": log.action,
                "actor": log.actor,
                "details": log.details,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
    }
