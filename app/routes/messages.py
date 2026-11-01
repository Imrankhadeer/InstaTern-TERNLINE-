from typing import List
from fastapi import APIRouter, HTTPException, Depends
from ..models import Conversation, DirectMessage, SendMessageRequest, User
from ..database import db
from .auth import get_current_user

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.get("", response_model=List[Conversation])
async def list_conversations(current_user: User = Depends(get_current_user)):
    """List direct message conversations for the logged in user."""
    return db.get_user_conversations(current_user.username)


@router.get("/{conv_id}", response_model=Conversation)
async def get_conversation(conv_id: str, current_user: User = Depends(get_current_user)):
    """Fetch all messages within a conversation if the user is a participant."""
    convs = db.get_user_conversations(current_user.username)
    target = next((c for c in convs if c.id == conv_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied")
    return target


@router.post("", response_model=DirectMessage)
async def send_direct_message(
    req: SendMessageRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a direct message to another user."""
    recipient = req.recipient.strip().lower()
    if recipient == current_user.username:
        raise HTTPException(status_code=400, detail="Cannot message yourself")

    recipient_user = db.get_user_by_username(recipient)
    if not recipient_user:
        raise HTTPException(status_code=404, detail="Recipient user not found")

    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Message text cannot be empty")

    return db.send_message(
        sender=current_user.username,
        recipient=recipient,
        text=req.text.strip()
    )
