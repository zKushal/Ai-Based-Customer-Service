import app.models  # Load models

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db
from app.services import chat_service
from app.api.conversations import router as conversations_router
from app.api.auth import router as auth_router
from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.core.security import hash_password

app = FastAPI(title="HimalayaData AI Customer Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the inbox router
app.include_router(conversations_router) 
app.include_router(auth_router) 

@app.on_event("startup")
def seed_default_users():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.id == 1).first():
            db.add(User(
                id=1,
                name="Default Customer",
                email="customer@example.com",
                password=hash_password("password"),
                role="customer",
            ))
        if not db.query(User).filter(User.id == 2).first():
            db.add(User(
                id=2,
                name="Default Agent",
                email="agent@example.com",
                password=hash_password("password"),
                role="agent",
            ))
        db.commit()
    finally:
        db.close()

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None

@app.get("/")
def read_root():
    return {"message": "HimalayaData AI Customer Service is running!"}

@app.post("/chat")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    result = chat_service.process_chat_message(
        message_text=request.message, 
        conversation_id=request.conversation_id, 
        db=db
    )
    return result