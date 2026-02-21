"""
Graph Extractor - Identifies and extracts visualizations from notebook outputs.
"""
import base64
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import io

from ..parser.notebook_parser import ParsedNotebook, NotebookCell, CellOutput


@dataclass
class ExtractedGraph:
    """Represents an extracted graph/visualization."""
    index: int
    cell_index: int
    image_data: bytes
    mime_type: str
    format: str  # 'png', 'jpeg', 'svg', 'pdf'
    width: Optional[int] = None
    height: Optional[int] = None
    caption: str = ""
    source_code: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class GraphExtractor:
    """Extracts graphs and visualizations from parsed notebooks."""
    
    MIME_TO_FORMAT = {
        "image/png": "png",
        "image/jpeg": "jpeg",
        "image/jpg": "jpeg",
        "image/gif": "gif",
        "image/svg+xml": "svg",
        "application/pdf": "pdf",
    }
    
    # Patterns to identify plotting code
    PLOT_PATTERNS = [
        r'\.plot\s*\(',
        r'\.scatter\s*\(',
        r'\.bar\s*\(',
        r'\.hist\s*\(',
        r'\.boxplot\s*\(',
        r'\.pie\s*\(',
        r'\.imshow\s*\(',
        r'\.heatmap\s*\(',
        r'\.lineplot\s*\(',
        r'\.countplot\s*\(',
        r'plt\.',
        r'sns\.',
        r'px\.',
        r'go\.',
        r'fig\.',
        r'\.figure\s*\(',
        r'plotly',
        r'matplotlib',
        r'seaborn',
    ]
    
    def __init__(self):
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.PLOT_PATTERNS]
    
    def extract_all(self, notebook: ParsedNotebook) -> List[ExtractedGraph]:
        """Extract all graphs from a parsed notebook."""
        graphs = []
        graph_index = 0
        
        for cell_idx, cell in enumerate(notebook.cells):
            if cell.cell_type != "code":
                continue
            
            cell_graphs = self._extract_from_cell(cell, cell_idx, graph_index)
            graphs.extend(cell_graphs)
            graph_index += len(cell_graphs)
        
        return graphs
    
    def _extract_from_cell(self, cell: NotebookCell, cell_index: int, start_index: int) -> List[ExtractedGraph]:
        """Extract graphs from a single code cell."""
        graphs = []
        current_index = start_index
        
        for output in cell.outputs:
            if not output.is_image:
                continue
            
            image_data = self._decode_image_data(output.image_data, output.mime_type)
            if image_data is None:
                continue
            
            graph = ExtractedGraph(
                index=current_index,
                cell_index=cell_index,
                image_data=image_data,
                mime_type=output.mime_type,
                format=self.MIME_TO_FORMAT.get(output.mime_type, "png"),
                caption=self._generate_basic_caption(cell, current_index),
                source_code=cell.source,
            )
            
            # Try to get image dimensions
            dims = self._get_image_dimensions(image_data, graph.format)
            if dims:
                graph.width, graph.height = dims
            
            graphs.append(graph)
            current_index += 1
        
        return graphs
    
    def _decode_image_data(self, data: Any, mime_type: str) -> Optional[bytes]:
        """Decode image data from various formats."""
        if isinstance(data, bytes):
            return data
        
        if isinstance(data, str):
            # Try base64 decoding
            try:
                return base64.b64decode(data)
            except Exception:
                pass
            
            # For SVG, encode as UTF-8 bytes
            if mime_type == "image/svg+xml":
                return data.encode("utf-8")
        
        return None
    
    def _get_image_dimensions(self, data: bytes, format: str) -> Optional[tuple]:
        """Get image width and height."""
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(data))
            return img.size
        except Exception:
            return None
    
    def _generate_basic_caption(self, cell: NotebookCell, index: int) -> str:
        """Generate a basic caption from the code cell."""
        # Try to extract a title from comments
        lines = cell.source.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("#") and not line.startswith("##"):
                comment = line[1:].strip()
                if len(comment) > 5 and len(comment) < 100:
                    return f"Figure {index + 1}: {comment}"
        
        # Check for title in plot commands
        title_match = re.search(r'title\s*[=\(]\s*["\']([^"\']+)["\']', cell.source)
        if title_match:
            return f"Figure {index + 1}: {title_match.group(1)}"
        
        return f"Figure {index + 1}"
    
    def is_plotting_code(self, code: str) -> bool:
        """Check if code contains plotting commands."""
        for pattern in self.compiled_patterns:
            if pattern.search(code):
                return True
        return False
    
    def identify_plot_library(self, code: str) -> Optional[str]:
        """Identify which plotting library is being used."""
        if re.search(r'import\s+matplotlib|from\s+matplotlib|plt\.', code):
            return "matplotlib"
        if re.search(r'import\s+seaborn|from\s+seaborn|sns\.', code):
            return "seaborn"
        if re.search(r'import\s+plotly|from\s+plotly|px\.|go\.', code):
            return "plotly"
        if re.search(r'import\s+bokeh|from\s+bokeh', code):
            return "bokeh"
        if re.search(r'import\s+altair|from\s+altair|alt\.', code):
            return "altair"
        return None
    
    def remove_inline_graphs(self, notebook: ParsedNotebook) -> ParsedNotebook:
        """Create a copy of notebook with inline graphs removed from outputs."""
        from copy import deepcopy
        
        new_cells = []
        for cell in notebook.cells:
            if cell.cell_type != "code":
                new_cells.append(cell)
                continue
            
            # Filter out image outputs
            new_outputs = [o for o in cell.outputs if not o.is_image]
            
            new_cell = NotebookCell(
                cell_type=cell.cell_type,
                source=cell.source,
                execution_count=cell.execution_count,
                outputs=new_outputs,
                metadata=cell.metadata,
            )
            new_cells.append(new_cell)
        
        return ParsedNotebook(
            title=notebook.title,
            cells=new_cells,
            metadata=notebook.metadata,
            nbformat=notebook.nbformat,
            nbformat_minor=notebook.nbformat_minor,
            graphs=notebook.graphs,
        )
