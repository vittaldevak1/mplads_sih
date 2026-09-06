from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from ..database import Base

class RiskSignal(Base):
    __tablename__ = "risk_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    work_id = Column(String(150), index=True)
    signal_code = Column(String(5), nullable=False)
    signal_name = Column(String(100), nullable=False)
    version = Column(String(50))
    score = Column(Numeric(5, 2))
    weight = Column(Numeric(5, 2), nullable=False)
    available = Column(Boolean, default=False)
    evidence = Column(JSONB)
    explanation = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        {'unique_together': ('work_id', 'signal_code')},
    )
