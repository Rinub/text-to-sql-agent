"""
FastAPI application entry point.

- Configures CORS middleware
- Seeds the database on startup
- Mounts API routes
- Exposes Swagger UI at /docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import router as api_router
from app.database.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle handler."""
    # --- Startup ---
    print("🚀 Starting Self-Healing Text-to-SQL Agent...")
    seed_database()
    print("✅ Database seeded and ready.")
    yield
    # --- Shutdown ---
    print("👋 Shutting down...")


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint — redirects to docs."""
    return {
        "message": "Self-Healing Text-to-SQL Agent",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
