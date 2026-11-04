import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .config import settings
from .telemetry import telemetry
from .routes.auth import router as auth_router
from .routes.feed import router as feed_router
from .routes.messages import router as messages_router
from .routes.search import router as search_router
from .routes.social import router as social_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    telemetry.close()


app = FastAPI(
    title=settings.app_name,
    description="Clean, production-ready social media platform with complex endpoints",
    version=settings.version,
    lifespan=lifespan,
)

raw_cors = os.getenv("ALLOWED_CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000")
origins = [o.strip() for o in raw_cors.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def ternline_telemetry_middleware(request: Request, call_next):
    """
    Standard Ternline telemetry middleware.
    Emits non-blocking http.request and http.server_error events to Cyber Engine.
    """
    start_time = time.time()
    trace_id = request.headers.get("x-trace-id") or request.headers.get("traceparent")
    client_ip = request.client.host if request.client else "unknown"

    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)

        severity = "info"
        if response.status_code >= 500:
            severity = "high"
        elif response.status_code in (401, 403, 429):
            severity = "medium"

        # Avoid spamming telemetry with static asset polls
        if not request.url.path.startswith("/static/"):
            telemetry.emit(
                event_type="http.request",
                severity=severity,
                source_resource=client_ip,
                target_resource=f"{request.method} {request.url.path}",
                trace_id=trace_id,
                attributes={
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "user_agent": request.headers.get("user-agent", "unknown"),
                },
            )
        return response
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        telemetry.emit(
            event_type="http.server_error",
            severity="critical",
            source_resource=client_ip,
            target_resource=f"{request.method} {request.url.path}",
            trace_id=trace_id,
            attributes={
                "error": str(exc),
                "duration_ms": duration_ms,
            },
        )
        raise


base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_dir = os.path.join(base_dir, "static")
templates_dir = os.path.join(base_dir, "templates")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory=templates_dir)

# Register API routes
app.include_router(auth_router)
app.include_router(feed_router)
app.include_router(messages_router)
app.include_router(search_router)
app.include_router(social_router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Renders the main application feed."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": settings.app_name},
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Renders the login and registration page."""
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"app_name": settings.app_name},
    )


@app.get("/profile/{username}", response_class=HTMLResponse)
async def profile_page(request: Request, username: str):
    """Renders the dedicated user profile page."""
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={"app_name": settings.app_name, "target_username": username},
    )


@app.get("/health")
async def health():
    """Application health probe with Cyber Engine reachability details."""
    telemetry_probe = await telemetry.check_health()
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.version,
        "telemetry": {
            "enabled": telemetry.enabled,
            "connected": telemetry_probe.get("reachable", False),
            "endpoint": settings.cyber_engine_url,
        },
    }
