"""
Tests for notebook parser module.
"""
import pytest
from pathlib import Path

from backend.src.parser import NotebookParser, PythonParser
from backend.src.parser.notebook_parser import ParsedNotebook, NotebookCell


class TestNotebookParser:
    """Tests for NotebookParser class."""
    
    def setup_method(self):
        self.parser = NotebookParser()
    
    def test_parse_content_basic(self):
        """Test parsing basic notebook content."""
        content = '''{
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": ["# Test Notebook"]
                },
                {
                    "cell_type": "code",
                    "metadata": {},
                    "source": ["print('Hello, World!')"],
                    "execution_count": 1,
                    "outputs": []
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 5
        }'''
        
        result = self.parser.parse_content(content, "test")
        
        assert isinstance(result, ParsedNotebook)
        assert result.title == "Test Notebook"
        assert len(result.cells) == 2
        assert result.cells[0].cell_type == "markdown"
        assert result.cells[1].cell_type == "code"
    
    def test_extract_title_from_heading(self):
        """Test title extraction from markdown heading."""
        content = '''{
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": ["## Introduction to Python"]
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5
        }'''
        
        result = self.parser.parse_content(content)
        assert result.title == "Introduction to Python"
    
    def test_code_cells_property(self):
        """Test code cells filtering."""
        content = '''{
            "cells": [
                {"cell_type": "markdown", "metadata": {}, "source": ["text"]},
                {"cell_type": "code", "metadata": {}, "source": ["code1"], "outputs": []},
                {"cell_type": "code", "metadata": {}, "source": ["code2"], "outputs": []}
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5
        }'''
        
        result = self.parser.parse_content(content)
        assert len(result.code_cells) == 2
        assert len(result.markdown_cells) == 1
    
    def test_parse_with_image_output(self):
        """Test parsing notebook with image outputs."""
        content = '''{
            "cells": [
                {
                    "cell_type": "code",
                    "metadata": {},
                    "source": ["import matplotlib.pyplot as plt\\nplt.plot([1,2,3])"],
                    "outputs": [
                        {
                            "output_type": "display_data",
                            "data": {
                                "image/png": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                                "text/plain": ["<Figure>"]
                            },
                            "metadata": {}
                        }
                    ],
                    "execution_count": 1
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5
        }'''
        
        result = self.parser.parse_content(content)
        assert len(result.cells) == 1
        assert len(result.cells[0].outputs) == 1
        assert result.cells[0].outputs[0].is_image
        assert result.cells[0].outputs[0].mime_type == "image/png"


class TestPythonParser:
    """Tests for PythonParser class."""
    
    def setup_method(self):
        self.parser = PythonParser()
    
    def test_parse_simple_script(self):
        """Test parsing a simple Python script."""
        content = '''"""
My Python Script
"""
import os

def hello():
    print("Hello, World!")

hello()
'''
        
        result = self.parser.parse_content(content, "script")
        
        assert isinstance(result, ParsedNotebook)
        assert len(result.cells) > 0
    
    def test_extract_title_from_docstring(self):
        """Test title extraction from module docstring."""
        content = '''"""
Data Analysis Script
Performs various analyses.
"""
import pandas as pd
'''
        
        result = self.parser.parse_content(content)
        assert "Data Analysis Script" in result.title
    
    def test_parse_with_cell_markers(self):
        """Test parsing script with cell markers."""
        content = '''# %%
import numpy as np

# %%
x = np.array([1, 2, 3])

# %% md
# This is a markdown section
# With multiple lines

# %%
print(x)
'''
        
        result = self.parser.parse_content(content)
        # Should have multiple cells
        assert len(result.cells) >= 3
    
    def test_extract_imports(self):
        """Test import extraction."""
        content = '''import os
import sys
from pathlib import Path
from typing import List, Dict
'''
        
        imports = self.parser.extract_imports(content)
        
        assert len(imports) == 4
        assert "import os" in imports
        assert "from pathlib import Path" in imports
    
    def test_extract_functions(self):
        """Test function extraction."""
        content = '''
def greet(name):
    """Say hello to someone."""
    return f"Hello, {name}!"

def calculate(x, y):
    return x + y
'''
        
        functions = self.parser.extract_functions(content)
        
        assert len(functions) == 2
        assert functions[0][0] == "greet"
        assert "Say hello" in functions[0][1]
