"""
API Routes - FastAPI endpoints for the notebook formatter.
"""
import time
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse

from .schemas import (
    ExportOptions,
    ExportFormat,
    UploadResponse,
    ParseResult,
    ConvertResult,
    ConvertRequest,
    BatchConvertRequest,
    BatchConvertResult,
    SessionInfo,
    ValidationResult,
    TemplateInfo,
    StyleInfo,
    NotebookPreview,
    CellPreview,
    GraphInfo,
    URLUploadRequest,
)
from ..config import settings
from ..parser import NotebookParser, PythonParser
from ..graph_handler import GraphExtractor, GraphStorage, CaptionGenerator
from ..formatter import TemplateEngine, CodeHighlighter, PageOptimizer
from ..exporter import HTMLExporter, DOCXExporter
from ..utils import FileHandler, NotebookValidator, NotebookFetcher


router = APIRouter()

# Initialize services
file_handler = FileHandler()
validator = NotebookValidator()
notebook_fetcher = NotebookFetcher()
notebook_parser = NotebookParser()
python_parser = PythonParser()
graph_extractor = GraphExtractor()
graph_storage = GraphStorage()
caption_generator = CaptionGenerator()
template_engine = TemplateEngine()
code_highlighter = CodeHighlighter()
page_optimizer = PageOptimizer()
html_exporter = HTMLExporter()
docx_exporter = DOCXExporter()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = None,
):
    """Upload a notebook or Python file."""
    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Read file content
    content = await file.read()
    
    # Check file size
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Save file
    file_path, session_id = file_handler.save_upload_sync(
        content, file.filename, session_id
    )
    
    return UploadResponse(
        success=True,
        session_id=session_id,
        filename=file_path.name,
        file_size=len(content),
        message="File uploaded successfully"
    )


@router.post("/upload-url", response_model=UploadResponse)
async def upload_from_url(request: URLUploadRequest):
    """
    Upload a notebook from a URL (Google Colab, GitHub, etc.).
    
    Supported sources:
    - Google Colab: colab.research.google.com/drive/FILE_ID
    - GitHub: github.com/user/repo/blob/branch/path/to/notebook.ipynb
    - GitHub Gists: gist.github.com/user/gist_id
    - Direct .ipynb URLs
    """
    try:
        # Fetch notebook from URL
        content, filename = await notebook_fetcher.fetch(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch notebook: {str(e)}"
        )
    
    # Check file size
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"Notebook too large. Max size: {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Save file
    file_path, session_id = file_handler.save_upload_sync(
        content, filename, request.session_id
    )
    
    return UploadResponse(
        success=True,
        session_id=session_id,
        filename=file_path.name,
        file_size=len(content),
        message=f"Notebook fetched from URL successfully"
    )


@router.post("/validate/{session_id}/{filename}", response_model=ValidationResult)
async def validate_file(session_id: str, filename: str):
    """Validate an uploaded file."""
    file_path = file_handler.get_file(session_id, filename, "upload")
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    result = validator.validate_file(file_path)
    
    return ValidationResult(
        is_valid=result.is_valid,
        errors=result.errors,
        warnings=result.warnings
    )


@router.post("/parse/{session_id}/{filename}", response_model=ParseResult)
async def parse_file(session_id: str, filename: str):
    """Parse a notebook and extract information."""
    file_path = file_handler.get_file(session_id, filename, "upload")
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Parse based on file type
        if file_path.suffix.lower() == ".ipynb":
            notebook = notebook_parser.parse_file(file_path)
        else:
            notebook = python_parser.parse_file(file_path)
        
        # Extract graphs
        graphs = graph_extractor.extract_all(notebook)
        
        # Generate captions
        captions = caption_generator.generate_all(graphs)
        
        return ParseResult(
            success=True,
            title=notebook.title,
            cell_count=len(notebook.cells),
            code_cells=len(notebook.code_cells),
            markdown_cells=len(notebook.markdown_cells),
            graph_count=len(graphs),
            graphs=[
                GraphInfo(
                    index=g.index,
                    caption=c.text,
                    format=g.format,
                    width=g.width,
                    height=g.height,
                )
                for g, c in zip(graphs, captions)
            ],
        )
    except Exception as e:
        return ParseResult(
            success=False,
            title="",
            cell_count=0,
            code_cells=0,
            markdown_cells=0,
            graph_count=0,
            errors=[str(e)],
        )


@router.get("/preview/{session_id}/{filename}", response_model=NotebookPreview)
async def get_preview(session_id: str, filename: str, max_cells: int = 10):
    """Get a preview of a notebook."""
    file_path = file_handler.get_file(session_id, filename, "upload")
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Parse
        if file_path.suffix.lower() == ".ipynb":
            notebook = notebook_parser.parse_file(file_path)
        else:
            notebook = python_parser.parse_file(file_path)
        
        # Extract graphs
        graphs = graph_extractor.extract_all(notebook)
        captions = caption_generator.generate_all(graphs)
        
        # Create cell previews
        cells = []
        for i, cell in enumerate(notebook.cells[:max_cells]):
            source_preview = cell.source[:200] + "..." if len(cell.source) > 200 else cell.source
            cells.append(CellPreview(
                index=i,
                cell_type=cell.cell_type,
                source_preview=source_preview,
                has_outputs=len(cell.outputs) > 0 if hasattr(cell, 'outputs') else False,
                has_graphs=any(o.is_image for o in cell.outputs) if hasattr(cell, 'outputs') else False,
            ))
        
        return NotebookPreview(
            title=notebook.title,
            total_cells=len(notebook.cells),
            cells=cells,
            graphs=[
                GraphInfo(index=g.index, caption=c.text, format=g.format)
                for g, c in zip(graphs, captions)
            ],
            metadata=notebook.metadata,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/convert", response_model=ConvertResult)
async def convert_notebook(request: ConvertRequest):
    """Convert a notebook to the specified format."""
    start_time = time.time()
    
    # Get file
    file_path = file_handler.get_file(request.session_id, request.filename, "upload")
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Parse notebook
        if file_path.suffix.lower() == ".ipynb":
            notebook = notebook_parser.parse_file(file_path)
        else:
            notebook = python_parser.parse_file(file_path)
        
        # Extract and store graphs
        graphs = graph_extractor.extract_all(notebook)
        stored_graphs = graph_storage.store_graphs(graphs, request.session_id)
        
        # Update captions
        captions = caption_generator.generate_all(graphs)
        for sg, caption in zip(stored_graphs, captions):
            sg.caption = caption.text
        
        # Remove inline graphs
        notebook = graph_extractor.remove_inline_graphs(notebook)
        
        # Render with template
        html_content = template_engine.render(
            notebook,
            template_name=request.options.template.value,
            graphs=stored_graphs,
            options=request.options.model_dump(),
        )
        
        # Optimize for printing
        html_content = page_optimizer.add_page_numbers(html_content)
        
        # Get output path
        output_path = file_handler.get_output_path(
            request.session_id,
            request.filename,
            request.options.format.value,
        )
        
        # Export based on format
        if request.options.format == ExportFormat.HTML:
            html_exporter.export_standalone(html_content, output_path, stored_graphs)
        elif request.options.format == ExportFormat.DOCX:
            docx_exporter.export(notebook, output_path, stored_graphs, request.options.model_dump())
        
        processing_time = time.time() - start_time
        
        return ConvertResult(
            success=True,
            session_id=request.session_id,
            output_filename=output_path.name,
            output_format=request.options.format.value,
            output_url=f"/download/{request.session_id}/{output_path.name}",
            file_size=output_path.stat().st_size,
            graph_count=len(graphs),
            processing_time=processing_time,
        )
    except Exception as e:
        return ConvertResult(
            success=False,
            session_id=request.session_id,
            output_filename="",
            output_format=request.options.format.value,
            output_url="",
            file_size=0,
            errors=[str(e)],
            processing_time=time.time() - start_time,
        )


@router.post("/convert/batch", response_model=BatchConvertResult)
async def batch_convert(request: BatchConvertRequest):
    """Convert multiple notebooks."""
    results = []
    successful = 0
    failed = 0
    
    for filename in request.filenames:
        convert_request = ConvertRequest(
            session_id=request.session_id,
            filename=filename,
            options=request.options,
        )
        result = await convert_notebook(convert_request)
        results.append(result)
        
        if result.success:
            successful += 1
        else:
            failed += 1
    
    return BatchConvertResult(
        success=failed == 0,
        total_files=len(request.filenames),
        successful=successful,
        failed=failed,
        results=results,
    )


@router.get("/download/{session_id}/{filename}")
async def download_file(session_id: str, filename: str):
    """Download a converted file."""
    file_path = file_handler.get_file(session_id, filename, "output")
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type
    ext = file_path.suffix.lower()
    media_types = {
        ".pdf": "application/pdf",
        ".html": "text/html",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_types.get(ext, "application/octet-stream"),
    )


@router.get("/session/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """Get information about a session."""
    files = file_handler.get_session_files(session_id)
    
    return SessionInfo(
        session_id=session_id,
        uploads=files["uploads"],
        outputs=files["outputs"],
    )


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and all its files."""
    deleted = file_handler.delete_session(session_id)
    graph_storage.delete_session(session_id)
    
    if deleted:
        return {"success": True, "message": "Session deleted"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/templates", response_model=List[TemplateInfo])
async def list_templates():
    """List available templates."""
    return [
        TemplateInfo(
            name="academic_report.html",
            display_name="Academic Report",
            description="Professional academic formatting with table of contents",
        ),
        TemplateInfo(
            name="technical_doc.html",
            display_name="Technical Documentation",
            description="Modern technical documentation style",
        ),
        TemplateInfo(
            name="base.html",
            display_name="Basic",
            description="Simple, clean formatting",
        ),
    ]


@router.get("/styles", response_model=List[StyleInfo])
async def list_code_styles():
    """List available code highlighting styles."""
    styles = CodeHighlighter.get_available_styles()
    return [StyleInfo(name=s) for s in styles[:20]]  # Limit to first 20


@router.post("/cleanup")
async def cleanup_old_files(background_tasks: BackgroundTasks, max_age_hours: int = 24):
    """Clean up old session files."""
    def cleanup():
        file_handler.cleanup_old_sessions(max_age_hours)
        graph_storage.cleanup_old_sessions(max_age_hours)
    
    background_tasks.add_task(cleanup)
    return {"message": "Cleanup scheduled"}


@router.get("/capabilities")
async def get_capabilities():
    """Get system capabilities and available features."""
    return {
        "html_export": True,
        "docx_export": True,
        "formats": {
            "html": {"available": True, "message": None},
            "docx": {"available": True, "message": None},
        },
    }
