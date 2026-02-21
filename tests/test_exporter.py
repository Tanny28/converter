"""
Tests for exporter module.
"""
import pytest
from pathlib import Path
import tempfile

from backend.src.exporter import HTMLExporter
from backend.src.parser.notebook_parser import ParsedNotebook, NotebookCell


class TestHTMLExporter:
    """Tests for HTMLExporter class."""
    
    def setup_method(self):
        self.exporter = HTMLExporter()
    
    def test_export_creates_file(self):
        """Test that export creates a file."""
        html = "<html><body>Test</body></html>"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.html"
            result = self.exporter.export(html, output_path)
            
            assert result.exists()
            assert result.read_text() == html
    
    def test_export_wraps_incomplete_html(self):
        """Test that incomplete HTML gets wrapped."""
        content = "<p>Just a paragraph</p>"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.html"
            self.exporter.export(content, output_path)
            
            result = output_path.read_text()
            assert "<!DOCTYPE html>" in result.lower() or "<html" in result.lower()
    
    def test_add_print_styles(self):
        """Test print styles are added."""
        html = "<html><head></head><body>Test</body></html>"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.html"
            self.exporter.export(html, output_path, {"print_styles": True})
            
            result = output_path.read_text()
            assert "@media print" in result
    
    def test_create_preview(self):
        """Test preview creation with cell limit."""
        html = '''
        <div class="cell">Cell 1</div>
        <div class="cell">Cell 2</div>
        <div class="cell">Cell 3</div>
        <div class="cell">Cell 4</div>
        <div class="cell">Cell 5</div>
        '''
        
        preview = self.exporter.create_preview(html, max_cells=3)
        
        # Should indicate truncation
        assert "Preview truncated" in preview or preview.count('<div class="cell">') <= 3
    
    def test_minify(self):
        """Test HTML minification."""
        html = '''
        <html>
            <head>
                <!-- Comment -->
            </head>
            <body>
                <p>Test</p>
            </body>
        </html>
        '''
        
        minified = self.exporter.minify(html)
        
        # Should remove comments
        assert "<!--" not in minified
        # Should be shorter
        assert len(minified) < len(html)


class TestValidators:
    """Tests for validators."""
    
    def test_validate_notebook_content(self):
        """Test notebook content validation."""
        from backend.src.utils.validators import NotebookValidator
        
        validator = NotebookValidator()
        
        # Valid notebook
        valid = {
            "cells": [
                {"cell_type": "code", "source": "x = 1", "outputs": []}
            ],
            "metadata": {},
            "nbformat": 4,
        }
        
        result = validator.validate_notebook_content(valid)
        assert result.is_valid
        
        # Invalid - missing cells
        invalid = {"metadata": {}, "nbformat": 4}
        result = validator.validate_notebook_content(invalid)
        assert not result.is_valid
    
    def test_validate_export_format(self):
        """Test export format validation."""
        from backend.src.utils.validators import NotebookValidator
        
        validator = NotebookValidator()
        
        assert validator.validate_export_format("pdf")
        assert validator.validate_export_format("html")
        assert validator.validate_export_format("docx")
        assert not validator.validate_export_format("xyz")
    
    def test_validate_template_name(self):
        """Test template name validation (path traversal prevention)."""
        from backend.src.utils.validators import NotebookValidator
        
        validator = NotebookValidator()
        
        # Valid
        assert validator.validate_template_name("academic_report.html")
        assert validator.validate_template_name("my_template.html")
        
        # Invalid - path traversal
        assert not validator.validate_template_name("../secret.html")
        assert not validator.validate_template_name("..\\secret.html")
        assert not validator.validate_template_name(".hidden.html")
        assert not validator.validate_template_name("template.txt")
