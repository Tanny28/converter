"""
File Handler - Manages file uploads and temporary storage.
"""
import os
import uuid
import shutil
import hashlib
from pathlib import Path
from typing import Optional, Tuple, BinaryIO
from datetime import datetime, timedelta
import tempfile

from ..config import settings


class FileHandler:
    """Handles file operations for uploads and outputs."""
    
    def __init__(
        self,
        upload_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        temp_dir: Optional[Path] = None,
    ):
        self.upload_dir = upload_dir or settings.UPLOAD_DIR
        self.output_dir = output_dir or settings.OUTPUT_DIR
        self.temp_dir = temp_dir or settings.TEMP_DIR
        
        # Ensure directories exist
        for directory in [self.upload_dir, self.output_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return uuid.uuid4().hex[:16]
    
    async def save_upload(
        self,
        file: BinaryIO,
        filename: str,
        session_id: Optional[str] = None,
    ) -> Tuple[Path, str]:
        """Save an uploaded file and return path and session ID."""
        session_id = session_id or self.generate_session_id()
        session_dir = self.upload_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        file_path = session_dir / safe_filename
        
        # Save file
        content = file.read() if hasattr(file, 'read') else file
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        return file_path, session_id
    
    def save_upload_sync(
        self,
        content: bytes,
        filename: str,
        session_id: Optional[str] = None,
    ) -> Tuple[Path, str]:
        """Synchronous version of save_upload."""
        session_id = session_id or self.generate_session_id()
        session_dir = self.upload_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        safe_filename = self._sanitize_filename(filename)
        file_path = session_dir / safe_filename
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        return file_path, session_id
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal."""
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove potentially dangerous characters
        dangerous_chars = '<>:"/\\|?*'
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Ensure it's not empty
        if not filename:
            filename = "unnamed_file"
        
        # Add timestamp to prevent collisions
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"{name}_{timestamp}{ext}"
    
    def get_output_path(
        self,
        session_id: str,
        filename: str,
        format: str,
    ) -> Path:
        """Get the path for an output file."""
        session_dir = self.output_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        safe_filename = self._sanitize_filename(filename)
        name, _ = os.path.splitext(safe_filename)
        
        return session_dir / f"{name}.{format}"
    
    def get_session_files(self, session_id: str) -> dict:
        """Get all files for a session."""
        result = {
            "uploads": [],
            "outputs": [],
        }
        
        upload_dir = self.upload_dir / session_id
        if upload_dir.exists():
            result["uploads"] = [f.name for f in upload_dir.iterdir() if f.is_file()]
        
        output_dir = self.output_dir / session_id
        if output_dir.exists():
            result["outputs"] = [f.name for f in output_dir.iterdir() if f.is_file()]
        
        return result
    
    def get_file(self, session_id: str, filename: str, file_type: str = "output") -> Optional[Path]:
        """Get a specific file path."""
        if file_type == "upload":
            base_dir = self.upload_dir
        else:
            base_dir = self.output_dir
        
        file_path = base_dir / session_id / filename
        
        if file_path.exists() and file_path.is_file():
            return file_path
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete all files for a session."""
        deleted = False
        
        for base_dir in [self.upload_dir, self.output_dir, self.temp_dir]:
            session_dir = base_dir / session_id
            if session_dir.exists():
                shutil.rmtree(session_dir)
                deleted = True
        
        return deleted
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old session directories."""
        cleaned = 0
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        for base_dir in [self.upload_dir, self.output_dir, self.temp_dir]:
            if not base_dir.exists():
                continue
            
            for session_dir in base_dir.iterdir():
                if not session_dir.is_dir():
                    continue
                
                # Check modification time
                mtime = datetime.fromtimestamp(session_dir.stat().st_mtime)
                if mtime < cutoff_time:
                    shutil.rmtree(session_dir)
                    cleaned += 1
        
        return cleaned
    
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes."""
        return file_path.stat().st_size
    
    def create_temp_file(self, suffix: str = "") -> Path:
        """Create a temporary file."""
        fd, path = tempfile.mkstemp(suffix=suffix, dir=self.temp_dir)
        os.close(fd)
        return Path(path)
    
    def create_temp_dir(self) -> Path:
        """Create a temporary directory."""
        return Path(tempfile.mkdtemp(dir=self.temp_dir))
