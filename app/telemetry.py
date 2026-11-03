import logging
import os
import sys
from collections import deque
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger("instagram_app.telemetry")

try:
    from cyber_engine import CyberEngine, IngestResult
except ImportError:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)
    try:
        from cyber_engine import CyberEngine, IngestResult
    except ImportError:
        sdk_path = r"D:\Programing\MUSE AI\CYBER ENGINE\sdk"
        if os.path.exists(sdk_path) and sdk_path not in sys.path:
            sys.path.insert(0, sdk_path)
        try:
            from cyber_engine import CyberEngine, IngestResult
        except ImportError:
            CyberEngine = None
            IngestResult = None

from .config import settings


class TelemetryService:
    """
    Manages telemetry integration with CYBER ENGINE / Ternline security platform.
    Dispatches non-blocking, buffered events for HTTP ingress, security signals,
    and user authentication lifecycles.
    """

    def __init__(self):
        self.enabled = settings.telemetry_enabled
        self.client: Optional[CyberEngine] = None
        self.recent_events: deque = deque(maxlen=50)
        self._init_client()

    def _init_client(self):
        if not self.enabled:
            logger.info("Cyber Engine telemetry is disabled via configuration.")
            return

        if CyberEngine is None:
            logger.warning("cyber_engine SDK is not available. Telemetry disabled.")
            return

        try:
            self.client = CyberEngine(
                api_key=settings.cyber_engine_api_key,
                app=settings.app_id,
                service=settings.service_id,
                endpoint=settings.cyber_engine_url,
                buffered=True,
                buffer_size=1000,
                flush_interval_seconds=1.5,
                auto_sanitize=True,
                allow_insecure_http=True,
            )
            logger.info(
                f"Connected to Cyber Engine telemetry endpoint: {settings.cyber_engine_url} (app={settings.app_id}, service={settings.service_id})"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Cyber Engine client: {e}")
            self.client = None

    def emit(
        self,
        event_type: str,
        severity: str = "info",
        source_resource: Optional[str] = None,
        target_resource: Optional[str] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """
        Emits a structured event to Cyber Engine via the non-blocking buffered pipeline.
        Never raises exceptions or blocks critical user paths.
        """
        record = {
            "event_type": event_type,
            "severity": severity,
            "source_resource": source_resource,
            "target_resource": target_resource,
            "trace_id": trace_id,
            "request_id": request_id,
            "attributes": attributes or {},
        }
        self.recent_events.append(record)

        if not self.enabled or not self.client:
            return None

        try:
            return self.client.emit(
                event_type=event_type,
                severity=severity,
                source_resource=source_resource,
                target_resource=target_resource,
                trace_id=trace_id,
                request_id=request_id,
                attributes=attributes,
            )
        except Exception as e:
            logger.debug(f"Telemetry emission failed: {e}")
            return None

    def close(self):
        """Cleanly drains buffer and closes client."""
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass

    async def check_health(self) -> Dict[str, Any]:
        """Probes Cyber Engine endpoint health."""
        endpoint = settings.cyber_engine_url.rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=3.0) as http_client:
                resp = await http_client.get(f"{endpoint}/health")
                return {
                    "reachable": resp.status_code == 200,
                    "status_code": resp.status_code,
                    "endpoint": endpoint,
                }
        except Exception as e:
            return {
                "reachable": False,
                "error": str(e),
                "endpoint": endpoint,
            }


telemetry = TelemetryService()
