"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import settings
from app.middleware.auth import AuthMiddleware
from app.routers import airline, feedback, knowledge, llm, packing, trip, vision, weather
from app.services.database import db_service

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize DB on startup."""
    db_service.initialize_schema()
    logger.info("Smart Baggage Architect started — version {v}", v=settings.app_version)
    yield
    db_service.close()
    logger.info("Smart Baggage Architect shutting down")


app = FastAPI(
    title=settings.app_name,
    description="AI-powered travel packing assistant -- backend API",
    version=settings.app_version,
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Authentication
app.add_middleware(AuthMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check(request: Request) -> dict:
    """Health check endpoint."""
    return {"status": "ok", "version": settings.app_version, "app": settings.app_name}


# Register all routers
app.include_router(trip.router, prefix="/api/trip", tags=["trip"])
app.include_router(packing.router, prefix="/api/packing", tags=["packing"])
app.include_router(airline.router, prefix="/api/airline", tags=["airline"])
app.include_router(weather.router, prefix="/api/weather", tags=["weather"])
app.include_router(vision.router, prefix="/api/vision", tags=["vision"])
app.include_router(llm.router, prefix="/api/llm", tags=["llm"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])
