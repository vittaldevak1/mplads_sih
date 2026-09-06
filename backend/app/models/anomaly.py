from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from ..database import Base

class Anomaly(Base):
    __tablename__ = "anomalies"
    
    id = Column(Integer, primary_key=True, index=True)
    work_id = Column(String(150), index=True)
    anomaly_type = Column(String(50), nullable=False)
    severity = Column(String(20))
    description = Column(Text)
    evidence = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now())
