"""FastAPI application entry point."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.logging_config import setup_logging
from app.routers.data_import import router as import_router
from app.routers.movies import router as movies_router

# Configure logging on module import
setup_logging()
logger = logging.getLogger("douban.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager."""
    logger.info("Application starting up...")
    # Startup
    init_db()
    logger.info("Database initialized successfully")
    yield
    # Shutdown
    logger.info("Application shutting down...")


app = FastAPI(
    title="Douban Movie Explorer API",
    description="API for exploring Douban movies and TV shows",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(movies_router, prefix="/api")
app.include_router(import_router, prefix="/api")


@app.get("/api/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
