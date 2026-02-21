"""
Configuration settings for the Smart Notebook Print Formatter.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

# Check if running in serverless environment
IS_SERVERLESS = os.environ.get("VERCEL", False) or os.environ.get("AWS_LAMBDA_FUNCTION_NAME", False)


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "Smart Notebook Print Formatter"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # Paths - use /tmp for serverless
    BASE_DIR: Path = Path("/tmp") if IS_SERVERLESS else Path(__file__).parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    TEMPLATES_DIR: Path = Path(__file__).parent.parent / "templates"  # Keep templates in package
    TEMP_DIR: Path = BASE_DIR / "temp"
    
    # File limits
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: set = {".ipynb", ".py"}
    
    # Export settings
    DEFAULT_EXPORT_FORMAT: str = "docx"
    SUPPORTED_FORMATS: set = {"html", "docx"}
    
    # Graph handling
    GRAPH_DPI: int = 150
    GRAPH_FORMAT: str = "png"
    MAX_GRAPH_WIDTH: int = 800
    
    # Formatting
    CODE_THEME: str = "monokai"
    DEFAULT_TEMPLATE: str = "academic_report"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure directories exist
for directory in [settings.UPLOAD_DIR, settings.OUTPUT_DIR, settings.TEMP_DIR]:
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass  # May fail in read-only filesystem
