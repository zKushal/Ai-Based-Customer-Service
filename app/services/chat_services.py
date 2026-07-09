from sqlalchemy.orm import Session
from langchain_groq import ChatGroq

from app.models.conversation import Conversation, Message
from app.models.user import User  # noqa: F401 - registers users table for FK resolution
from app.models.prompt import PromptTemplate
from app.api.rag import retrieve_context
from app.core.config import settings

llm = ChatGroq(model="llama-3.1-8b-instant", api_key=settings.GROQ_API_KEY)


def process_chat_message(message_text: str, db: Session):
    dummy_user_id = 1

    new_conversation = Conversation(user_id=dummy_user_id, status="open")
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)

    user_msg = Message(
        conversation_id=new_conversation.id,
        sender_id=dummy_user_id,
        sender_type="customer",
        content=message_text,
    )
    db.add(user_msg)
    db.commit()

    context = retrieve_context(message_text)

    prompt_record = db.query(PromptTemplate).filter(PromptTemplate.id == 1).first()
    system_prompt = prompt_record.prompt_text if prompt_record else "You are a helpful assistant."

    final_prompt = (
        f"{system_prompt}\n\nCONTEXT:\n{context}\n\nCUSTOMER:\n{message_text}\n\nAI:"
    )

    try:
        response = llm.invoke(final_prompt)
        ai_reply = response.content
    except Exception:
        ai_reply = "I am currently unable to process your request due to a technical issue."

    ai_msg = Message(
        conversation_id=new_conversation.id,
        sender_id=None,
        sender_type="ai",
        content=ai_reply,
    )
    db.add(ai_msg)
    db.commit()

    return {
        "conversation_id": new_conversation.id,
        "reply": ai_reply,
    }
