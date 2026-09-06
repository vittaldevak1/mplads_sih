from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date
from sqlalchemy.sql import func
from ..database import Base

class Expenditure(Base):
    __tablename__ = "expenditures"
    
    id = Column(Integer, primary_key=True, index=True)
    work_id = Column(String(150), index=True)
    expenditure_date = Column(Date)
    vendor_name = Column(String(300))
    payment_status = Column(String(100))
    fund_disbursed_amount = Column(Numeric(15, 2))
    mp_name = Column(String(300))
    state = Column(String(100))
    ida = Column(String(300))
    created_at = Column(DateTime, server_default=func.now())
