from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List, Optional
from ..database import get_db, SessionLocal
from ..models.work import Work
from ..schemas.ai_contract import AIResultsRequest
from ..services.ai_adapter import AIAdapter
import subprocess
import sys
import os

router = APIRouter(prefix="/api/v1", tags=["ai"])

_audit_status = {"running": False, "last_run": None, "works_processed": 0, "total": 0}


@router.post("/audit/prepare")
async def prepare_batch_for_ai(
    work_ids: Optional[List[str]] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    adapter = AIAdapter()
    if work_ids:
        works = db.query(Work).filter(Work.work_id.in_(work_ids)).all()
    else:
        works = db.query(Work).limit(limit).all()
    ai_inputs = [adapter.prepare_work_for_ai(w, db) for w in works]
    return {"works": [inp.dict() for inp in ai_inputs]}


@router.post("/audit/batch")
async def receive_ai_batch(
    request: AIResultsRequest,
    db: Session = Depends(get_db)
):
    adapter = AIAdapter()
    adapter.store_ai_results(request.results, db)
    return {"status": "success", "stored": len(request.results)}


@router.post("/audit/run")
async def run_audit(
    limit: int = 100,
):
    global _audit_status
    if _audit_status["running"]:
        return {"status": "already_running", "processed": _audit_status["works_processed"]}

    _audit_status = {"running": True, "last_run": None, "works_processed": 0, "total": limit}

    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    script_path = os.path.join(backend_dir, "scripts", "run_full_audit.py")

    subprocess.Popen(
        [sys.executable, script_path, str(limit)],
        cwd=backend_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return {"status": "started", "total": limit}


@router.get("/audit/status")
async def get_audit_status():
    global _audit_status

    try:
        db = SessionLocal()
        r = db.execute(text("SELECT count(*) FROM risk_scores"))
        count = r.scalar() or 0
        db.close()

        if _audit_status["running"] and count > 0:
            _audit_status["works_processed"] = count
            if count >= _audit_status["total"]:
                _audit_status["running"] = False
                _audit_status["last_run"] = "completed"
    except Exception:
        pass

    return _audit_status
