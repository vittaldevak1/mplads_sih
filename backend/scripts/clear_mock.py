"""Clear all mock data and re-run with real AI inference."""
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Count before
    r = db.execute(text("SELECT count(*) FROM risk_scores"))
    print(f"Before: {r.scalar()} risk_scores")
    r = db.execute(text("SELECT count(*) FROM risk_signals"))
    print(f"Before: {r.scalar()} risk_signals")
    r = db.execute(text("SELECT count(*) FROM anomalies"))
    print(f"Before: {r.scalar()} anomalies")

    # Clear all mock/old data
    db.execute(text("DELETE FROM anomalies"))
    db.execute(text("DELETE FROM risk_signals"))
    db.execute(text("DELETE FROM risk_scores"))
    db.commit()

    # Count after
    r = db.execute(text("SELECT count(*) FROM risk_scores"))
    print(f"\nAfter clear: {r.scalar()} risk_scores")
    r = db.execute(text("SELECT count(*) FROM risk_signals"))
    print(f"After clear: {r.scalar()} risk_signals")
    r = db.execute(text("SELECT count(*) FROM anomalies"))
    print(f"After clear: {r.scalar()} anomalies")

    print("\nAll mock data cleared. Ready for full real inference audit.")
finally:
    db.close()
