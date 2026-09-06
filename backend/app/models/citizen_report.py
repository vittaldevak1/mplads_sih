from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from ..database import Base

class CitizenReport(Base):
    __tablename__ = "citizen_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    work_id = Column(String(150))
    complaint_text = Column(Text)
    photo_url = Column(String(500))
    reporter_name = Column(String(200))
    reporter_contact = Column(String(100))
    status = Column(String(50), default='pending')
    created_at = Column(DateTime, server_default=func.now())
