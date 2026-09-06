from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date
from sqlalchemy.sql import func
from ..database import Base

class WorkCompletion(Base):
    __tablename__ = "work_completions"
    
    id = Column(Integer, primary_key=True, index=True)
    work_id = Column(String(150), index=True)
    completion_date = Column(Date)
    amount_disbursed = Column(Numeric(15, 2))
    image_status = Column(String(50))
    elected_nominated = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
