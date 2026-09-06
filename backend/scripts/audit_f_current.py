import sys; sys.stdout.reconfigure(encoding='utf-8'); sys.path.insert(0, r'C:\Users\alway\Downloads\sih\mplads_sih\backend')
from sqlalchemy import text
from app.database import SessionLocal
from app.ai.engine import get_predictor

db = SessionLocal()
predictor = get_predictor()

# Test current pipeline with disbursed=None
test_cases = [
    {"work_id": "TEST1", "work_title": "Test", "work_description": "Test road construction",
     "category": "Normal/Others", "State": "Karnataka", "constituency": "TEST",
     "is_sc_quota": False, "is_st_quota": False,
     "sanction_amount": 500000.0, "disbursed_amount": None,
     "vendor_name": "", "recommended_date": None, "sanction_date": None, "completion_date": None},
    {"work_id": "TEST2", "work_title": "Test", "work_description": "Test road construction",
     "category": "Normal/Others", "State": "Karnataka", "constituency": "TEST",
     "is_sc_quota": False, "is_st_quota": False,
     "sanction_amount": 500000.0, "disbursed_amount": 500000.0,
     "vendor_name": "", "recommended_date": None, "sanction_date": None, "completion_date": None},
]

for tc in test_cases:
    result = predictor.predict_new_work(tc)
    f_sig = [s for s in result["signals"] if s["signal_code"] == "F"][0]
    print(f"\nWork: {tc['work_id']}")
    print(f"  sanction={tc['sanction_amount']}  disbursed={tc['disbursed_amount']}")
    print(f"  F available: {f_sig['available']}  score: {f_sig['score']}")
    print(f"  F explanation: {f_sig['explanation']}")
    print(f"  F evidence: {f_sig['evidence']}")

db.close()
