from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from ..database import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    work_id = Column(String(150))
    document_type = Column(String(100))
    file_name = Column(String(300))
    file_path = Column(String(500))
    uploaded_at = Column(DateTime, server_default=func.now())
