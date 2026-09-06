from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date
from sqlalchemy.sql import func
from ..database import Base

class CalamityConsent(Base):
    __tablename__ = "calamity_consents"
    
    id = Column(Integer, primary_key=True, index=True)
    calamity_type = Column(String(100))
    calamity_name = Column(String(300))
    mp_name = Column(String(300))
    consent_date = Column(Date)
    consent_amount = Column(Numeric(15, 2))
    parliament_house = Column(String(20), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
