"""
FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.api import ingest, reviews, query, themes, segments, opportunities, synthesis, quotes, health


# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — startup and shutdown."""
    # Startup
    print("🚀 Spotify Discovery Engine starting up (Serverless Mode)...")
    print(f"   Environment: {settings.app_env}")
    print(f"   Database: {settings.database_url[:50]}...")
    print("⚠️ APScheduler disabled for Serverless compatibility. Using Vercel Crons.")

    yield

    # Shutdown
    print("🛑 Spotify Discovery Engine shutting down...")



app = FastAPI(
    title="Spotify Discovery Engine",
    description="AI-Powered Review Discovery Intelligence Platform — Spotify Growth Team",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# State for rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(ingest.router, prefix="/api", tags=["Ingestion"])
app.include_router(reviews.router, prefix="/api", tags=["Reviews"])
app.include_router(query.router, prefix="/api", tags=["Query"])
app.include_router(themes.router, prefix="/api", tags=["Themes"])
app.include_router(segments.router, prefix="/api", tags=["Segments"])
app.include_router(opportunities.router, prefix="/api", tags=["Opportunities"])
app.include_router(synthesis.router, prefix="/api", tags=["Synthesis"])
app.include_router(quotes.router, prefix="/api", tags=["Quotes & Collections"])


@app.get("/")
async def root():
    return {
        "name": "Spotify Discovery Engine",
        "version": "1.0.0",
        "docs": "/docs",
    }
