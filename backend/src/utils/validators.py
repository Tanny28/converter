"""
Validators - Input validation for notebooks and files.
"""
import json
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

from ..config import settings


@dataclass
class ValidationResult:
    """Result of validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def __bool__(self):
        return self.is_valid


class NotebookValidator:
    """Validates notebook files and content."""
    
    # Required notebook structure
    REQUIRED_KEYS = ["cells", "metadata", "nbformat"]
    VALID_CELL_TYPES = ["code", "markdown", "raw"]
    
    def __init__(self):
        pass
    
    def validate_file(self, file_path: Path) -> ValidationResult:
        """Validate a notebook file."""
        errors = []
        warnings = []
        
        # Check file exists
        if not file_path.exists():
            return ValidationResult(False, ["File does not exist"], [])
        
        # Check extension
        if file_path.suffix.lower() not in settings.ALLOWED_EXTENSIONS:
            errors.append(f"Invalid file extension: {file_path.suffix}")
            return ValidationResult(False, errors, warnings)
        
        # Check file size
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > settings.MAX_FILE_SIZE_MB:
            errors.append(f"File too large: {size_mb:.1f}MB (max: {settings.MAX_FILE_SIZE_MB}MB)")
            return ValidationResult(False, errors, warnings)
        
        # For notebooks, validate JSON structure
        if file_path.suffix.lower() == ".ipynb":
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                return self.validate_notebook_content(content)
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON: {str(e)}")
                return ValidationResult(False, errors, warnings)
            except UnicodeDecodeError:
                errors.append("File encoding error - ensure UTF-8")
                return ValidationResult(False, errors, warnings)
        
        # For Python files, just check it's readable
        if file_path.suffix.lower() == ".py":
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    f.read()
                return ValidationResult(True, [], [])
            except Exception as e:
                errors.append(f"Cannot read file: {str(e)}")
                return ValidationResult(False, errors, warnings)
        
        return ValidationResult(True, errors, warnings)
    
    def validate_notebook_content(self, content: dict) -> ValidationResult:
        """Validate notebook JSON content."""
        errors = []
        warnings = []
        
        # Check required keys
        for key in self.REQUIRED_KEYS:
            if key not in content:
                errors.append(f"Missing required key: {key}")
        
        if errors:
            return ValidationResult(False, errors, warnings)
        
        # Validate nbformat
        nbformat = content.get("nbformat", 0)
        if nbformat < 4:
            warnings.append(f"Old notebook format (v{nbformat}) - some features may not work")
        
        # Validate cells
        cells = content.get("cells", [])
        if not cells:
            warnings.append("Notebook has no cells")
        
        for i, cell in enumerate(cells):
            cell_errors, cell_warnings = self._validate_cell(cell, i)
            errors.extend(cell_errors)
            warnings.extend(cell_warnings)
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def _validate_cell(self, cell: dict, index: int) -> Tuple[List[str], List[str]]:
        """Validate a single cell."""
        errors = []
        warnings = []
        
        # Check cell type
        cell_type = cell.get("cell_type")
        if not cell_type:
            errors.append(f"Cell {index}: missing cell_type")
        elif cell_type not in self.VALID_CELL_TYPES:
            errors.append(f"Cell {index}: invalid cell_type '{cell_type}'")
        
        # Check source
        source = cell.get("source")
        if source is None:
            errors.append(f"Cell {index}: missing source")
        elif isinstance(source, list):
            # Source can be list of strings
            pass
        elif not isinstance(source, str):
            errors.append(f"Cell {index}: source must be string or list")
        
        # Check code cell specific
        if cell_type == "code":
            outputs = cell.get("outputs")
            if outputs is not None and not isinstance(outputs, list):
                errors.append(f"Cell {index}: outputs must be a list")
            
            # Check for very large outputs
            if outputs:
                total_size = sum(len(str(o)) for o in outputs)
                if total_size > 1_000_000:  # 1MB
                    warnings.append(f"Cell {index}: large outputs ({total_size} chars)")
        
        return errors, warnings
    
    def validate_export_format(self, format: str) -> bool:
        """Validate export format."""
        return format.lower() in settings.SUPPORTED_FORMATS
    
    def validate_template_name(self, template_name: str) -> bool:
        """Validate template name (prevent path traversal)."""
        # Must not contain path separators
        if "/" in template_name or "\\" in template_name:
            return False
        
        # Must end with .html
        if not template_name.endswith(".html"):
            return False
        
        # Must not start with dot
        if template_name.startswith("."):
            return False
        
        return True
    
    def sanitize_options(self, options: dict) -> dict:
        """Sanitize export options."""
        sanitized = {}
        
        # Boolean options
        bool_keys = [
            "show_line_numbers",
            "show_execution_count",
            "include_outputs",
            "page_numbers",
            "toc",
        ]
        for key in bool_keys:
            if key in options:
                sanitized[key] = bool(options[key])
        
        # String options with validation
        if "template" in options:
            template = options["template"]
            if self.validate_template_name(template):
                sanitized["template"] = template
        
        if "page_size" in options:
            valid_sizes = ["a4", "letter", "legal", "a3", "a5"]
            if options["page_size"].lower() in valid_sizes:
                sanitized["page_size"] = options["page_size"].lower()
        
        return sanitized
