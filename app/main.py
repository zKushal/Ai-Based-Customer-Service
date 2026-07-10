from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db
from app.services import chat_service

app = FastAPI(title="HimalayaData AI Customer Service")

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