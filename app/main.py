import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .config import settings
from .routes.auth import router as auth_router
from .routes.feed import router as feed_router
from .routes.messages import router as messages_router
from .routes.search import router as search_router

app = FastAPI(
    title=settings.app_name,
    description="Clean, production-ready social media platform",
    version=settings.version,
)

# CORS configuration
raw_cors = os.getenv("ALLOWED_CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000")
origins = [o.strip() for o in raw_cors.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_dir = os.path.join(base_dir, "static")
templates_dir = os.path.join(base_dir, "templates")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory=templates_dir)

# Register routers
app.include_router(auth_router)
app.include_router(feed_router)
app.include_router(messages_router)
app.include_router(search_router)


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


@app.get("/health")
async def health():
    """Application health probe."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.version,
    }
