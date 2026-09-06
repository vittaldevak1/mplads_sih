from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.risk_score import RiskScore
from ..models.risk_signal import RiskSignal
from ..ai.interfaces.contract import SIGNAL_DEFINITIONS
from ..schemas.ai_contract import RiskScoreResponse, RiskSignalResponse

router = APIRouter(prefix="/api", tags=["risk"])

@router.get("/risk/{work_id:path}", response_model=RiskScoreResponse)
async def get_risk_score(
    work_id: str,
    db: Session = Depends(get_db)
):
    """
    Risk score + 11 signals for a work.
    Preserves available=false, score=null exactly.
    """
    risk = db.query(RiskScore).filter_by(work_id=work_id).first()
    
    if not risk:
        # Return empty structure with all 11 signals unavailable
        return RiskScoreResponse(
            work_id=work_id,
            composite_risk=None,
            confidence_coverage=None,
            inspection_priority=None,
            signals=[
                RiskSignalResponse(
                    signal_code=s["code"],
                    signal_name=s["name"],
                    version=None,
                    score=None,
                    weight=s["weight"],
                    available=False,
                    evidence=None,
                    explanation=None,
                )
                for s in SIGNAL_DEFINITIONS
            ],
            created_at=None,
            updated_at=None,
        )
    
    # Get signals from database
    signals = db.query(RiskSignal).filter_by(work_id=work_id).all()
    
    # Build signal map by code
    signal_map = {s.signal_code: s for s in signals}
    
    # Ensure all 11 signals present in response
    signals_list = []
    for defn in SIGNAL_DEFINITIONS:
        signal = signal_map.get(defn["code"])
        
        if signal:
            # Signal exists in database - use stored values
            signals_list.append(RiskSignalResponse(
                signal_code=signal.signal_code,
                signal_name=signal.signal_name,
                version=signal.version,
                score=float(signal.score) if signal.score is not None else None,
                weight=float(signal.weight),
                available=signal.available,
                evidence=signal.evidence,
                explanation=signal.explanation,
            ))
        else:
            # Signal not computed - preserve unavailable state
            signals_list.append(RiskSignalResponse(
                signal_code=defn["code"],
                signal_name=defn["name"],
                version=None,
                score=None,
                weight=defn["weight"],
                available=False,
                evidence=None,
                explanation=None,
            ))
    
    return RiskScoreResponse(
        work_id=risk.work_id,
        composite_risk=float(risk.composite_risk) if risk.composite_risk is not None else None,
        confidence_coverage=float(risk.confidence_coverage) if risk.confidence_coverage is not None else None,
        inspection_priority=risk.inspection_priority,
        signals=signals_list,
        created_at=risk.created_at.isoformat() if risk.created_at else None,
        updated_at=risk.updated_at.isoformat() if risk.updated_at else None,
    )
