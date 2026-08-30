import sys
import os
import asyncio
import threading
import logging

# Add the workspace root to sys.path to resolve root-level imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from backend.app.core.config import settings
from backend.app.repositories.database import init_db
from backend.app.api import location, simulation, incidents, approval, reports, chat, auth, email

logger = logging.getLogger("hres.startup")

# ── Allowed origins ────────────────────────────────────────────────────────────
# In production: replace with your actual domain (e.g. https://hres.yourdomain.com)
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

# Load extra origins from environment for production deployments
_extra_origins = os.getenv("ALLOWED_ORIGINS", "")
if _extra_origins:
    ALLOWED_ORIGINS.extend([o.strip() for o in _extra_origins.split(",") if o.strip()])


def _startup_weather_fetch():
    """Run Open-Meteo ingest on startup in a background thread."""
    try:
        from backend.app.services.monitoring import get_or_create_active_incident
        from backend.app.services.openmeteo_service import run_openmeteo_ingest
        incident = get_or_create_active_incident()
        run_openmeteo_ingest(
            incident.incident_id,
            settings.DEFAULT_LATITUDE,
            settings.DEFAULT_LONGITUDE,
            settings.DEFAULT_LOCATION_NAME,
            trigger_process=True
        )
        logger.info("Startup Open-Meteo ingest complete.")
    except Exception as e:
        logger.warning(f"Startup Open-Meteo ingest failed (non-critical): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    init_db()
    logger.info("Database initialized.")
    # Fire Open-Meteo weather fetch in background thread (non-blocking)
    thread = threading.Thread(target=_startup_weather_fetch, daemon=True)
    thread.start()
    yield
    # Cleanup on shutdown (nothing needed for now)


app = FastAPI(
    title=settings.APP_NAME,
    description="HRES (Heat Response Emergency System) Backend Service",
    version="1.0.0",
    lifespan=lifespan,
    # Disable OpenAPI in production for security
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# ── Security Middleware ────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Add security headers to every response."""
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    # Only add HSTS on HTTPS
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "debug": settings.DEBUG,
    }


# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(location.router,   prefix=settings.API_V1_STR)
app.include_router(simulation.router, prefix=settings.API_V1_STR)
# reports MUST come before incidents so /{incident_id}/aar is not swallowed by /{incident_id}
app.include_router(reports.router,    prefix=settings.API_V1_STR)
app.include_router(incidents.router,  prefix=settings.API_V1_STR)
app.include_router(approval.router,   prefix=settings.API_V1_STR)
app.include_router(chat.router,       prefix=settings.API_V1_STR)
app.include_router(auth.router,       prefix=settings.API_V1_STR)
app.include_router(email.router,      prefix=settings.API_V1_STR)
