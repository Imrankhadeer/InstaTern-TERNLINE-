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


# ---------------------------------------------------------------------------
# Attack Scenario 1: Brute Force Password Spray
# ---------------------------------------------------------------------------
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
        time.sleep(0.04)

    return {
        "status": "completed",
        "attack": "brute_force_login",
        "target_user": target,
        "attempts_fired": req.attempts,
        "attacker_ip": attacker_ip,
        "detector_targeted": "BruteForceLoginDetector",
        "events": emitted,
        "message": f"Fired {req.attempts} failed login attempts against @{target} to Cyber Engine.",
    }


# ---------------------------------------------------------------------------
# Attack Scenario 2: Multi-Service APT Exfiltration (Cross-Service Correlation)
# ---------------------------------------------------------------------------
@router.post("/cross-service-exfil")
async def simulate_cross_service_exfiltration(req: CrossServiceExfilRequest):
    """
    Simulates an advanced coordinated attack spanning 3 distributed microservices:
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
        "message": f"Fired 3-stage correlated exfiltration sequence (trace_id: {shared_trace_id}).",
    }


# ---------------------------------------------------------------------------
# Attack Scenario 3: BOLA / IDOR Secret Direct Message Theft
# ---------------------------------------------------------------------------
@router.post("/bola-dm-theft")
async def simulate_bola_dm_theft():
    """
    Simulates Broken Object Level Authorization (BOLA / IDOR).
    An unauthorized user accesses private executive conversations containing API keys.
    """
    trace_id = f"trc_bola_{uuid.uuid4().hex[:10]}"
    target_conv_id = "conv_charlie_bob"
    conv = db.conversations.get(target_conv_id)

    # Telemetry: Security violation and data leakage
    r1 = telemetry.emit(
        event_type="security.alert",
        attributes={
            "alert_type": "BOLA_IDOR_VIOLATION",
            "conv_id": target_conv_id,
            "target_participants": conv.participants if conv else ["charlie_vip", "bob_cloud"],
            "sensitive_records_exposed": len(conv.messages) if conv else 3,
            "secret_types": ["api_token", "db_connection_string"],
        },
        source_resource="user:alice_cyber",
        target_resource=f"conversation:{target_conv_id}",
        trace_id=trace_id,
        severity="critical",
    )

    r2 = telemetry.emit(
        event_type="http.request",
        attributes={
            "method": "GET",
            "endpoint": f"/api/messages/{target_conv_id}",
            "is_unauthorized_bola": True,
            "status_code": 200,
        },
        source_resource="user:alice_cyber",
        target_resource=f"conversation:{target_conv_id}",
        trace_id=trace_id,
        severity="warning",
    )

    return {
        "status": "completed",
        "attack": "bola_idor_direct_message_theft",
        "stolen_conversation_id": target_conv_id,
        "leaked_messages": [m.model_dump() for m in conv.messages] if conv else [],
        "events": [r1, r2],
        "message": f"Exploited BOLA/IDOR on conversation '{target_conv_id}'! Leaked {len(conv.messages) if conv else 3} private executive messages.",
    }


# ---------------------------------------------------------------------------
# Attack Scenario 4: Search SQL Injection Bulk Leak
# ---------------------------------------------------------------------------
@router.post("/search-sqli")
async def simulate_search_sqli():
    """Simulates SQL injection exploitation in search yielding 850 leaked records."""
    trace_id = f"trc_sqli_{uuid.uuid4().hex[:10]}"
    sqli_payload = "' OR 1=1; SELECT * FROM users --"

    r1 = telemetry.emit(
        event_type="http.request",
        attributes={
            "method": "GET",
            "endpoint": "/api/search",
            "query_param": sqli_payload,
            "sqli_heuristic_flag": True,
            "status_code": 200,
        },
        source_resource="ip:198.51.100.99",
        target_resource="/api/search",
        trace_id=trace_id,
        severity="warning",
    )

    r2 = telemetry.emit(
        event_type="db.bulk_query",
        attributes={
            "table": "users",
            "rows_affected": 850,
            "query": f"SELECT * FROM users WHERE username LIKE '%{sqli_payload}%' OR 1=1;",
            "is_sqli_dump": True,
        },
        source_resource="service:instagram-api",
        target_resource="table:users",
        trace_id=trace_id,
        severity="critical",
    )

    return {
        "status": "completed",
        "attack": "sql_injection_bulk_leak",
        "payload": sqli_payload,
        "rows_exfiltrated": 850,
        "events": [r1, r2],
        "message": "Executed SQL Injection exfiltration against 'users' table (850 rows leaked).",
    }


# ---------------------------------------------------------------------------
# Attack Scenario 5: High-Frequency Profile Scraper Bot
# ---------------------------------------------------------------------------
@router.post("/api-scraping")
async def simulate_api_scraping():
    """Simulates automated scraper bot iterating through user profiles in rapid succession."""
    trace_id = f"trc_scrape_{uuid.uuid4().hex[:10]}"
    bot_ip = "185.220.101.5"
    events = []

    for username in list(db.users.keys()) * 3:
        rec = telemetry.emit(
            event_type="http.request",
            attributes={
                "method": "GET",
                "endpoint": f"/api/users/{username}",
                "user_agent": "python-requests/2.31.0 (Automated Scraper Bot)",
                "client_ip": bot_ip,
                "status_code": 200,
            },
            source_resource=f"ip:{bot_ip}",
            target_resource=f"user:{username}",
            trace_id=trace_id,
            severity="warning",
        )
        events.append(rec)
        time.sleep(0.02)

    return {
        "status": "completed",
        "attack": "api_rate_scraping",
        "requests_burst": len(events),
        "bot_ip": bot_ip,
        "events": events,
        "message": f"Fired {len(events)} automated scraping requests in rapid burst from {bot_ip}.",
    }


# ---------------------------------------------------------------------------
# Attack Scenario 6: Privilege Escalation Credential Dump
# ---------------------------------------------------------------------------
@router.post("/privilege-escalation")
async def simulate_privilege_escalation():
    """Simulates accessing internal admin database dump without admin privileges."""
    trace_id = f"trc_priv_esc_{uuid.uuid4().hex[:10]}"

    r1 = telemetry.emit(
        event_type="security.alert",
        attributes={
            "alert_type": "UNAUTHORIZED_ADMIN_DUMP",
            "endpoint": "/api/admin/dump-users",
            "requester": "hacker_zero",
            "escalation_method": "role_claim_forgery",
        },
        source_resource="user:hacker_zero",
        target_resource="/api/admin/dump-users",
        trace_id=trace_id,
        severity="critical",
    )

    r2 = telemetry.emit(
        event_type="db.bulk_query",
        attributes={
            "table": "users",
            "operation": "FULL_CREDENTIAL_DUMP",
            "rows_affected": len(db.users),
            "columns": ["id", "username", "password_hash", "session_tokens"],
        },
        source_resource="user:hacker_zero",
        target_resource="table:users",
        trace_id=trace_id,
        severity="critical",
    )

    return {
        "status": "completed",
        "attack": "privilege_escalation_credential_dump",
        "dumped_users": len(db.users),
        "events": [r1, r2],
        "message": f"Exploited broken role authorization to dump all user credential hashes ({len(db.users)} accounts).",
    }


# ---------------------------------------------------------------------------
# Scenario 7: Normal Benign Traffic
# ---------------------------------------------------------------------------
@router.post("/benign-traffic")
async def simulate_benign_traffic():
    """Simulates normal benign social operations (browsing, liking, commenting)."""
    trace_id = f"trc_benign_{uuid.uuid4().hex[:10]}"
    events = []

    events.append(
        telemetry.emit(
            event_type="http.request",
            attributes={"method": "GET", "endpoint": "/api/feed", "status_code": 200},
            target_resource="/api/feed",
            trace_id=trace_id,
            severity="info",
        )
    )
    events.append(
        telemetry.emit(
            event_type="http.request",
            attributes={"method": "POST", "endpoint": "/api/posts/post_1/like", "status_code": 200},
            target_resource="post:post_1",
            trace_id=trace_id,
            severity="info",
        )
    )
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
        "message": "Fired 3 clean benign user events with zero false-positives.",
    }
