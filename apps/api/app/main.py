"""FastAPI application entry point"""
from .routes import agent, leads, inventory, webhooks, marketing, monitoring, admin, media
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
import time

from .config import get_settings
from .logging import configure_logging, get_logger, set_request_id
from .deps import get_qdrant
from .services.embedding_store import QdrantEmbeddingStore

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("application_startup", environment=settings.environment)

    # Initialize Qdrant collections
    try:
        qdrant_client = get_qdrant()
        embedding_store = QdrantEmbeddingStore(qdrant_client)
        logger.info("qdrant_initialized")
    except Exception as e:
        logger.error("qdrant_init_failed", error=str(e))

    yield

    # Shutdown
    logger.info("application_shutdown")


app = FastAPI(
    title="Real Estate AI CRM",
    version="0.1.0",
    lifespan=lifespan,
)

media_url = settings.media_url or "/uploads"
media_url = f"/{media_url.lstrip('/')}"
media_dir = Path(settings.media_dir)
media_dir.mkdir(parents=True, exist_ok=True)
app.mount(media_url, StaticFiles(directory=media_dir), name="uploads")

# CORS middleware
def parse_cors_origins(value: str) -> list[str]:
    origins = [item.strip() for item in value.split(",") if item.strip()]
    return origins or ["*"]


cors_origins = parse_cors_origins(settings.cors_allow_origins)
cors_allow_credentials = True
if "*" in cors_origins:
    cors_origins = ["*"]
    cors_allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Add request ID and timing to all requests"""
    # Set request ID
    request_id = request.headers.get("X-Request-ID")
    set_request_id(request_id)

    # Time the request
    start_time = time.time()

    try:
        response = await call_next(request)

        # Add timing
        duration = time.time() - start_time
        response.headers["X-Response-Time"] = f"{duration:.3f}s"

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration=duration,
        )

        return response

    except Exception as e:
        logger.error(
            "request_failed",
            method=request.method,
            path=request.url.path,
            error=str(e),
        )
        raise


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(
        "unhandled_exception",
        method=request.method,
        path=request.url.path,
        error=str(exc),
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "real-estate-ai-crm",
        "version": "0.1.0",
        "status": "healthy",
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "environment": settings.environment,
    }


# Import and include routers

app.include_router(agent.router, prefix="/agent", tags=["agent"])
app.include_router(leads.router, prefix="/leads", tags=["leads"])
app.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(marketing.router, prefix="/marketing", tags=["marketing"])
app.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(media.router, prefix="/media", tags=["media"])
