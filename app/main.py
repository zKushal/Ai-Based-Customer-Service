from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services import chat_service

app = FastAPI(title="HimalayaData AI Customer Service")


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def read_root():
    return {"message": "HimalayaData AI Customer Service is running!"}


@app.post("/chat")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    return chat_service.process_chat_message(
        message_text=request.message,
        db=db,
    )
