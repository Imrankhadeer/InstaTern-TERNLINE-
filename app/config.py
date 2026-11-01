import os
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "InstaTern"
    version: str = "2.0.0"
    port: int = int(os.environ.get("PORT", "8000"))
    environment: str = os.environ.get("ENV", "production")
    secret_key: str = os.environ.get("SECRET_KEY", "super-secret-jwt-key-change-in-production-2026")
    db_path: str = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "instagram.db"))


settings = Settings()
