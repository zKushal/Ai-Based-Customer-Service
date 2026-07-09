from sqlalchemy import Column, Integer, Text
from app.core.database import Base

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    prompt_text = Column(Text, nullable=False)