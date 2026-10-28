import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .config import settings
from .telemetry import telemetry
from .routes.auth import router as auth_router
from .routes.feed import router as feed_router
from .routes.search import router as search_router
from .routes.worker import router as worker_router
from .routes.attacks import router as attacks_router

app = FastAPI(
    title="InstaTern",
    description="Instagram-like social application instrumented for Cyber Engine security testing",
    version=settings.version,
)

# Enable CORS for cloud deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static and templates
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_dir = os.path.join(base_dir, "static")
templates_dir = os.path.join(base_dir, "templates")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory=templates_dir)

# Register routes
app.include_router(auth_router)
app.include_router(feed_router)
app.include_router(search_router)
app.include_router(worker_router)
app.include_router(attacks_router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Renders the main Instagram interface with Cyber Engine security dock."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "cyber_engine_url": settings.cyber_engine_url,
            "app_id": settings.app_id,
            "tenant_id": settings.tenant_id,
        },
    )


@app.get("/health")
async def health():
    """Health check endpoint for Cloud Run, ECS, or Kubernetes readiness/liveness probes."""
    conn = await telemetry.check_connection()
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.version,
        "port": settings.port,
        "cyber_engine_connection": conn,
    }

