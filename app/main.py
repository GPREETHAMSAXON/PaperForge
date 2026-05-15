from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.api.routes import health, parse, analyze, generate, benchmark

settings = get_settings()
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "PaperForge starting | version=%s env=%s",
        settings.app_version,
        settings.environment,
    )
    yield
    logger.info("PaperForge shutting down")


app = FastAPI(
    title="PaperForge API",
    description=(
        "Parse ML research papers from arXiv or PDF uploads, "
        "extract structured methodology, and generate runnable implementations."
    ),
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── CORS ──────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Global exception handler ──────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s: %s", request.method, request.url, exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. Please try again.",
            "type": type(exc).__name__,
        },
    )

# ─── Routers ───────────────────────────────────────────────────────────────

app.include_router(health.router)
app.include_router(parse.router, prefix="/api/v1")
app.include_router(analyze.router, prefix="/api/v1")
app.include_router(generate.router, prefix="/api/v1")
app.include_router(benchmark.router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "PaperForge API",
        "version": settings.app_version,
        "docs": "/docs",
    }
