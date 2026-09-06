import sys
sys.path.insert(0, '.')
import json
from datetime import datetime
from sqlalchemy import text
from app.database import SessionLocal
from app.ai.engine import get_predictor_with_stats

_audit_status = {"running": False, "last_run": None, "works_processed": 0, "total": 0}

def run_audit(limit):
    global _audit_status
    _audit_status = {"running": True, "last_run": None, "works_processed": 0, "total": limit}

    try:
        db = SessionLocal()
        predictor = get_predictor_with_stats(db)
        print(f"Predictor loaded. X matrix: {predictor.sample_matrix.shape}", flush=True)
        print(f"Constituency stats loaded: {len(predictor.constituency_stats)} constituencies", flush=True)

        # Bulk fetch all work data
        print(f"Fetching {limit} works with JOINs...", flush=True)
        rows = db.execute(text("""
            SELECT w.work_id, w.work_description, w.work_category, w.state,
                   w.constituency, w.is_sc_quota, w.is_st_quota,
                   ws.sanction_amount, ws.sanction_date,
                   wc.completion_date,
                   wr.recommended_date,
                   COALESCE(d.total_disbursed, 0) as total_disbursed,
                   v.vendor_name
            FROM works w
            LEFT JOIN work_sanctions ws ON w.work_id = ws.work_id
            LEFT JOIN work_completions wc ON w.work_id = wc.work_id
            LEFT JOIN work_recommendations wr ON w.work_id = wr.work_id
            LEFT JOIN (
                SELECT work_id, SUM(fund_disbursed_amount) as total_disbursed
                FROM expenditures
                GROUP BY work_id
            ) d ON w.work_id = d.work_id
            LEFT JOIN (
                SELECT DISTINCT ON (work_id) work_id, vendor_name
                FROM expenditures
            ) v ON w.work_id = v.work_id
            ORDER BY w.id
            LIMIT :lim
        """), {"lim": limit}).fetchall()

        total = len(rows)
        _audit_status["total"] = total
        print(f"Fetched {total} works. Starting inference...", flush=True)

        stored = 0
        for idx, row in enumerate(rows):
            work_input = {
                "work_id": row[0] or "",
                "work_title": (row[1] or "")[:100],
                "work_description": row[1] or "",
                "category": row[2] or "Normal/Others",
                "State": row[3] or "",
                "constituency": row[4] or "",
                "is_sc_quota": bool(row[5]),
                "is_st_quota": bool(row[6]),
                "sanction_amount": float(row[7]) if row[7] else None,
                "disbursed_amount": float(row[11]) if row[11] and float(row[11]) > 0 else None,
                "vendor_name": row[12] or "",
                "recommended_date": str(row[10]) if row[10] else None,
                "sanction_date": str(row[8]) if row[8] else None,
                "completion_date": str(row[9]) if row[9] else None,
            }

            result = predictor.predict_new_work(work_input)

            composite = result["composite_risk"]
            priority = result["inspection_priority"]
            confidence = result["confidence_coverage"]

            db.execute(text("""
                INSERT INTO risk_scores (work_id, composite_risk, confidence_coverage, inspection_priority)
                VALUES (:wid, :cr, :cc, :ip)
                ON CONFLICT (work_id) DO UPDATE SET
                    composite_risk = EXCLUDED.composite_risk,
                    confidence_coverage = EXCLUDED.confidence_coverage,
                    inspection_priority = EXCLUDED.inspection_priority,
                    updated_at = NOW()
            """), {"wid": row[0], "cr": composite, "cc": confidence, "ip": priority})

            for sig in result["signals"]:
                evidence_json = json.dumps(sig.get("evidence")) if sig.get("evidence") else None
                db.execute(text("""
                    INSERT INTO risk_signals (work_id, signal_code, signal_name, version, score, weight, available, explanation, evidence)
                    VALUES (:wid, :sc, :sn, '1.0', :score, :w, :avail, :expl, CAST(:ev AS jsonb))
                    ON CONFLICT (work_id, signal_code) DO UPDATE SET
                        score = EXCLUDED.score, weight = EXCLUDED.weight,
                        available = EXCLUDED.available, explanation = EXCLUDED.explanation,
                        evidence = EXCLUDED.evidence, updated_at = NOW()
                """), {
                    "wid": row[0], "sc": sig["signal_code"], "sn": sig["signal_name"],
                    "score": sig.get("score"), "w": sig["weight"], "avail": sig["available"],
                    "expl": sig.get("explanation"), "ev": evidence_json,
                })

            if composite > 70:
                evidence_obj = {"composite_risk": composite, "priority": priority}
                db.execute(text("""
                    INSERT INTO anomalies (work_id, anomaly_type, severity, description, evidence)
                    VALUES (:wid, 'HIGH_RISK', 'CRITICAL', :desc, CAST(:ev AS jsonb))
                """), {
                    "wid": row[0],
                    "desc": f"Work flagged with composite risk {composite}/100. Priority {priority}.",
                    "ev": json.dumps(evidence_obj),
                })

            stored += 1
            _audit_status["works_processed"] = stored

            if stored % 200 == 0:
                db.commit()
                print(f"  {stored}/{total} ({stored*100//total}%)", flush=True)

        db.commit()
        _audit_status["last_run"] = datetime.now().isoformat()
        print(f"Audit complete: {stored}/{total} works processed.", flush=True)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"AUDIT FAILED: {e}", flush=True)
    finally:
        _audit_status["running"] = False
        try:
            db.close()
        except:
            pass


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 88111
    run_audit(limit)
