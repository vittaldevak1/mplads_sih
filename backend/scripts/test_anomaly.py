import hashlib
import random
from app.database import SessionLocal
from app.models.work import Work
from app.models.risk_score import RiskScore
from app.models.risk_signal import RiskSignal
from app.models.anomaly import Anomaly
from app.ai.interfaces.contract import SIGNAL_DEFINITIONS

db = SessionLocal()
works = db.query(Work).order_by(Work.id).limit(100).all()
stored = 0
anomalies_added = 0
for work in works:
    seed = int(hashlib.md5(work.work_id.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    composite = round(rng.uniform(5, 95), 1)
    if composite > 70:
        priority = "CRITICAL"
    elif composite > 50:
        priority = "HIGH"
    elif composite > 25:
        priority = "MEDIUM"
    else:
        priority = "LOW"
    risk_score = RiskScore(
        work_id=work.work_id,
        composite_risk=composite,
        confidence_coverage=round(rng.uniform(0.4, 0.95), 4),
        inspection_priority=priority,
    )
    db.merge(risk_score)
    for defn in SIGNAL_DEFINITIONS:
        available = rng.random() > 0.25
        score = round(rng.uniform(0, 100), 1) if available else None
        signal = RiskSignal(
            work_id=work.work_id,
            signal_code=defn["code"],
            signal_name=defn["name"],
            version="1.0",
            score=score,
            weight=defn["weight"],
            available=available,
            evidence=None,
            explanation="Signal active for this work" if available else None,
        )
        db.merge(signal)
    if composite > 70:
        anomaly = Anomaly(
            work_id=work.work_id,
            anomaly_type="HIGH_RISK",
            severity="CRITICAL",
            description=f"Work flagged with composite risk {composite}/100. Priority {priority}.",
            evidence={"composite_risk": composite, "priority": priority},
        )
        db.add(anomaly)
        anomalies_added += 1
    stored += 1
    if stored % 500 == 0:
        db.commit()
db.commit()
anomaly_count = db.query(Anomaly).count()
print(f"Processed {stored}, anomalies this run: {anomalies_added}, total anomalies: {anomaly_count}")
db.close()
