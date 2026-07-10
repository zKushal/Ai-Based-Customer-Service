from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from langchain_groq import ChatGroq
from app.models.conversation import Conversation, Message
from app.models.escalation import Escalation
from app.models.prompt import PromptTemplate
from app.api.rag import retrieve_context
from app.core.config import settings

llm = ChatGroq(model="llama-3.1-8b-instant", api_key=settings.GROQ_API_KEY)


class MessageIntent(BaseModel):
    """AI-derived customer message intent — no keyword lists."""

    priority: Literal["low", "medium", "high"] = Field(
        description="low for normal messages; medium for problems needing help; high for urgent/critical issues."
    )
    requires_secure_data: bool = Field(
        description=(
            "True when the customer wants THEIR private account data that only a verified human can provide "
            "(account number, bank balance, password, OTP, transaction history, billing details, etc.). "
            "False for general company/policy questions answerable from the public knowledge base."
        )
    )
    is_general_greeting: bool = Field(
        description=(
            "True for greetings or small talk only (hi, hello, thanks, bye, good morning) "
            "with no real support question. False when they ask something substantive."
        )
    )


def classify_message_intent(message_text: str) -> MessageIntent:
    """Use Groq to infer greeting vs secure vs normal intent from meaning, not fixed word lists."""
    classifier = llm.with_structured_output(MessageIntent)
    return classifier.invoke(
        [
            {
                "role": "system",
                "content": (
                    "You classify customer-support messages for HimalayaData Solutions.\n"
                    "The knowledge base only has general company documentation — NOT individual customer accounts.\n\n"
                    "Rules:\n"
                    "- is_general_greeting: true for 'Hi', 'Hello', 'Thanks', 'Bye', etc. when there is no real question.\n"
                    "- requires_secure_data: true when they ask for personal account info (account number, bank balance, "
                    "password, login, OTP, their transactions) even if similar words appear in company docs.\n"
                    "- requires_secure_data: false for general questions about company services, policies, or locations.\n"
                    "- priority: high if urgent/angry/critical outage; medium for problems; low otherwise."
                ),
            },
            {"role": "user", "content": message_text},
        ]
    )

def process_chat_message(message_text: str, conversation_id: int = None, db: Session = None):
    DUMMY_USER_ID = 1
    DUMMY_AGENT_ID = 2 

    # 1. Get or Create Conversation
    if conversation_id:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            return {"error": "Conversation not found"}
    else:
        conversation = Conversation(user_id=DUMMY_USER_ID, status="open")
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # 2. Save Customer's new message
    user_msg = Message(
        conversation_id=conversation.id,
        sender_id=DUMMY_USER_ID,
        sender_type="customer",
        content=message_text
    )
    db.add(user_msg)
    db.commit()

    # ====================================================================
    # FEATURE 1: AI-DRIVEN INTENT & SECURITY CLASSIFIER
    # ====================================================================
    analysis = MessageIntent(priority="low", requires_secure_data=False, is_general_greeting=False)

    try:
        analysis = classify_message_intent(message_text)
        conversation.priority = analysis.priority
        db.commit()

        if analysis.requires_secure_data:
            return handle_escalation(
                conversation,
                DUMMY_AGENT_ID,
                db,
                "User requested private/secure information that AI cannot access.",
            )
    except Exception:
        # Classifier unavailable — safe defaults; RAG step still handles unknown topics.
        pass

    # 3. Get RAG Context AND Score
    context, score = retrieve_context(message_text)

    # Escalate if it's a real question but NOT in the PDF
    if not analysis.is_general_greeting and (not context or context.strip() == "" or score < 0.35):
        return handle_escalation(conversation, DUMMY_AGENT_ID, db, f"Question not found in knowledge base: {message_text}")

    # 4. Get System Prompt
    prompt_record = db.query(PromptTemplate).filter(PromptTemplate.id == 1).first()
    system_prompt = prompt_record.prompt_text if prompt_record else "You are a helpful assistant."

    # 5. Build Message History for the AI
    history_messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at.asc()).all()

    formatted_history = []
    for msg in history_messages:
        if msg.sender_type == "customer":
            formatted_history.append({"role": "user", "content": msg.content})
        elif msg.sender_type == "ai":
            formatted_history.append({"role": "assistant", "content": msg.content})

    # 6. Construct the final payload for Groq
    messages_for_llm = [
        {"role": "system", "content": f"{system_prompt}\n\nCONTEXT FROM KNOWLEDGE BASE:\n{context}"}
    ]
    messages_for_llm.extend(formatted_history)

    # 7. Ask Groq for the final customer reply
    try:
        response = llm.invoke(messages_for_llm)
        ai_reply = response.content
    except Exception as e:
        ai_reply = f"I am currently unable to process your request due to a technical issue: {str(e)}"

    # 8. Save AI's response
    ai_msg = Message(
        conversation_id=conversation.id,
        sender_id=None, 
        sender_type="ai",
        content=ai_reply
    )
    db.add(ai_msg)
    db.commit()

    return {
        "conversation_id": conversation.id, 
        "reply": ai_reply
    }


# Helper function to keep code clean
def handle_escalation(conversation, agent_id, db, reason):
    conversation.status = "pending"
    
    escalation = Escalation(
        conversation_id=conversation.id,
        assigned_agent_id=agent_id,
        reason=reason,
        priority=conversation.priority
    )
    db.add(escalation)
    
    handoff_msg = Message(
        conversation_id=conversation.id,
        sender_id=None,
        sender_type="ai",
        content="I apologize, but I do not have the specific information required to answer your question. I am escalating this to a human support agent who will assist you shortly."
    )
    db.add(handoff_msg)
    db.commit()

    return {
        "conversation_id": conversation.id,
        "reply": handoff_msg.content,
        "escalated": True
    }