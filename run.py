import os
import uvicorn
from app.config import settings

if __name__ == "__main__":
    port = int(os.environ.get("PORT", settings.port))
    print(f"==================================================")
    print(f"🚀 Starting InstaTern (Instagram Test App)")
    print(f"🌐 Server listening on http://0.0.0.0:{port}")
    print(f"🛡️ Cyber Engine Ingestion: {settings.cyber_engine_url}")
    print(f"🔑 App ID: {settings.app_id} | Tenant: {settings.tenant_id}")
    print(f"==================================================")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)

