import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from ..telemetry import telemetry

router = APIRouter(prefix="/api/worker", tags=["worker"])


class WorkerJobRequest(BaseModel):
    job_type: str = "image_resizer"
    image_url: str
    is_malicious: bool = False
    trace_id: Optional[str] = None


@router.post("/process-media")
async def process_media_job(req: WorkerJobRequest):
    """
    Simulates async background worker media processing (e.g., Celery/Cloud Run worker).
    Emits 'worker.job_anomalous' when anomalous/malicious image payloads are submitted.
    """
    trace_id = req.trace_id or f"trc_worker_{uuid.uuid4().hex[:12]}"

    if req.is_malicious or "bomb" in req.image_url.lower() or "overflow" in req.image_url.lower():
        # Anomalous worker failure
        telemetry.emit(
            event_type="worker.job_anomalous",
            attributes={
                "job_type": req.job_type,
                "anomaly_flag": True,
                "error": "Decompression bomb detected during media transcoding",
                "cpu_spike_percent": 99.8,
                "memory_used_mb": 4096,
                "target_image": req.image_url,
            },
            source_resource="worker:media-transcoder",
            target_resource=f"media:{req.image_url}",
            trace_id=trace_id,
            severity="high",
        )
        return {
            "status": "anomalous_failure",
            "trace_id": trace_id,
            "message": "Worker job failed with anomaly flag. Telemetry emitted to Cyber Engine.",
        }

    # Normal worker completion
    telemetry.emit(
        event_type="worker.job_completed",
        attributes={
            "job_type": req.job_type,
            "duration_ms": 38.2,
            "output_dimensions": "600x600",
        },
        source_resource="worker:media-transcoder",
        trace_id=trace_id,
        severity="info",
    )

    return {
        "status": "completed",
        "trace_id": trace_id,
        "thumbnail_url": req.image_url,
    }

