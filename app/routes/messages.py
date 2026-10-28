import uuid
from fastapi import APIRouter, HTTPException, Request, Query
from typing import List, Dict, Any

from ..models import Conversation, DirectMessage, SendMessageRequest
from ..database import db
from ..telemetry import telemetry
from .auth import CURRENT_ACTIVE_USER

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.get("", response_model=List[Conversation])
async def list_conversations(request: Request):
    """List private direct message conversations for the logged in user."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    trace_id = f"trc_dm_list_{uuid.uuid4().hex[:10]}"

    convs = db.get_user_conversations(CURRENT_ACTIVE_USER)

    telemetry.emit(
        event_type="http.request",
        attributes={
            "method": "GET",
            "endpoint": "/api/messages",
            "user": CURRENT_ACTIVE_USER,
            "conversations_returned": len(convs),
            "client_ip": client_ip,
        },
        source_resource=f"user:{CURRENT_ACTIVE_USER}",
        target_resource="/api/messages",
        trace_id=trace_id,
        severity="info",
    )
    return convs


@router.get("/{conv_id}", response_model=Conversation)
async def get_conversation_messages(
    conv_id: str,
    request: Request,
    exploit_bola: bool = Query(False, description="Simulate BOLA/IDOR vulnerability bypass")
):
    """
    Fetch messages in a conversation.
    Demonstrates Broken Object Level Authorization (BOLA / IDOR):
    If exploit_bola is True, unauthorized users can read private executive threads!
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    trace_id = f"trc_dm_read_{uuid.uuid4().hex[:10]}"

    try:
        conv = db.get_conversation(conv_id, requester_username=CURRENT_ACTIVE_USER, bypass_auth=exploit_bola)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Check if unauthorized access occurred
        is_unauthorized = CURRENT_ACTIVE_USER not in conv.participants

        if is_unauthorized:
            # Emit high-severity security alert for BOLA/IDOR data exfiltration
            telemetry.emit(
                event_type="security.alert",
                attributes={
                    "alert_type": "BOLA_IDOR_VIOLATION",
                    "conv_id": conv_id,
                    "target_participants": conv.participants,
                    "attacker_user": CURRENT_ACTIVE_USER,
                    "client_ip": client_ip,
                    "sensitive_records_exposed": len(conv.messages),
                },
                source_resource=f"user:{CURRENT_ACTIVE_USER}",
                target_resource=f"conversation:{conv_id}",
                trace_id=trace_id,
                severity="critical",
            )

        telemetry.emit(
            event_type="http.request",
            attributes={
                "method": "GET",
                "endpoint": f"/api/messages/{conv_id}",
                "user": CURRENT_ACTIVE_USER,
                "is_unauthorized_bola": is_unauthorized,
                "status_code": 200,
                "client_ip": client_ip,
            },
            source_resource=f"user:{CURRENT_ACTIVE_USER}",
            target_resource=f"conversation:{conv_id}",
            trace_id=trace_id,
            severity="warning" if is_unauthorized else "info",
        )

        return conv

    except PermissionError as pe:
        # Access blocked by proper authorization check
        telemetry.emit(
            event_type="http.request",
            attributes={
                "method": "GET",
                "endpoint": f"/api/messages/{conv_id}",
                "user": CURRENT_ACTIVE_USER,
                "status_code": 403,
                "denied_reason": str(pe),
                "client_ip": client_ip,
            },
            source_resource=f"user:{CURRENT_ACTIVE_USER}",
            target_resource=f"conversation:{conv_id}",
            trace_id=trace_id,
            severity="warning",
        )
        raise HTTPException(status_code=403, detail=str(pe))


@router.post("", response_model=DirectMessage)
async def send_direct_message(req: SendMessageRequest, request: Request):
    """Send a new direct message."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    trace_id = f"trc_dm_send_{uuid.uuid4().hex[:10]}"

    dm = db.send_direct_message(
        sender=CURRENT_ACTIVE_USER,
        recipient=req.recipient,
        text=req.text,
    )

    telemetry.emit(
        event_type="http.request",
        attributes={
            "method": "POST",
            "endpoint": "/api/messages",
            "sender": CURRENT_ACTIVE_USER,
            "recipient": req.recipient,
            "is_sensitive": dm.is_sensitive,
        },
        source_resource=f"user:{CURRENT_ACTIVE_USER}",
        target_resource=f"user:{req.recipient}",
        trace_id=trace_id,
        severity="info",
    )

    return dm

