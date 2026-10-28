import os
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "InstaTern"
    version: str = "1.0.0"
    port: int = int(os.environ.get("PORT", "8080"))
    environment: str = os.environ.get("ENV", "development")

    # Cyber Engine Ingestion Configuration
    cyber_engine_url: str = os.environ.get("CYBER_ENGINE_URL", "http://localhost:8000").rstrip("/")
    cyber_engine_api_key: str = os.environ.get(
        "CYBER_ENGINE_API_KEY", "ce_live_test_api_key_secret_12345"
    )
    tenant_id: str = os.environ.get("TENANT_ID", "tenant-alpha")
    app_id: str = os.environ.get("APP_ID", "instagram-app")
    service_id: str = os.environ.get("SERVICE_ID", "instagram-api")

    # Telemetry buffering
    telemetry_enabled: bool = os.environ.get("TELEMETRY_ENABLED", "true").lower() == "true"
    telemetry_buffered: bool = os.environ.get("TELEMETRY_BUFFERED", "false").lower() == "true"


settings = Settings()

