"""
HTML Exporter - Generates standalone HTML files.
"""
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List
import re

from ..graph_handler.graph_storage import StoredGraph


class HTMLExporter:
    """Exports formatted content to standalone HTML."""
    
    def __init__(self):
        pass
    
    def export(
        self,
        html_content: str,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Export HTML content to a file."""
        options = options or {}
        
        # Ensure it's a complete HTML document
        if not html_content.strip().lower().startswith("<!doctype"):
            html_content = self._wrap_in_document(html_content)
        
        # Add print styles if requested
        if options.get("print_styles", True):
            html_content = self._add_print_styles(html_content)
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding="utf-8")
        
        return output_path
    
    def export_standalone(
        self,
        html_content: str,
        output_path: Path,
        graphs: Optional[List[StoredGraph]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Export as standalone HTML with embedded images."""
        options = options or {}
        
        # Embed images as base64
        if graphs:
            html_content = self._embed_images(html_content, graphs)
        
        # Inline all CSS
        html_content = self._inline_external_resources(html_content)
        
        return self.export(html_content, output_path, options)
    
    def _wrap_in_document(self, content: str) -> str:
        """Wrap content in a basic HTML document."""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notebook Export</title>
</head>
<body>
{content}
</body>
</html>'''
    
    def _add_print_styles(self, html_content: str) -> str:
        """Add print-optimized styles."""
        print_styles = '''
<style>
@media print {
    body {
        font-size: 11pt;
        line-height: 1.4;
    }
    
    .highlight, pre {
        page-break-inside: avoid;
        font-size: 9pt;
    }
    
    h1, h2, h3 {
        page-break-after: avoid;
    }
    
    figure {
        page-break-inside: avoid;
    }
    
    .no-print {
        display: none !important;
    }
    
    a {
        text-decoration: none;
        color: inherit;
    }
    
    a[href^="http"]::after {
        content: " (" attr(href) ")";
        font-size: 0.8em;
        color: #666;
    }
}

@page {
    margin: 2cm;
}
</style>
'''
        # Insert before </head>
        return html_content.replace("</head>", f"{print_styles}</head>")
    
    def _embed_images(self, html_content: str, graphs: List[StoredGraph]) -> str:
        """Embed images as base64 data URIs."""
        for graph in graphs:
            file_path = Path(graph.file_path)
            if not file_path.exists():
                continue
            
            # Read and encode image
            image_data = file_path.read_bytes()
            b64_data = base64.b64encode(image_data).decode("utf-8")
            
            # Determine mime type
            mime_type = f"image/{graph.format}"
            if graph.format == "svg":
                mime_type = "image/svg+xml"
            
            # Create data URI
            data_uri = f"data:{mime_type};base64,{b64_data}"
            
            # Replace file path references
            html_content = html_content.replace(
                f'src="{graph.file_path}"',
                f'src="{data_uri}"'
            )
            html_content = html_content.replace(
                f"src='{graph.file_path}'",
                f'src="{data_uri}"'
            )
        
        return html_content
    
    def _inline_external_resources(self, html_content: str) -> str:
        """Inline external CSS and JS (for truly standalone files)."""
        # This is a placeholder - in production, would fetch and inline
        # external resources referenced in <link> and <script> tags
        return html_content
    
    def create_preview(
        self,
        html_content: str,
        max_cells: int = 10,
    ) -> str:
        """Create a preview version with limited content."""
        # Count cells and truncate
        cell_pattern = r'<div class="cell[^"]*">'
        cells = list(re.finditer(cell_pattern, html_content))
        
        if len(cells) <= max_cells:
            return html_content
        
        # Find position of max_cells + 1 cell and truncate
        truncate_pos = cells[max_cells].start()
        
        truncated = html_content[:truncate_pos]
        truncated += f'''
<div class="preview-notice" style="
    text-align: center;
    padding: 2rem;
    background: #f5f5f5;
    border: 1px dashed #ccc;
    margin: 1rem 0;
">
    <p>Preview truncated. {len(cells) - max_cells} more cells...</p>
</div>
'''
        
        # Close any open tags
        truncated += "</body></html>"
        
        return truncated
    
    def minify(self, html_content: str) -> str:
        """Minify HTML content."""
        # Remove comments
        html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
        
        # Remove extra whitespace (but preserve pre/code formatting)
        # This is a simple version - production would use proper minifier
        lines = html_content.split('\n')
        minified = ' '.join(line.strip() for line in lines)
        minified = re.sub(r'\s{2,}', ' ', minified)
        
        return minified
