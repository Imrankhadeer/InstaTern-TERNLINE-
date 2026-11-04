import os
import uvicorn
from app.config import settings

if __name__ == "__main__":
    port = int(os.environ.get("PORT", settings.port))
    print("=" * 50)
    print(f"Starting {settings.app_name}")
    print(f"Server listening on http://0.0.0.0:{port}")
    print("=" * 50)
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
