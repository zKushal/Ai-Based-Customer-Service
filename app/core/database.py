from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create the database engine
engine = create_engine(settings.DATABASE_URL)

# Create the SessionLocal class that embedder.py is trying to import
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)