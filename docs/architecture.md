# Smart Notebook Print Formatter - Architecture

## Overview

The Smart Notebook Print Formatter (SNPF) is a web application that converts Jupyter notebooks and Python scripts into professionally formatted, printable reports.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Upload    │  │   Preview   │  │   Options   │             │
│  │  Component  │  │  Component  │  │  Component  │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                     API Layer                            │   │
│  │   /upload  │  /parse  │  /convert  │  /download         │   │
│  └──────┬─────────┬──────────┬─────────────┬───────────────┘   │
│         │         │          │             │                    │
│  ┌──────▼─────────▼──────────▼─────────────▼───────────────┐   │
│  │                  Processing Pipeline                     │   │
│  │                                                          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │   │
│  │  │  Parser  │──│  Graph   │──│ Formatter│──│ Exporter │ │   │
│  │  │          │  │ Extractor│  │          │  │          │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Storage Layer                          │   │
│  │   Uploads/  │  Outputs/  │  Templates/  │  Temp/        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### Parser Module

Handles reading and parsing notebook files.

- **NotebookParser**: Parses `.ipynb` files using `nbformat`
- **PythonParser**: Converts `.py` files with cell markers to notebook structure
- **MarkdownExtractor**: Processes markdown content

### Graph Handler Module

Extracts and manages visualizations.

- **GraphExtractor**: Identifies and extracts image outputs
- **GraphStorage**: Saves extracted images to disk
- **CaptionGenerator**: Creates automatic captions using code analysis

### Formatter Module

Handles content formatting and template rendering.

- **CodeHighlighter**: Syntax highlighting with Pygments
- **TemplateEngine**: Jinja2-based HTML rendering
- **PageOptimizer**: Page break optimization for print

### Exporter Module

Generates output files in various formats.

- **PDFExporter**: PDF generation using WeasyPrint
- **HTMLExporter**: Standalone HTML files with embedded resources
- **DOCXExporter**: Microsoft Word documents using python-docx

## Data Flow

1. **Upload**: User uploads notebook file
2. **Validation**: File type and content validation
3. **Parsing**: Extract cells, code, markdown, outputs
4. **Graph Extraction**: Identify and store visualizations
5. **Template Rendering**: Apply formatting template
6. **Export**: Generate output in requested format
7. **Download**: User downloads the result

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload` | POST | Upload notebook file |
| `/api/validate/{session}/{file}` | POST | Validate file |
| `/api/parse/{session}/{file}` | POST | Parse and analyze |
| `/api/preview/{session}/{file}` | GET | Get preview |
| `/api/convert` | POST | Convert notebook |
| `/api/download/{session}/{file}` | GET | Download result |
| `/api/session/{session}` | GET | Session info |
| `/api/templates` | GET | List templates |

## Session Management

- Sessions are identified by unique IDs
- Files are stored in session-specific directories
- Automatic cleanup of old sessions (default: 24 hours)

## Security Considerations

- File type validation
- Size limits (default: 50MB)
- Path traversal prevention
- No external network requests (privacy)

## Configuration

Environment variables:

```
DEBUG=false
MAX_FILE_SIZE_MB=50
CODE_THEME=monokai
DEFAULT_EXPORT_FORMAT=pdf
```
