from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date
from sqlalchemy.sql import func
from ..database import Base

class WorkRecommendation(Base):
    __tablename__ = "work_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    work_id = Column(String(150), index=True)
    mp_name = Column(String(300))
    recommended_date = Column(Date)
    recommended_amount = Column(Numeric(15, 2))
    created_at = Column(DateTime, server_default=func.now())
