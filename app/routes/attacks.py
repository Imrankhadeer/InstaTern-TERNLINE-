import uuid
import time
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from ..telemetry import telemetry
from ..config import settings
from ..database import db

router = APIRouter(prefix="/api/attacks", tags=["attacks"])


class BruteForceRequest(BaseModel):
    target_username: str = "charlie_vip"
    attempts: int = Field(default=6, ge=1, le=20)


class CrossServiceExfilRequest(BaseModel):
    attacker_ip: str = "198.51.100.42"
    target_table: str = "users"
    rows_affected: int = 1200


@router.get("/status")
async def get_telemetry_status():
    """Returns connectivity and configuration status for Cyber Engine."""
    conn = await telemetry.check_connection()
    return {
        "cyber_engine_url": settings.cyber_engine_url,
        "app_id": settings.app_id,
        "service_id": settings.service_id,
        "tenant_id": settings.tenant_id,
        "telemetry_enabled": settings.telemetry_enabled,
        "connection": conn,
    }


@router.get("/recent-telemetry")
async def get_recent_telemetry():
    """Returns recently emitted telemetry events for the live UI dock."""
    return list(telemetry.recent_events)


@router.post("/brute-force")
async def simulate_brute_force(req: BruteForceRequest):
    """
    Simulates a rapid credential stuffing / password spraying attack.
    Fires N consecutive failed login events against a victim account.
    Triggers Cyber Engine Fast Track 'BruteForceLoginDetector'.
    """
    target = req.target_username
    attacker_ip = f"203.0.113.{int(time.time()) % 250 + 1}"
    emitted = []

    for i in range(req.attempts):
        trace_id = f"trc_bf_{uuid.uuid4().hex[:10]}"
        rec = telemetry.emit(
            event_type="auth.login_failed",
            attributes={
                "username": target,
                "ip": attacker_ip,
                "attempt_index": i + 1,
                "password_tried": f"pass_guess_{i+1}!",
                "reason": "invalid_credentials",
                "user_agent": "Hydra/9.5 (Kali Linux; Automated Password Spray)",
            },
            source_resource=f"ip:{attacker_ip}",
            target_resource=f"user:{target}",
            trace_id=trace_id,
            severity="warning",
        )
        emitted.append(rec)
        time.sleep(0.05)  # Slight spacing to simulate rapid burst

    return {
        "status": "completed",
        "attack": "brute_force_login",
        "target_user": target,
        "attempts_fired": req.attempts,
        "attacker_ip": attacker_ip,
        "detector_targeted": "BruteForceLoginDetector",
        "events": emitted,
        "message": f"Successfully fired {req.attempts} failed login attempts to Cyber Engine. Check your Security Console for the new finding!",
    }


@router.post("/cross-service-exfil")
async def simulate_cross_service_exfiltration(req: CrossServiceExfilRequest):
    """
    Simulates an advanced attack spanning 3 distributed microservices:
    1. Inbound HTTP API exploit request
    2. Compromised background media worker job anomaly
    3. Mass database exfiltration from sensitive table
    Triggers Cyber Engine Fast Track 'CrossServiceExfiltrationDetector'.
    """
    shared_trace_id = f"trc_apt_{uuid.uuid4().hex[:12]}"
    emitted = []

    # Stage 1: API Gateway request with suspicious SQL injection search
    r1 = telemetry.emit(
        event_type="http.request",
        attributes={
            "method": "POST",
            "endpoint": "/api/search",
            "client_ip": req.attacker_ip,
            "user_agent": "sqlmap/1.7.2#stable",
            "status_code": 200,
        },
        source_resource=f"ip:{req.attacker_ip}",
        target_resource="/api/search",
        trace_id=shared_trace_id,
        severity="warning",
    )
    emitted.append(r1)

    # Stage 2: Anomalous worker job processing payload
    r2 = telemetry.emit(
        event_type="worker.job_anomalous",
        attributes={
            "job_type": "async_query_cache",
            "anomaly_flag": True,
            "error": "Unauthorized memory probe into internal connection pool",
        },
        source_resource="worker:async-cache",
        target_resource="worker:pool",
        trace_id=shared_trace_id,
        severity="high",
    )
    emitted.append(r2)

    # Stage 3: Large database bulk exfiltration of sensitive table
    r3 = telemetry.emit(
        event_type="db.bulk_query",
        attributes={
            "table": req.target_table,
            "rows_affected": req.rows_affected,
            "query": f"SELECT id, username, password_hash, session_token FROM {req.target_table} WHERE 1=1;",
            "is_exfiltration": True,
        },
        source_resource="service:instagram-api",
        target_resource=f"table:{req.target_table}",
        trace_id=shared_trace_id,
        severity="critical",
    )
    emitted.append(r3)

    return {
        "status": "completed",
        "attack": "cross_service_exfiltration",
        "correlated_trace_id": shared_trace_id,
        "detector_targeted": "CrossServiceExfiltrationDetector",
        "stages": ["http.request", "worker.job_anomalous", "db.bulk_query"],
        "events": emitted,
        "message": f"Fired 3-stage correlated exfiltration sequence (trace_id: {shared_trace_id}). Check Cyber Engine Overview & Findings!",
    }


@router.post("/benign-traffic")
async def simulate_benign_traffic():
    """
    Simulates normal benign social operations (browsing, liking, commenting).
    Shows continuous telemetry with 0 false positives.
    """
    trace_id = f"trc_benign_{uuid.uuid4().hex[:10]}"
    events = []

    # 1. Feed browse
    events.append(
        telemetry.emit(
            event_type="http.request",
            attributes={"method": "GET", "endpoint": "/api/feed", "status_code": 200},
            target_resource="/api/feed",
            trace_id=trace_id,
            severity="info",
        )
    )
    # 2. Post like
    events.append(
        telemetry.emit(
            event_type="http.request",
            attributes={"method": "POST", "endpoint": "/api/posts/post_1/like", "status_code": 200},
            target_resource="post:post_1",
            trace_id=trace_id,
            severity="info",
        )
    )
    # 3. Normal DB select
    events.append(
        telemetry.emit(
            event_type="db.query",
            attributes={"table": "posts", "operation": "SELECT", "rows_affected": 3},
            target_resource="table:posts",
            trace_id=trace_id,
            severity="info",
        )
    )

    return {
        "status": "completed",
        "mode": "benign_traffic",
        "events_fired": len(events),
        "events": events,
    }

