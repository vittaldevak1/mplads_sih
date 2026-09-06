from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text
from sqlalchemy.sql import func
from ..database import Base

class RiskScore(Base):
    __tablename__ = "risk_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    work_id = Column(String(150), unique=True, index=True)
    composite_risk = Column(Numeric(5, 2))
    confidence_coverage = Column(Numeric(5, 4))
    inspection_priority = Column(String(20))
    recommended_action = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
