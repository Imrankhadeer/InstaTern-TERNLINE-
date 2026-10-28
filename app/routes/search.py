import uuid
from fastapi import APIRouter, Request, Query
from typing import Dict, Any

from ..database import db
from ..telemetry import telemetry

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search")
async def search(
    request: Request,
    q: str = Query("", description="Search term for users or tags")
):
    """
    Search users and posts.
    Demonstrates SQL injection vulnerability detection when malicious characters are queried.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    trace_id = f"trc_search_{uuid.uuid4().hex[:12]}"

    # Detect SQL injection attack pattern in search query
    sql_keywords = ["'", "or 1=1", "union select", "--", "drop table", "; select"]
    is_sqli = any(k in q.lower() for k in sql_keywords)

    if is_sqli:
        # Emit an anomalous DB bulk query event directly simulating SQLi exfiltration
        telemetry.emit(
            event_type="http.request",
            attributes={
                "method": "GET",
                "endpoint": "/api/search",
                "query_param": q,
                "status_code": 200,
                "client_ip": client_ip,
                "sqli_heuristic_flag": True,
            },
            source_resource=f"ip:{client_ip}",
            target_resource="/api/search",
            trace_id=trace_id,
            severity="warning",
        )

        telemetry.emit(
            event_type="db.bulk_query",
            attributes={
                "table": "users",
                "rows_affected": 850,
                "query": f"SELECT * FROM users WHERE username LIKE '%{q}%' OR 1=1;",
                "execution_time_ms": 142.5,
                "sensitive_data_accessed": ["password_hashes", "email_addresses", "phone_numbers"],
            },
            source_resource="service:instagram-api",
            target_resource="table:users",
            trace_id=trace_id,
            severity="critical",
        )

        return {
            "query": q,
            "attack_detected_by_app": True,
            "warning": "Simulated SQL Injection executed bulk query against 'users' table! Emitted db.bulk_query to Cyber Engine.",
            "results": {
                "users": list(db.users.values()),
                "posts": list(db.posts.values()),
                "leaked_user_rows": 850,
            },
        }

    # Normal search flow
    results = db.search(q)

    telemetry.emit(
        event_type="http.request",
        attributes={
            "method": "GET",
            "endpoint": "/api/search",
            "query_param": q,
            "status_code": 200,
            "client_ip": client_ip,
        },
        source_resource=f"ip:{client_ip}",
        target_resource="/api/search",
        trace_id=trace_id,
        severity="info",
    )

    return {
        "query": q,
        "results": results,
    }

