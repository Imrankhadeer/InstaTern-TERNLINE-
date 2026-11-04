import os
from pydantic import BaseModel

# Automatically load local .env if present
env_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(env_file_path):
    with open(env_file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


class Settings(BaseModel):
    app_name: str = "InstaTern"
    version: str = "2.0.0"
    port: int = int(os.environ.get("PORT", "8080"))
    environment: str = os.environ.get("ENV", "production")
    secret_key: str = os.environ.get("SECRET_KEY", "super-secret-jwt-key-change-in-production-2026")
    db_path: str = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "instagram.db"))
    cyber_engine_url: str = os.environ.get("TERNLINE_ENDPOINT", os.environ.get("CYBER_ENGINE_URL", "http://13.211.144.111:8000"))
    cyber_engine_api_key: str = os.environ.get("TERNLINE_API_KEY", os.environ.get("CYBER_ENGINE_API_KEY", "ce_live_test_api_key_secret_12345"))
    app_id: str = os.environ.get("TERNLINE_APP_ID", os.environ.get("APP_ID", "instagr-app"))
    service_id: str = os.environ.get("TERNLINE_SERVICE_ID", os.environ.get("SERVICE_ID", "instagr-tern"))
    telemetry_enabled: bool = os.environ.get("TELEMETRY_ENABLED", "true").lower() in ("true", "1", "yes")


settings = Settings()
