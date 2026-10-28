import uuid
from fastapi import APIRouter, HTTPException, Request, Query
from typing import Dict, Any, List

from ..database import db
from ..telemetry import telemetry
from .auth import CURRENT_ACTIVE_USER

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/metrics")
async def get_system_metrics(request: Request):
    """Returns application health and operational statistics."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    trace_id = f"trc_admin_metrics_{uuid.uuid4().hex[:10]}"

    metrics = db.get_metrics()

    telemetry.emit(
        event_type="http.request",
        attributes={
            "method": "GET",
            "endpoint": "/api/admin/metrics",
            "user": CURRENT_ACTIVE_USER,
            "status_code": 200,
        },
        source_resource=f"ip:{client_ip}",
        target_resource="/api/admin/metrics",
        trace_id=trace_id,
        severity="info",
    )
    return metrics


@router.get("/dump-users")
async def dump_users(
    request: Request,
    bypass_role_check: bool = Query(False, description="Simulate privilege escalation / broken access control")
):
    """
    Simulates privileged database extraction.
    Only accessible by users with role='admin' (e.g. charlie_vip).
    If bypass_role_check is True, simulates broken access control privilege escalation!
    """
    user = db.users.get(CURRENT_ACTIVE_USER)
    client_ip = request.client.host if request.client else "127.0.0.1"
    trace_id = f"trc_admin_dump_{uuid.uuid4().hex[:10]}"

    is_admin = user and user.role == "admin"

    if not is_admin and not bypass_role_check:
        telemetry.emit(
            event_type="security.alert",
            attributes={
                "alert_type": "UNAUTHORIZED_ADMIN_ACCESS",
                "endpoint": "/api/admin/dump-users",
                "requester": CURRENT_ACTIVE_USER,
                "role": user.role if user else "anonymous",
                "client_ip": client_ip,
                "status_code": 403,
            },
            source_resource=f"user:{CURRENT_ACTIVE_USER}",
            target_resource="/api/admin/dump-users",
            trace_id=trace_id,
            severity="warning",
        )
        raise HTTPException(status_code=403, detail="Forbidden: Admin role required for credential dump")

    # Privileged data exfiltration occurred -> emit db.bulk_query
    telemetry.emit(
        event_type="db.bulk_query",
        attributes={
            "table": "users",
            "operation": "SELECT_ALL_CREDENTIALS",
            "rows_affected": len(db.users),
            "columns": ["id", "username", "password_hash", "session_tokens"],
            "is_privileged_dump": True,
            "requester": CURRENT_ACTIVE_USER,
            "escalated_privilege": not is_admin and bypass_role_check,
        },
        source_resource=f"user:{CURRENT_ACTIVE_USER}",
        target_resource="table:users",
        trace_id=trace_id,
        severity="critical",
    )

    return {
        "status": "success",
        "warning": "Sensitive user credential dump retrieved!",
        "records_count": len(db.users),
        "data": db.admin_dump_users(),
    }

