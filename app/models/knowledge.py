from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    source_title = Column(String(255), nullable=True)
    chunk_text = Column(Text, nullable=False)
    
    # Automatically handles the NOW() defaults from your SQL schema
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())