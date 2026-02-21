# API Reference

## Base URL

```
http://localhost:8000/api
```

## Endpoints

### File Upload

#### POST /upload

Upload a notebook or Python file.

**Request:**
```http
POST /api/upload HTTP/1.1
Content-Type: multipart/form-data

file: <binary>
session_id: (optional) existing session ID
```

**Response:**
```json
{
  "success": true,
  "session_id": "abc123def456",
  "filename": "notebook_20240101_120000.ipynb",
  "file_size": 12345,
  "message": "File uploaded successfully"
}
```

---

### Validation

#### POST /validate/{session_id}/{filename}

Validate an uploaded file.

**Response:**
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": ["Notebook has 0 code cells"]
}
```

---

### Parsing

#### POST /parse/{session_id}/{filename}

Parse a notebook and extract information.

**Response:**
```json
{
  "success": true,
  "title": "My Notebook",
  "cell_count": 15,
  "code_cells": 10,
  "markdown_cells": 5,
  "graph_count": 3,
  "graphs": [
    {
      "index": 0,
      "caption": "Figure 1: Sales Chart",
      "format": "png",
      "width": 800,
      "height": 600
    }
  ],
  "errors": [],
  "warnings": []
}
```

---

### Preview

#### GET /preview/{session_id}/{filename}

Get a preview of a notebook.

**Query Parameters:**
- `max_cells`: Maximum cells to include (default: 10)

**Response:**
```json
{
  "title": "My Notebook",
  "total_cells": 15,
  "cells": [
    {
      "index": 0,
      "cell_type": "markdown",
      "source_preview": "# Introduction...",
      "has_outputs": false,
      "has_graphs": false
    }
  ],
  "graphs": [...],
  "metadata": {}
}
```

---

### Conversion

#### POST /convert

Convert a notebook to PDF/HTML/DOCX.

**Request:**
```json
{
  "session_id": "abc123def456",
  "filename": "notebook.ipynb",
  "options": {
    "format": "pdf",
    "template": "academic_report.html",
    "show_line_numbers": true,
    "show_execution_count": false,
    "include_outputs": true,
    "page_numbers": true,
    "toc": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "abc123def456",
  "output_filename": "notebook.pdf",
  "output_format": "pdf",
  "output_url": "/api/download/abc123def456/notebook.pdf",
  "file_size": 245678,
  "page_count": 12,
  "graph_count": 3,
  "processing_time": 2.5,
  "errors": []
}
```

---

### Batch Conversion

#### POST /convert/batch

Convert multiple notebooks.

**Request:**
```json
{
  "session_id": "abc123def456",
  "filenames": ["notebook1.ipynb", "notebook2.ipynb"],
  "options": {
    "format": "pdf"
  }
}
```

**Response:**
```json
{
  "success": true,
  "total_files": 2,
  "successful": 2,
  "failed": 0,
  "results": [...]
}
```

---

### Download

#### GET /download/{session_id}/{filename}

Download a converted file.

**Response:** Binary file with appropriate Content-Type header

---

### Session Management

#### GET /session/{session_id}

Get session information.

**Response:**
```json
{
  "session_id": "abc123def456",
  "uploads": ["notebook.ipynb"],
  "outputs": ["notebook.pdf"],
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### DELETE /session/{session_id}

Delete a session and all its files.

---

### Configuration

#### GET /templates

List available templates.

**Response:**
```json
[
  {
    "name": "academic_report.html",
    "display_name": "Academic Report",
    "description": "Professional academic formatting"
  }
]
```

#### GET /styles

List available code highlighting styles.

---

### Maintenance

#### POST /cleanup

Clean up old session files.

**Query Parameters:**
- `max_age_hours`: Maximum age in hours (default: 24)

---

## Error Responses

All endpoints may return error responses:

```json
{
  "detail": "Error message description"
}
```

HTTP Status Codes:
- `400`: Bad Request (validation error)
- `404`: Not Found (file/session not found)
- `413`: Payload Too Large (file size exceeded)
- `500`: Internal Server Error
