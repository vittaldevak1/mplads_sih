from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, asc, desc
from typing import Optional
from ..database import get_db
from ..models.risk_signal import RiskSignal
from ..models.risk_score import RiskScore
from ..models.work import Work
from ..models.work_recommendation import WorkRecommendation
from ..models.work_sanction import WorkSanction
from ..models.inspection_task import InspectionTask

router = APIRouter(prefix="/api", tags=["anomalies"])

UNAVAILABLE_SIGNALS = {"C", "O", "S", "G"}

# Signal-level thresholds for flagging elevated signals
SIGNAL_THRESHOLDS = {
    "F": {"score": 65, "label": "Financial Disbursement Alert", "severity": "HIGH",
           "desc": "Elevated disbursement-to-sanction ratio detected; requires verification."},
    "X": {"score": 65, "label": "Semantic Similarity Alert", "severity": "HIGH",
           "desc": "High semantic similarity with historical work description; manual verification recommended."},
    "V": {"score": 60, "label": "Vendor Concentration Alert", "severity": "HIGH",
           "desc": "Vendor concentration/network risk detected; requires review."},
    "D": {"score": 55, "label": "Delay Alert", "severity": "MEDIUM",
           "desc": "Moderate gestation delay detected; monitoring recommended."},
    "B": {"score": 65, "label": "Statistical Threshold Alert", "severity": "MEDIUM",
           "desc": "Statistical threshold pattern detected; requires verification."},
    "Rs": {"score": 80, "label": "Cost Outlier Alert", "severity": "MEDIUM",
            "desc": "Statistical cost/gestation outlier detected; requires review."},
    "Q": {"score": 100, "label": "Quota Compliance Indicator", "severity": "INFO",
           "desc": "Constituency allocation below configured SC/ST threshold — systemic policy indicator."},
}

SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "INFO": 2, "LOW": 3}


@router.get("/anomalies")
async def get_anomalies(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    severity: Optional[str] = None,
    anomaly_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Paginated risk-flagged items driven by live risk_signals and risk_scores.

    Categories:
    - HIGH_RISK: Works with composite risk >= 65 requiring inspection
    - Signal codes (F, D, X, V, Q, B, Rs): Individual elevated signal alerts
    - C, O, S, G: Return unavailable message
    """
    # Handle unavailable signals
    if anomaly_type in UNAVAILABLE_SIGNALS:
        return {
            "items": [],
            "total": 0,
            "page": page,
            "size": size,
            "pages": 0,
            "signal_unavailable": True,
            "message": f"Signal '{anomaly_type}' source data is unavailable in this MVP.",
        }

    # Specific available signal filter
    if anomaly_type and anomaly_type != "HIGH_RISK" and anomaly_type in SIGNAL_THRESHOLDS:
        threshold = SIGNAL_THRESHOLDS[anomaly_type]
        min_score = threshold["score"]

        query = db.query(
            RiskSignal.id,
            RiskSignal.work_id,
            RiskSignal.signal_code,
            RiskSignal.signal_name,
            RiskSignal.score,
            RiskSignal.explanation,
            RiskSignal.evidence,
            RiskScore.composite_risk,
            RiskScore.inspection_priority,
            Work.work_description,
            Work.state,
            Work.constituency,
            InspectionTask.status.label("task_status"),
        ).join(
            RiskScore, RiskSignal.work_id == RiskScore.work_id
        ).join(
            Work, RiskSignal.work_id == Work.work_id
        ).outerjoin(
            InspectionTask, RiskSignal.work_id == InspectionTask.work_id
        ).filter(
            RiskSignal.signal_code == anomaly_type,
            RiskSignal.available == True,
            RiskSignal.score >= min_score,
        )

        if severity:
            if severity == "HIGH":
                query = query.filter(RiskSignal.score >= 65.0)
            elif severity == "MEDIUM":
                query = query.filter(RiskSignal.score >= 40.0, RiskSignal.score < 65.0)

        query = query.order_by(RiskSignal.score.desc(), RiskSignal.id.desc())
        total = query.count()
        results = query.offset((page - 1) * size).limit(size).all()

        items = []
        for r in results:
            sig_score = float(r.score) if r.score is not None else 0.0
            sev = "HIGH" if sig_score >= 65.0 else "MEDIUM" if sig_score >= 40.0 else "INFO"
            items.append({
                "id": f"{r.signal_code}-{r.work_id}",
                "work_id": r.work_id,
                "signal_code": r.signal_code,
                "signal_name": r.signal_name,
                "anomaly_type": threshold["label"],
                "score": sig_score,
                "severity": sev,
                "composite_risk": float(r.composite_risk) if r.composite_risk is not None else None,
                "inspection_priority": r.inspection_priority,
                "state": r.state,
                "constituency": r.constituency,
                "description": r.explanation or threshold["desc"],
                "evidence": r.evidence,
                "task_status": r.task_status or "pending",
            })

    else:
        # High Risk: works with composite >= 65
        query = db.query(
            RiskScore.id,
            RiskScore.work_id,
            RiskScore.composite_risk,
            RiskScore.confidence_coverage,
            RiskScore.inspection_priority,
            Work.work_description,
            Work.state,
            Work.constituency,
            InspectionTask.status.label("task_status"),
        ).join(
            Work, RiskScore.work_id == Work.work_id
        ).outerjoin(
            InspectionTask, RiskScore.work_id == InspectionTask.work_id
        ).filter(
            RiskScore.composite_risk >= 65.0,
        )

        if severity:
            query = query.filter(RiskScore.inspection_priority == severity)

        query = query.order_by(RiskScore.composite_risk.desc(), RiskScore.id.desc())
        total = query.count()
        results = query.offset((page - 1) * size).limit(size).all()

        # Get top triggered signals for each work
        items = []
        for r in results:
            comp_risk = float(r.composite_risk) if r.composite_risk is not None else 0.0
            sev = r.inspection_priority or "HIGH"

            # Get top signals for this work
            top_signals = db.query(
                RiskSignal.signal_code,
                RiskSignal.score,
                RiskSignal.available,
            ).filter(
                RiskSignal.work_id == r.work_id,
                RiskSignal.available == True,
                RiskSignal.score >= 35.0,
            ).order_by(RiskSignal.score.desc()).limit(4).all()

            triggered = [
                {"code": s.signal_code, "score": float(s.score)}
                for s in top_signals
            ]

            items.append({
                "id": f"COMPOSITE-{r.work_id}",
                "work_id": r.work_id,
                "signal_code": "COMPOSITE",
                "signal_name": "Composite Risk",
                "anomaly_type": "High-Risk Work Requiring Inspection",
                "score": comp_risk,
                "severity": sev,
                "composite_risk": comp_risk,
                "confidence_coverage": float(r.confidence_coverage) if r.confidence_coverage else None,
                "inspection_priority": r.inspection_priority,
                "state": r.state,
                "constituency": r.constituency,
                "description": (
                    r.work_description
                    or f"Composite risk {comp_risk:.1f} — high-priority inspection candidate."
                ),
                "evidence": {
                    "composite_risk": comp_risk,
                    "priority": sev,
                    "top_signals": triggered,
                },
                "triggered_signals": triggered,
                "task_status": r.task_status or "pending",
            })

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 0,
        "signal_unavailable": False,
    }
