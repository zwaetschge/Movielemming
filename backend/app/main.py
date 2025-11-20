"""
FastAPI main application for MediaCleaner
"""
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .models.database import init_db
from .api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global database session
SessionLocal = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for FastAPI application"""
    global SessionLocal

    logger.info("Starting MediaCleaner application")

    # Initialize database
    logger.info(f"Initializing database at {settings.DATABASE_PATH}")
    engine, SessionLocal = init_db(settings.DATABASE_PATH)

    # Ensure thumbnail directory exists
    settings.THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Thumbnail directory: {settings.THUMBNAIL_DIR}")

    # Check data directory
    if settings.DATA_DIR.exists():
        logger.info(f"Data directory mounted: {settings.DATA_DIR}")
    else:
        logger.warning(f"Data directory not found: {settings.DATA_DIR}")

    yield

    # Cleanup
    logger.info("Shutting down MediaCleaner application")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Web application for identifying and managing duplicate movie files",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix=settings.API_PREFIX)

# Serve thumbnails as static files
app.mount(
    "/thumbnails",
    StaticFiles(directory=str(settings.THUMBNAIL_DIR)),
    name="thumbnails"
)

# Serve frontend static files (will be built React app)
frontend_path = Path("/app/frontend/dist")
if frontend_path.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(frontend_path), html=True),
        name="frontend"
    )
    logger.info("Serving frontend from /app/frontend/dist")
else:
    logger.warning("Frontend build not found, API-only mode")


@app.get("/")
async def root():
    """Root endpoint - will be overridden by frontend if built"""
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "api_docs": "/docs",
        "status": "running"
    }


# Dependency injection for database sessions
def get_db():
    """Get database session for dependency injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Make get_db available to routes
from .api import routes
routes.get_db_session = get_db


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
