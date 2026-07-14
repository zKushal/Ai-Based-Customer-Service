import app.models  # Load models

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db
from app.services import chat_service
from app.api.conversations import router as conversations_router
from app.api.auth import router as auth_router

app = FastAPI(title="HimalayaData AI Customer Service")

# Include the inbox router
app.include_router(conversations_router) 
app.include_router(auth_router) 

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