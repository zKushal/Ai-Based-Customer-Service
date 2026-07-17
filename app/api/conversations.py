from fastapi import HTTPException
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.api.deps import get_db, get_current_agent
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.escalation import Escalation

router = APIRouter(prefix="/conversations", tags=["Conversations"])


# -------------------------------------------------------------------------------
# 1. View Assigned Escalations (Specific route MUST be before generic "/")
# -------------------------------------------------------------------------------
@router.get("/escalations/assigned")
def get_assigned_escalations(
    status: str = Query(None, description="Filter by: pending, assigned, in_progress, resolved"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_agent)
):
    """
    Returns all tickets assigned to the logged-in human agent.
    (For now, hardcoded to agent_id=2).
    """
    ASSIGNED_AGENT_ID = current_user.id

    query = db.query(Escalation).filter(Escalation.assigned_agent_id == ASSIGNED_AGENT_ID)
    
    if status:
        query = query.filter(Escalation.status == status)
        
    escalations = query.order_by(Escalation.escalated_at.desc()).all()

    ticket_list = []
    for ticket in escalations:
        ticket_list.append({
            "escalation_id": ticket.id,
            "conversation_id": ticket.conversation_id,
            "reason": ticket.reason,
            "priority": ticket.priority,
            "status": ticket.status,
            "escalated_at": ticket.escalated_at
        })

    return {"assigned_tickets": ticket_list}


# -------------------------------------------------------------------------------
# 2. Z-ai Style Inbox (View, Search, Filter)
# -------------------------------------------------------------------------------
@router.get("/")
def get_conversations(
    status: str = Query(None, description="Filter by status: open, pending, resolved"),
    priority: str = Query(None, description="Filter by priority: low, medium, high"),
    search: str = Query(None, description="Search in message content or conversation summary"),
    db: Session = Depends(get_db)
):
    """
    Get a list of conversations.
    Can filter by status/priority, and search within message text.
    """
    query = db.query(Conversation).order_by(Conversation.updated_at.desc())

    if status:
        query = query.filter(Conversation.status == status)
    if priority:
        query = query.filter(Conversation.priority == priority)

    if search:
        query = query.outerjoin(Message, Conversation.id == Message.conversation_id)
        query = query.filter(
            or_(
                Conversation.summary.ilike(f"%{search}%"),
                Message.content.ilike(f"%{search}%")
            )
        ).distinct()

    conversations = query.all()
    
    inbox_list = []
    for conv in conversations:
        # Get the first message from the customer to use as a fallback title
        first_user_msg = db.query(Message).filter(
            Message.conversation_id == conv.id,
            Message.sender_type == "customer"
        ).order_by(Message.created_at.asc()).first()

        last_message = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.created_at.desc()).first()

        # Determine the best summary for the UI
        final_summary = conv.summary
        if not final_summary or final_summary.strip() == "" or "no content" in final_summary.strip().lower():
            if first_user_msg:
                final_summary = first_user_msg.content[:35] + "..."
            else:
                final_summary = f"Conversation {conv.id}"

        inbox_list.append({
            "id": conv.id,
            "status": conv.status,
            "priority": conv.priority,
            "summary": final_summary,
            "last_message_preview": last_message.content[:100] if last_message else None,
            "last_message_at": last_message.created_at if last_message else conv.updated_at,
            "created_at": conv.created_at
        })

    return {"conversations": inbox_list}


# -------------------------------------------------------------------------------
# 3. View Full Chat History
# -------------------------------------------------------------------------------
@router.get("/{conversation_id}/messages")
def get_chat_history(conversation_id: int, db: Session = Depends(get_db)):
    """
    Fetch all messages for a specific conversation.
    Used when an agent clicks on a chat in the inbox.
    """
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        return {"error": "Conversation not found"}

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).all()

    chat_history = []
    for msg in messages:
        chat_history.append({
            "id": msg.id,
            "sender_type": msg.sender_type,
            "content": msg.content,
            "created_at": msg.created_at
        })

    return {
        "conversation_id": conversation_id,
        "status": conversation.status,
        "priority": conversation.priority,
        "messages": chat_history
    }


# -------------------------------------------------------------------------------
# 4. Update Ticket Status (Resolve, Reopen, etc.)
# -------------------------------------------------------------------------------
@router.put("/{conversation_id}/status")
def update_conversation_status(
    conversation_id: int, 
    status: str = Query(..., description="New status: open, pending, resolved"),
    db: Session = Depends(get_db)
):
    """
    Allows a human agent to update the status of a ticket (e.g., mark as resolved).
    """
    if status not in ["open", "pending", "resolved"]:
        return {"error": "Invalid status. Must be 'open', 'pending', or 'resolved'."}

    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        return {"error": "Conversation not found"}

    conversation.status = status
    db.commit()

    return {
        "message": f"Conversation {conversation_id} updated to '{status}' successfully."
    }


# -------------------------------------------------------------------------------
# 5. Human Agent Reply
# -------------------------------------------------------------------------------
class AgentReplyRequest(BaseModel):
    message: str

@router.post("/{conversation_id}/agent-reply")
def agent_reply(
    conversation_id: int, 
    request: AgentReplyRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_agent)
):
    """
    Allows a human agent to send a message in an existing conversation.
    """
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        return {"error": "Conversation not found"}

    query = db.query(Escalation).filter(Escalation.assigned_agent_id == current_user.id)
    escalation = query.filter(Escalation.conversation_id == conversation_id).first()
    if not escalation:
        return {"error": "Escalation not found"}
    
    agent_msg = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        sender_type="agent",
        content=request.message
    )
    db.add(agent_msg)

    # Automatically update escalation status to 'in_progress'
    escalation = db.query(Escalation).filter(
        Escalation.conversation_id == conversation_id,
        Escalation.status == "pending"
    ).first()
    
    if escalation:
        escalation.status = "in_progress"

    db.commit()

    return {
        "message": "Agent reply sent successfully.",
        "sender_type": "agent"
    }

# -------------------------------------------------------------------------------
# DELETE All Conversations
# -------------------------------------------------------------------------------
@router.delete("/all")
def delete_all_conversations(db: Session = Depends(get_db)):
    """
    Deletes ALL conversations and their messages from the database.
    """
    db.query(Message).delete()
    db.query(Conversation).delete()
    db.commit()
    return {"status": "success", "message": "All conversations deleted."}

# -------------------------------------------------------------------------------
# DELETE Conversation
# -------------------------------------------------------------------------------
@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """
    Deletes a conversation and all of its messages from the database.
    """
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    db.delete(conversation)
    db.commit()
    return {"status": "success", "message": f"Conversation {conversation_id} deleted."}