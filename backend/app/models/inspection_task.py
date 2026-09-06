from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from ..database import Base

class InspectionTask(Base):
    __tablename__ = "inspection_tasks"

    id = Column(Integer, primary_key=True, index=True)
    work_id = Column(String(150), ForeignKey("works.work_id"), index=True)
    status = Column(String(20), default="pending", index=True)
    assigned_to = Column(String(200))
    assigned_at = Column(DateTime)
    notes = Column(Text)
    priority_override = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
