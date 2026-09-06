from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date
from sqlalchemy.sql import func
from ..database import Base

class WorkSanction(Base):
    __tablename__ = "work_sanctions"
    
    id = Column(Integer, primary_key=True, index=True)
    work_id = Column(String(150), index=True)
    sanction_date = Column(Date)
    sanction_amount = Column(Numeric(15, 2))
    work_status = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
