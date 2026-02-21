"""
Jupyter Notebook Parser - Extracts cells, code, markdown, and outputs from .ipynb files.
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import nbformat
from nbformat import NotebookNode


@dataclass
class CellOutput:
    """Represents a cell output."""
    output_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    text: Optional[str] = None
    is_image: bool = False
    image_data: Optional[bytes] = None
    mime_type: Optional[str] = None


@dataclass
class NotebookCell:
    """Represents a single notebook cell."""
    cell_type: str  # 'code', 'markdown', 'raw'
    source: str
    execution_count: Optional[int] = None
    outputs: List[CellOutput] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedNotebook:
    """Represents a fully parsed notebook."""
    title: str
    cells: List[NotebookCell]
    metadata: Dict[str, Any]
    nbformat: int
    nbformat_minor: int
    graphs: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def code_cells(self) -> List[NotebookCell]:
        return [c for c in self.cells if c.cell_type == "code"]
    
    @property
    def markdown_cells(self) -> List[NotebookCell]:
        return [c for c in self.cells if c.cell_type == "markdown"]


class NotebookParser:
    """Parser for Jupyter Notebook (.ipynb) files."""
    
    IMAGE_MIME_TYPES = {
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/svg+xml",
    }
    
    def __init__(self):
        self.current_notebook: Optional[NotebookNode] = None
    
    def parse_file(self, file_path: Path) -> ParsedNotebook:
        """Parse a notebook file from disk."""
        with open(file_path, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)
        return self._parse_notebook(notebook, file_path.stem)
    
    def parse_content(self, content: str, title: str = "Untitled") -> ParsedNotebook:
        """Parse notebook content from a string."""
        notebook = nbformat.reads(content, as_version=4)
        return self._parse_notebook(notebook, title)
    
    def _parse_notebook(self, notebook: NotebookNode, title: str) -> ParsedNotebook:
        """Internal method to parse a notebook node."""
        self.current_notebook = notebook
        
        cells = []
        graphs = []
        graph_index = 0
        
        for idx, cell in enumerate(notebook.cells):
            parsed_cell, cell_graphs = self._parse_cell(cell, idx, graph_index)
            cells.append(parsed_cell)
            graphs.extend(cell_graphs)
            graph_index += len(cell_graphs)
        
        # Try to extract title from first markdown cell
        extracted_title = self._extract_title(cells) or title
        
        return ParsedNotebook(
            title=extracted_title,
            cells=cells,
            metadata=dict(notebook.metadata),
            nbformat=notebook.nbformat,
            nbformat_minor=notebook.nbformat_minor,
            graphs=graphs,
        )
    
    def _parse_cell(self, cell: NotebookNode, cell_index: int, graph_index: int) -> tuple:
        """Parse a single cell and extract outputs."""
        outputs = []
        graphs = []
        
        if cell.cell_type == "code" and hasattr(cell, "outputs"):
            for output in cell.outputs:
                parsed_output, graph = self._parse_output(output, cell_index, graph_index + len(graphs))
                outputs.append(parsed_output)
                if graph:
                    graphs.append(graph)
        
        return NotebookCell(
            cell_type=cell.cell_type,
            source=cell.source,
            execution_count=getattr(cell, "execution_count", None),
            outputs=outputs,
            metadata=dict(cell.metadata) if cell.metadata else {},
        ), graphs
    
    def _parse_output(self, output: NotebookNode, cell_index: int, graph_index: int) -> tuple:
        """Parse a cell output and identify if it's a graph."""
        output_type = output.output_type
        graph = None
        
        parsed = CellOutput(output_type=output_type)
        
        if output_type == "stream":
            parsed.text = output.get("text", "")
        
        elif output_type == "execute_result" or output_type == "display_data":
            data = output.get("data", {})
            parsed.data = data
            
            # Check for image outputs (graphs)
            for mime_type in self.IMAGE_MIME_TYPES:
                if mime_type in data:
                    parsed.is_image = True
                    parsed.mime_type = mime_type
                    parsed.image_data = data[mime_type]
                    
                    # Create graph entry
                    graph = {
                        "index": graph_index,
                        "cell_index": cell_index,
                        "mime_type": mime_type,
                        "data": data[mime_type],
                        "caption": f"Figure {graph_index + 1}",
                    }
                    break
            
            if "text/plain" in data and not parsed.is_image:
                parsed.text = data["text/plain"]
        
        elif output_type == "error":
            parsed.text = "\n".join(output.get("traceback", []))
        
        return parsed, graph
    
    def _extract_title(self, cells: List[NotebookCell]) -> Optional[str]:
        """Extract title from first markdown heading."""
        for cell in cells:
            if cell.cell_type == "markdown":
                lines = cell.source.strip().split("\n")
                for line in lines:
                    line = line.strip()
                    if line.startswith("# "):
                        return line[2:].strip()
                    elif line.startswith("## "):
                        return line[3:].strip()
                break
        return None
    
    def get_all_code(self, notebook: ParsedNotebook) -> str:
        """Get all code from a notebook as a single string."""
        return "\n\n".join(cell.source for cell in notebook.code_cells)
    
    def get_all_markdown(self, notebook: ParsedNotebook) -> str:
        """Get all markdown from a notebook as a single string."""
        return "\n\n".join(cell.source for cell in notebook.markdown_cells)
