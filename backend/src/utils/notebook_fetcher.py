"""
Notebook Fetcher - Fetch notebooks from URLs (Google Colab, GitHub, etc.)
"""
import re
import httpx
from pathlib import Path
from typing import Tuple, Optional
from urllib.parse import urlparse, unquote


class NotebookFetcher:
    """Fetches Jupyter notebooks from various online sources."""
    
    # URL patterns
    COLAB_PATTERN = re.compile(
        r'colab\.research\.google\.com/drive/([a-zA-Z0-9_-]+)'
    )
    COLAB_GITHUB_PATTERN = re.compile(
        r'colab\.research\.google\.com/github/([^/]+)/([^/]+)/blob/([^/]+)/(.+\.ipynb)'
    )
    GITHUB_BLOB_PATTERN = re.compile(
        r'github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+\.ipynb)'
    )
    GITHUB_RAW_PATTERN = re.compile(
        r'raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+\.ipynb)'
    )
    GIST_PATTERN = re.compile(
        r'gist\.github\.com/([^/]+)/([a-f0-9]+)'
    )
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    def parse_url(self, url: str) -> Tuple[str, str]:
        """
        Parse a notebook URL and return the download URL and filename.
        
        Returns:
            Tuple of (download_url, suggested_filename)
        """
        url = url.strip()
        
        # Google Colab with GitHub
        match = self.COLAB_GITHUB_PATTERN.search(url)
        if match:
            user, repo, branch, path = match.groups()
            download_url = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{path}"
            filename = Path(path).name
            return download_url, filename
        
        # Google Colab with Drive
        match = self.COLAB_PATTERN.search(url)
        if match:
            file_id = match.group(1)
            # Google Drive direct download link
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            filename = f"colab_notebook_{file_id[:8]}.ipynb"
            return download_url, filename
        
        # GitHub blob URL
        match = self.GITHUB_BLOB_PATTERN.search(url)
        if match:
            user, repo, branch, path = match.groups()
            download_url = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{path}"
            filename = Path(path).name
            return download_url, filename
        
        # GitHub raw URL (already a download URL)
        match = self.GITHUB_RAW_PATTERN.search(url)
        if match:
            _, _, _, path = match.groups()
            filename = Path(path).name
            return url, filename
        
        # GitHub Gist
        match = self.GIST_PATTERN.search(url)
        if match:
            user, gist_id = match.groups()
            # Gist raw URL pattern
            download_url = f"https://gist.githubusercontent.com/{user}/{gist_id}/raw"
            filename = f"gist_{gist_id[:8]}.ipynb"
            return download_url, filename
        
        # Direct .ipynb URL
        if url.endswith('.ipynb'):
            parsed = urlparse(url)
            filename = Path(unquote(parsed.path)).name
            return url, filename
        
        raise ValueError(
            "Unsupported URL format. Supported sources:\n"
            "- Google Colab (colab.research.google.com)\n"
            "- GitHub notebooks (github.com/.../blob/.../*.ipynb)\n"
            "- GitHub Gists (gist.github.com)\n"
            "- Direct .ipynb URLs"
        )
    
    async def fetch(self, url: str) -> Tuple[bytes, str]:
        """
        Fetch a notebook from URL.
        
        Returns:
            Tuple of (content_bytes, filename)
        """
        download_url, filename = self.parse_url(url)
        
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        ) as client:
            response = await client.get(download_url)
            response.raise_for_status()
            
            content = response.content
            
            # Validate it's actually JSON (notebook format)
            try:
                import json
                json.loads(content)
            except json.JSONDecodeError:
                # Check if it's a Google Drive HTML page (file not accessible)
                if b'<html' in content.lower()[:1000]:
                    raise ValueError(
                        "Could not download notebook. For Google Drive files, "
                        "make sure the file is publicly shared (Anyone with the link)."
                    )
                raise ValueError("Downloaded content is not a valid notebook (not JSON)")
            
            return content, filename
    
    def fetch_sync(self, url: str) -> Tuple[bytes, str]:
        """Synchronous version of fetch."""
        download_url, filename = self.parse_url(url)
        
        with httpx.Client(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        ) as client:
            response = client.get(download_url)
            response.raise_for_status()
            
            content = response.content
            
            # Validate it's actually JSON
            try:
                import json
                json.loads(content)
            except json.JSONDecodeError:
                if b'<html' in content.lower()[:1000]:
                    raise ValueError(
                        "Could not download notebook. For Google Drive files, "
                        "make sure the file is publicly shared."
                    )
                raise ValueError("Downloaded content is not a valid notebook")
            
            return content, filename
