from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from ..database import Base

class IngestionLog(Base):
    __tablename__ = "ingestion_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(200))
    dataset_type = Column(String(100))
    parliament_house = Column(String(20))
    rows_read = Column(Integer)
    rows_inserted = Column(Integer)
    rows_skipped = Column(Integer)
    errors = Column(JSONB)
    warnings = Column(JSONB)
    ingested_at = Column(DateTime, server_default=func.now())
