import os
import sys
import uuid
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from collections import deque
import httpx

from .config import settings

logger = logging.getLogger("instagram_app.telemetry")

# Attempt importing CyberEngine SDK, fallback to local path if running from repo root
try:
    from cyber_engine import CyberEngine, Event
except ImportError:
    sdk_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "sdk")
    )
    if os.path.exists(sdk_path) and sdk_path not in sys.path:
        sys.path.insert(0, sdk_path)
    try:
        from cyber_engine import CyberEngine, Event
    except ImportError:
        CyberEngine = None
        Event = None
        logger.warning("CyberEngine SDK could not be imported; falling back to direct HTTP ingestion.")


class TelemetryManager:
    """
    Manages telemetry event emission from the Instagram clone to Cyber Engine.
    Keeps a rolling buffer of recently emitted events for the interactive UI dock.
    """

    def __init__(self):
        self.client: Optional[Any] = None
        self.recent_events: deque = deque(maxlen=50)
        self._init_client()

    def _init_client(self):
        if not settings.telemetry_enabled:
            logger.info("Telemetry is disabled via settings.")
            return

        if CyberEngine:
            try:
                self.client = CyberEngine(
                    api_key=settings.cyber_engine_api_key,
                    app=settings.app_id,
                    service=settings.service_id,
                    endpoint=settings.cyber_engine_url,
                    buffered=settings.telemetry_buffered,
                    timeout_seconds=4.0,
                )
                logger.info(
                    f"CyberEngine SDK initialized for endpoint {settings.cyber_engine_url}"
                )
            except Exception as e:
                logger.error(f"Failed to initialize CyberEngine client: {e}")
                self.client = None

    def emit(
        self,
        event_type: str,
        attributes: Optional[Dict[str, Any]] = None,
        source_resource: Optional[str] = None,
        target_resource: Optional[str] = None,
        trace_id: Optional[str] = None,
        severity: str = "info",
    ) -> Dict[str, Any]:
        """
        Emits a security telemetry event to Cyber Engine and stores it in the local UI buffer.
        """
        attributes = attributes or {}
        event_id = str(uuid.uuid4())
        trace_id = trace_id or str(uuid.uuid4())
        ts = datetime.now(timezone.utc).isoformat()

        record = {
            "event_id": event_id,
            "timestamp": ts,
            "event_type": event_type,
            "severity": severity,
            "app_id": settings.app_id,
            "service_id": settings.service_id,
            "source_resource": source_resource,
            "target_resource": target_resource,
            "trace_id": trace_id,
            "attributes": attributes,
            "delivery_status": "pending",
            "delivery_latency_ms": 0,
        }

        start_time = time.time()
        success = False
        error_msg = None

        if settings.telemetry_enabled:
            # 1. Try SDK first if available
            if self.client:
                try:
                    result = self.client.emit(
                        event_type=event_type,
                        attributes=attributes,
                        source_resource=source_resource,
                        target_resource=target_resource,
                        trace_id=trace_id,
                        severity=severity,
                    )
                    success = getattr(result, "success", True)
                except Exception as e:
                    error_msg = str(e)
                    logger.warning(f"SDK emission failed, falling back to direct HTTP: {e}")

            # 2. Fallback to direct HTTP ingestion if SDK is unavailable or failed
            if not success and not self.client:
                try:
                    payload = {
                        "events": [
                            {
                                "event_id": event_id,
                                "schema_version": "1.0.0",
                                "timestamp": ts,
                                "app_id": settings.app_id,
                                "service_id": settings.service_id,
                                "event_type": event_type,
                                "severity": severity,
                                "source_resource": source_resource,
                                "target_resource": target_resource,
                                "trace_id": trace_id,
                                "attributes": attributes,
                            }
                        ]
                    }
                    with httpx.Client(timeout=4.0) as http:
                        resp = http.post(
                            f"{settings.cyber_engine_url}/api/v1/ingest",
                            json=payload,
                            headers={
                                "Authorization": f"Bearer {settings.cyber_engine_api_key}",
                                "Content-Type": "application/json",
                            },
                        )
                        if resp.status_code == 200:
                            success = True
                        else:
                            error_msg = f"HTTP {resp.status_code}: {resp.text}"
                except Exception as e:
                    error_msg = str(e)

        latency_ms = round((time.time() - start_time) * 1000, 2)
        record["delivery_latency_ms"] = latency_ms
        record["delivery_status"] = "accepted" if success else ("failed: " + (error_msg or "offline"))

        self.recent_events.appendleft(record)
        return record

    async def check_connection(self) -> Dict[str, Any]:
        """Checks connectivity to Cyber Engine health endpoint."""
        url = f"{settings.cyber_engine_url}/health"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    return {
                        "connected": True,
                        "status_code": 200,
                        "url": settings.cyber_engine_url,
                        "data": res.json(),
                    }
                return {
                    "connected": False,
                    "status_code": res.status_code,
                    "url": settings.cyber_engine_url,
                    "error": res.text,
                }
        except Exception as e:
            return {
                "connected": False,
                "url": settings.cyber_engine_url,
                "error": str(e),
            }


telemetry = TelemetryManager()

