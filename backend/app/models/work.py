from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric, DateTime, Date
from sqlalchemy.sql import func
from ..database import Base

class Work(Base):
    __tablename__ = "works"
    
    id = Column(Integer, primary_key=True, index=True)
    work_id = Column(String(150), unique=True, nullable=False, index=True)
    work_id_raw = Column(Text)
    work_title = Column(String(500))
    work_category = Column(String(100))
    work_description = Column(Text)
    state = Column(String(100))
    ida = Column(String(300))
    constituency = Column(String(100))
    parliament_house = Column(String(20), nullable=False)
    source_file = Column(String(200))
    has_image_proof = Column(Boolean, default=False)
    is_sc_quota = Column(Boolean, default=False)
    is_st_quota = Column(Boolean, default=False)
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))
    citizen_complaint_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
