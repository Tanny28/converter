"""
Smart Notebook Print Formatter - Main FastAPI Application
"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from .config import settings
from .api.routes import router

# Frontend path: main.py is at backend/src/main.py
# .parent = backend/src/, .parent.parent = backend/, .parent.parent.parent = project root
FRONTEND_PATH = Path(__file__).parent.parent.parent / "frontend" / "src"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    yield
    # Shutdown
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

# Mount static files for outputs
if settings.OUTPUT_DIR.exists():
    app.mount("/outputs", StaticFiles(directory=str(settings.OUTPUT_DIR)), name="outputs")

# Mount frontend static files
if FRONTEND_PATH.exists():
    app.mount("/styles", StaticFiles(directory=str(FRONTEND_PATH / "styles")), name="styles")
    app.mount("/scripts", StaticFiles(directory=str(FRONTEND_PATH / "scripts")), name="scripts")


@app.get("/")
async def root():
    """Serve frontend index.html."""
    index_path = FRONTEND_PATH / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Catch-all route to serve frontend for SPA routing."""
    # Try to serve static file first
    file_path = FRONTEND_PATH / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    # Otherwise serve index.html
    index_path = FRONTEND_PATH / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"error": "Not found"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
