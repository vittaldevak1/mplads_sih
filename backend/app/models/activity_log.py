from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from ..database import Base

class ActivityLog(Base):
    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True, index=True)
    work_id = Column(String(150), index=True)
    action = Column(String(100), nullable=False)
    actor = Column(String(200))
    details = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
