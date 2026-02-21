"""
Smart Notebook Print Formatter - Main FastAPI Application
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .api.routes import router

# Check if running in serverless environment
IS_SERVERLESS = os.environ.get("VERCEL", False) or os.environ.get("AWS_LAMBDA_FUNCTION_NAME", False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    if not IS_SERVERLESS:
        print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    yield
    # Shutdown
    if not IS_SERVERLESS:
        print("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Convert Jupyter/Python notebooks into professionally formatted printable reports",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

# Mount static files only in non-serverless environments
if not IS_SERVERLESS:
    try:
        from fastapi.staticfiles import StaticFiles
        if settings.OUTPUT_DIR.exists():
            app.mount("/outputs", StaticFiles(directory=str(settings.OUTPUT_DIR)), name="outputs")
    except Exception:
        pass


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
