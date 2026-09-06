from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.sql import func
from ..database import Base

class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_name = Column(String(300), unique=True, nullable=False)
    total_works = Column(Integer, default=0)
    total_expenditure = Column(Numeric(15, 2), default=0)
    created_at = Column(DateTime, server_default=func.now())
