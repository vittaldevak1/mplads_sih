from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.sql import func
from ..database import Base

class MPAllocation(Base):
    __tablename__ = "mp_allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    mp_name = Column(String(300))
    state = Column(String(100))
    constituency = Column(String(100))
    parliament_house = Column(String(20), nullable=False)
    allocated_amount = Column(Numeric(15, 2))
    elected_nominated = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
