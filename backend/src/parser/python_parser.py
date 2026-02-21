"""
Python Script Parser - Converts .py files into notebook-like structure.
"""
import re
import ast
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass, field

from .notebook_parser import NotebookCell, ParsedNotebook


@dataclass
class CodeBlock:
    """Represents a block of code with optional docstring."""
    code: str
    docstring: Optional[str] = None
    start_line: int = 0
    end_line: int = 0
    block_type: str = "code"  # 'code', 'import', 'class', 'function'


class PythonParser:
    """Parser for Python (.py) files."""
    
    # Regex patterns
    DOCSTRING_PATTERN = re.compile(r'^[\s]*["\'][\s\S]*?["\'][\s]*$|^[\s]*"""[\s\S]*?"""[\s]*$|^[\s]*\'\'\'[\s\S]*?\'\'\'[\s]*$', re.MULTILINE)
    COMMENT_BLOCK_PATTERN = re.compile(r'^#\s*(?:%%|<markdown>|md:)(.*?)(?=^[^#]|\Z)', re.MULTILINE | re.DOTALL)
    SECTION_COMMENT_PATTERN = re.compile(r'^#\s*[-=]{3,}\s*$|^#\s*\[.*\]\s*$', re.MULTILINE)
    
    def __init__(self):
        pass
    
    def parse_file(self, file_path: Path) -> ParsedNotebook:
        """Parse a Python file from disk."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return self.parse_content(content, file_path.stem)
    
    def parse_content(self, content: str, title: str = "Untitled") -> ParsedNotebook:
        """Parse Python content into a notebook-like structure."""
        cells = []
        blocks = self._split_into_blocks(content)
        
        for block in blocks:
            if block.block_type == "markdown":
                cells.append(NotebookCell(
                    cell_type="markdown",
                    source=block.code,
                ))
            else:
                # Add docstring as markdown if present
                if block.docstring:
                    cells.append(NotebookCell(
                        cell_type="markdown",
                        source=block.docstring,
                    ))
                
                cells.append(NotebookCell(
                    cell_type="code",
                    source=block.code,
                ))
        
        # Extract title from module docstring or first class/function
        extracted_title = self._extract_title(content) or title
        
        return ParsedNotebook(
            title=extracted_title,
            cells=cells,
            metadata={"language": "python", "source_type": "script"},
            nbformat=4,
            nbformat_minor=5,
        )
    
    def _split_into_blocks(self, content: str) -> List[CodeBlock]:
        """Split Python content into logical blocks."""
        blocks = []
        lines = content.split("\n")
        current_block = []
        current_start = 0
        in_markdown_comment = False
        markdown_content = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Check for markdown comment blocks (# %% md or # <markdown>)
            if stripped.startswith("# %% md") or stripped.startswith("# <markdown>"):
                # Save current code block
                if current_block:
                    blocks.append(CodeBlock(
                        code="\n".join(current_block),
                        start_line=current_start,
                        end_line=i - 1,
                    ))
                    current_block = []
                
                in_markdown_comment = True
                markdown_content = []
                i += 1
                continue
            
            # Check for cell separator (# %%)
            if stripped.startswith("# %%") and not stripped.startswith("# %% md"):
                # End markdown block if active
                if in_markdown_comment:
                    blocks.append(CodeBlock(
                        code="\n".join(markdown_content),
                        block_type="markdown",
                        start_line=current_start,
                        end_line=i - 1,
                    ))
                    in_markdown_comment = False
                    markdown_content = []
                
                # Save current code block
                if current_block:
                    blocks.append(CodeBlock(
                        code="\n".join(current_block),
                        start_line=current_start,
                        end_line=i - 1,
                    ))
                    current_block = []
                
                current_start = i + 1
                i += 1
                continue
            
            if in_markdown_comment:
                # Remove leading # for markdown content
                if stripped.startswith("#"):
                    markdown_content.append(stripped[1:].lstrip())
                else:
                    # Non-comment line ends markdown block
                    blocks.append(CodeBlock(
                        code="\n".join(markdown_content),
                        block_type="markdown",
                        start_line=current_start,
                        end_line=i - 1,
                    ))
                    in_markdown_comment = False
                    markdown_content = []
                    current_start = i
                    current_block = [line]
            else:
                if not current_block:
                    current_start = i
                current_block.append(line)
            
            i += 1
        
        # Handle remaining content
        if in_markdown_comment and markdown_content:
            blocks.append(CodeBlock(
                code="\n".join(markdown_content),
                block_type="markdown",
                start_line=current_start,
                end_line=len(lines) - 1,
            ))
        elif current_block:
            blocks.append(CodeBlock(
                code="\n".join(current_block),
                start_line=current_start,
                end_line=len(lines) - 1,
            ))
        
        return blocks
    
    def _extract_title(self, content: str) -> Optional[str]:
        """Extract title from module docstring or first definition."""
        try:
            tree = ast.parse(content)
            
            # Check for module docstring
            if (tree.body and 
                isinstance(tree.body[0], ast.Expr) and 
                isinstance(tree.body[0].value, ast.Constant) and
                isinstance(tree.body[0].value.value, str)):
                docstring = tree.body[0].value.value
                # Get first line of docstring as title
                first_line = docstring.strip().split("\n")[0]
                return first_line[:100]  # Limit length
            
            # Look for first class or function
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    return f"Class: {node.name}"
                elif isinstance(node, ast.FunctionDef):
                    return f"Script: {node.name}"
        
        except SyntaxError:
            pass
        
        return None
    
    def extract_imports(self, content: str) -> List[str]:
        """Extract all import statements from Python code."""
        imports = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    names = ", ".join(alias.name for alias in node.names)
                    imports.append(f"from {module} import {names}")
        except SyntaxError:
            pass
        return imports
    
    def extract_functions(self, content: str) -> List[Tuple[str, Optional[str]]]:
        """Extract function names and their docstrings."""
        functions = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    docstring = ast.get_docstring(node)
                    functions.append((node.name, docstring))
        except SyntaxError:
            pass
        return functions
