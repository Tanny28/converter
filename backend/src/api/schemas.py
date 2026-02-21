"""
API Schemas - Pydantic models for request/response validation.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ExportFormat(str, Enum):
    """Supported export formats."""
    HTML = "html"
    DOCX = "docx"


class TemplateType(str, Enum):
    """Available templates."""
    ACADEMIC = "academic_report.html"
    TECHNICAL = "technical_doc.html"
    BASIC = "base.html"


# Request Models

class ExportOptions(BaseModel):
    """Options for export."""
    format: ExportFormat = ExportFormat.DOCX
    template: TemplateType = TemplateType.ACADEMIC
    show_line_numbers: bool = True
    show_execution_count: bool = False
    include_outputs: bool = True
    page_numbers: bool = True
    toc: bool = True
    custom_css: Optional[str] = None


class ConvertRequest(BaseModel):
    """Request to convert a notebook."""
    session_id: str
    filename: str
    options: ExportOptions = Field(default_factory=ExportOptions)


class BatchConvertRequest(BaseModel):
    """Request for batch conversion."""
    session_id: str
    filenames: List[str]
    options: ExportOptions = Field(default_factory=ExportOptions)


# Response Models

class UploadResponse(BaseModel):
    """Response after file upload."""
    success: bool
    session_id: str
    filename: str
    file_size: int
    message: str = ""


class GraphInfo(BaseModel):
    """Information about an extracted graph."""
    index: int
    caption: str
    format: str
    width: Optional[int] = None
    height: Optional[int] = None


class ParseResult(BaseModel):
    """Result of parsing a notebook."""
    success: bool
    title: str
    cell_count: int
    code_cells: int
    markdown_cells: int
    graph_count: int
    graphs: List[GraphInfo] = []
    errors: List[str] = []
    warnings: List[str] = []


class ConvertResult(BaseModel):
    """Result of converting a notebook."""
    success: bool
    session_id: str
    output_filename: str
    output_format: str
    output_url: str
    file_size: int
    page_count: Optional[int] = None
    graph_count: int = 0
    processing_time: float = 0.0
    errors: List[str] = []


class BatchConvertResult(BaseModel):
    """Result of batch conversion."""
    success: bool
    total_files: int
    successful: int
    failed: int
    results: List[ConvertResult]


class SessionInfo(BaseModel):
    """Information about a session."""
    session_id: str
    uploads: List[str]
    outputs: List[str]
    created_at: Optional[str] = None


class ValidationResult(BaseModel):
    """Validation result."""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []


class TemplateInfo(BaseModel):
    """Information about available templates."""
    name: str
    display_name: str
    description: str


class StyleInfo(BaseModel):
    """Information about code styles."""
    name: str
    description: str = ""


class HealthStatus(BaseModel):
    """Health check response."""
    status: str
    version: str
    uptime: float = 0.0


# Preview Models

class CellPreview(BaseModel):
    """Preview of a notebook cell."""
    index: int
    cell_type: str
    source_preview: str
    has_outputs: bool = False
    has_graphs: bool = False


class NotebookPreview(BaseModel):
    """Preview of a notebook."""
    title: str
    total_cells: int
    cells: List[CellPreview]
    graphs: List[GraphInfo]
    metadata: Dict[str, Any] = {}
