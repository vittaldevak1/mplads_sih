"""Backend adapter that prepares AI input and stores AI output."""

import json
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from ..models.work import Work
from ..models.work_recommendation import WorkRecommendation
from ..models.work_sanction import WorkSanction
from ..models.work_completion import WorkCompletion
from ..models.expenditure import Expenditure
from ..schemas.ai_contract import AIWorkInput, AIWorkOutput


class AIAdapter:
    """Prepares data for AI engine and stores results."""

    def prepare_work_for_ai(self, work: Work, db: Session) -> AIWorkInput:
        """Convert database work to AI input format."""
        recommendation = db.query(WorkRecommendation).filter_by(
            work_id=work.work_id
        ).first()

        sanction = db.query(WorkSanction).filter_by(
            work_id=work.work_id
        ).first()

        completion = db.query(WorkCompletion).filter_by(
            work_id=work.work_id
        ).first()

        # Non-duplicating disbursement hierarchy for Financial (F) signal:
        # Step 1: Aggregate valid expenditure records with deduplication of identical rows
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
            total_disbursed = exp_total
        elif completion and completion.amount_disbursed and float(completion.amount_disbursed) > 0:
            # Step 2: Fallback to work_completions.amount_disbursed if no valid expenditure records exist
            total_disbursed = float(completion.amount_disbursed)
        else:
            # Step 3: Otherwise keep disbursed_amount NULL
            total_disbursed = None

        primary_vendor_exp = db.query(Expenditure).filter(
            Expenditure.work_id == work.work_id
        ).first()
        primary_vendor = primary_vendor_exp.vendor_name if primary_vendor_exp else None

        work_title = (
            work.work_description[:100]
            if work.work_description
            else None
        )

        return AIWorkInput(
            work_id=work.work_id,
            work_title=work_title,
            work_description=work.work_description,
            sanction_amount=sanction.sanction_amount if sanction else None,
            disbursed_amount=total_disbursed if total_disbursed > 0 else None,
            vendor_name=primary_vendor,
            constituency=work.constituency,
            recommended_date=recommendation.recommended_date if recommendation else None,
            sanction_date=sanction.sanction_date if sanction else None,
            status=sanction.work_status if sanction else None,
            completion_date=completion.completion_date if completion else None,
            has_image_proof=work.has_image_proof,
            is_sc_quota=work.is_sc_quota,
            is_st_quota=work.is_st_quota,
            latitude=float(work.latitude) if work.latitude else None,
            longitude=float(work.longitude) if work.longitude else None,
            citizen_complaint_count=work.citizen_complaint_count or 0,
        )

    def prepare_batch_for_ai(
        self,
        work_ids: List[str],
        db: Session
    ) -> List[AIWorkInput]:
        """Prepare multiple works for AI engine."""
        works = db.query(Work).filter(Work.work_id.in_(work_ids)).all()
        return [self.prepare_work_for_ai(w, db) for w in works]

    def store_ai_results(
        self,
        results: List[AIWorkOutput],
        db: Session
    ):
        """Store AI results in PostgreSQL using raw SQL upserts."""
        for result in results:
            # Upsert risk score
            db.execute(text("""
                INSERT INTO risk_scores (work_id, composite_risk, confidence_coverage, inspection_priority)
                VALUES (:wid, :cr, :cc, :ip)
                ON CONFLICT (work_id) DO UPDATE SET
                    composite_risk = EXCLUDED.composite_risk,
                    confidence_coverage = EXCLUDED.confidence_coverage,
                    inspection_priority = EXCLUDED.inspection_priority,
                    updated_at = NOW()
            """), {
                "wid": result.work_id,
                "cr": result.composite_risk,
                "cc": result.confidence_coverage,
                "ip": result.inspection_priority,
            })

            # Upsert signals
            for signal in result.signals:
                # Handle both dict evidence (X signal) and list-of-SignalEvidence
                ev = signal.evidence
                if ev is None:
                    evidence_json = None
                elif isinstance(ev, dict):
                    evidence_json = json.dumps(ev)
                elif isinstance(ev, list):
                    evidence_json = json.dumps(
                        [e.dict() if hasattr(e, 'dict') else e for e in ev]
                    )
                else:
                    evidence_json = json.dumps(ev)
                db.execute(text("""
                    INSERT INTO risk_signals (work_id, signal_code, signal_name, version, score, weight, available, explanation, evidence)
                    VALUES (:wid, :sc, :sn, '1.0', :score, :w, :avail, :expl, CAST(:ev AS jsonb))
                    ON CONFLICT (work_id, signal_code) DO UPDATE SET
                        score = EXCLUDED.score,
                        weight = EXCLUDED.weight,
                        available = EXCLUDED.available,
                        explanation = EXCLUDED.explanation,
                        evidence = EXCLUDED.evidence,
                        updated_at = NOW()
                """), {
                    "wid": result.work_id,
                    "sc": signal.signal_code,
                    "sn": signal.signal_name,
                    "score": signal.score,
                    "w": signal.weight,
                    "avail": signal.available,
                    "expl": signal.explanation,
                    "ev": evidence_json,
                })

        db.commit()
