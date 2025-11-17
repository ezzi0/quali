"""FastAPI application entry point"""
from .routes import agent, leads, inventory, webhooks, marketing, monitoring
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
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
