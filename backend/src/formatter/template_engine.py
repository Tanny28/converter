"""
Template Engine - Renders notebooks using HTML templates.
"""
from pathlib import Path
from typing import Dict, Any, Optional, List
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime
import markdown

from ..config import settings
from ..parser.notebook_parser import ParsedNotebook, NotebookCell
from ..graph_handler.graph_storage import StoredGraph
from .code_highlighter import CodeHighlighter


class TemplateEngine:
    """Renders parsed notebooks using Jinja2 templates."""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or settings.TEMPLATES_DIR
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        
        # Add custom filters
        self._add_filters()
        
        # Initialize components
        self.highlighter = CodeHighlighter(settings.CODE_THEME)
        self.md = markdown.Markdown(
            extensions=[
                "fenced_code",
                "tables",
                "toc",
                "nl2br",
                "sane_lists",
            ]
        )
        
        # Create default templates if they don't exist
        self._ensure_default_templates()
    
    def _add_filters(self):
        """Add custom Jinja2 filters."""
        self.env.filters["markdown"] = self._render_markdown
        self.env.filters["highlight"] = self._highlight_code
        self.env.filters["truncate_lines"] = self._truncate_lines
    
    def _render_markdown(self, text: str) -> str:
        """Render markdown to HTML."""
        self.md.reset()
        return self.md.convert(text)
    
    def _highlight_code(self, code: str, language: str = "python") -> str:
        """Highlight code."""
        return self.highlighter.highlight_code(code, language)
    
    def _truncate_lines(self, text: str, max_lines: int = 50) -> str:
        """Truncate text to max lines."""
        lines = text.split("\n")
        if len(lines) > max_lines:
            return "\n".join(lines[:max_lines]) + f"\n... ({len(lines) - max_lines} more lines)"
        return text
    
    def render(
        self,
        notebook: ParsedNotebook,
        template_name: str = "academic_report.html",
        graphs: Optional[List[StoredGraph]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Render a notebook using a template."""
        options = options or {}
        
        # Process cells
        processed_cells = self._process_cells(notebook.cells)
        
        # Prepare context
        context = {
            "notebook": notebook,
            "title": notebook.title,
            "cells": processed_cells,
            "graphs": graphs or [],
            "metadata": notebook.metadata,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "css": self.highlighter.get_css(),
            "options": {
                "show_line_numbers": options.get("show_line_numbers", True),
                "show_execution_count": options.get("show_execution_count", False),
                "include_outputs": options.get("include_outputs", True),
                "page_numbers": options.get("page_numbers", True),
                "toc": options.get("toc", True),
            },
        }
        
        # Load and render template
        try:
            template = self.env.get_template(template_name)
        except Exception:
            template = self.env.get_template("base.html")
        
        return template.render(**context)
    
    def _process_cells(self, cells: List[NotebookCell]) -> List[Dict[str, Any]]:
        """Process cells for rendering."""
        processed = []
        
        for i, cell in enumerate(cells):
            proc = {
                "index": i,
                "type": cell.cell_type,
                "source": cell.source,
                "execution_count": cell.execution_count,
            }
            
            if cell.cell_type == "markdown":
                proc["html"] = self._render_markdown(cell.source)
            elif cell.cell_type == "code":
                proc["highlighted"] = self.highlighter.highlight_code(cell.source)
                proc["outputs"] = self._process_outputs(cell.outputs)
            
            processed.append(proc)
        
        return processed
    
    def _process_outputs(self, outputs: list) -> List[Dict[str, Any]]:
        """Process cell outputs for rendering."""
        processed = []
        
        for output in outputs:
            proc = {"type": output.output_type}
            
            if output.text:
                proc["text"] = output.text
                proc["html"] = f"<pre class='output'>{self._escape_html(output.text)}</pre>"
            
            if output.is_image:
                # Skip images - they go in figures section
                proc["is_image"] = True
                proc["skipped"] = True
            
            processed.append(proc)
        
        return processed
    
    def _escape_html(self, text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
    
    def _ensure_default_templates(self):
        """Create default templates if they don't exist."""
        base_template = self.templates_dir / "base.html"
        if not base_template.exists():
            base_template.write_text(self._get_base_template())
        
        academic_template = self.templates_dir / "academic_report.html"
        if not academic_template.exists():
            academic_template.write_text(self._get_academic_template())
        
        technical_template = self.templates_dir / "technical_doc.html"
        if not technical_template.exists():
            technical_template.write_text(self._get_technical_template())
    
    def _get_base_template(self) -> str:
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        {{ css | safe }}
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
            color: #333;
        }
        
        h1, h2, h3 { margin-top: 2rem; }
        
        .output {
            background: #f5f5f5;
            padding: 1rem;
            border-left: 3px solid #4CAF50;
            margin: 0.5rem 0;
            overflow-x: auto;
        }
        
        .cell { margin: 1.5rem 0; }
        
        .markdown-cell { }
        
        .code-cell {
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
        }
        
        @media print {
            body { max-width: none; padding: 0; }
            .code-cell { page-break-inside: avoid; }
        }
    </style>
    {% block extra_styles %}{% endblock %}
</head>
<body>
    {% block header %}
    <header>
        <h1>{{ title }}</h1>
        <p class="generated">Generated: {{ generated_at }}</p>
    </header>
    {% endblock %}
    
    {% block content %}
    {% for cell in cells %}
    <div class="cell {{ cell.type }}-cell">
        {% if cell.type == "markdown" %}
        {{ cell.html | safe }}
        {% elif cell.type == "code" %}
        <div class="code-content">
            {{ cell.highlighted | safe }}
        </div>
        {% if options.include_outputs %}
        {% for output in cell.outputs %}
        {% if not output.skipped %}
        {{ output.html | safe }}
        {% endif %}
        {% endfor %}
        {% endif %}
        {% endif %}
    </div>
    {% endfor %}
    {% endblock %}
    
    {% block figures %}
    {% if graphs %}
    <section class="figures-section">
        <h2>Figures</h2>
        {% for graph in graphs %}
        <figure>
            <img src="{{ graph.file_path }}" alt="{{ graph.caption }}">
            <figcaption>{{ graph.caption }}</figcaption>
        </figure>
        {% endfor %}
    </section>
    {% endif %}
    {% endblock %}
    
    {% block footer %}{% endblock %}
</body>
</html>'''
    
    def _get_academic_template(self) -> str:
        return '''{% extends "base.html" %}

{% block extra_styles %}
<style>
    body {
        font-family: "Times New Roman", Times, serif;
        font-size: 12pt;
        text-align: justify;
    }
    
    h1 { text-align: center; margin-bottom: 0.5rem; }
    
    .abstract {
        font-style: italic;
        margin: 2rem 3rem;
        padding: 1rem;
        border-left: 3px solid #333;
    }
    
    .toc {
        margin: 2rem 0;
        padding: 1rem;
        background: #f9f9f9;
    }
    
    .toc h2 { margin-top: 0; }
    .toc ul { list-style: none; padding-left: 1rem; }
    .toc a { text-decoration: none; color: #333; }
    
    figure {
        text-align: center;
        margin: 2rem 0;
        page-break-inside: avoid;
    }
    
    figure img {
        max-width: 100%;
        height: auto;
    }
    
    figcaption {
        font-style: italic;
        margin-top: 0.5rem;
    }
    
    .page-break { page-break-after: always; }
    
    @media print {
        .figures-section { page-break-before: always; }
    }
</style>
{% endblock %}

{% block header %}
<header class="title-page">
    <h1>{{ title }}</h1>
    {% if notebook.metadata.authors %}
    <p class="authors">{{ notebook.metadata.authors | join(", ") }}</p>
    {% endif %}
    <p class="date">{{ generated_at }}</p>
</header>
{% endblock %}

{% block content %}
{% if options.toc %}
<nav class="toc">
    <h2>Table of Contents</h2>
    <ul>
    {% for cell in cells if cell.type == "markdown" and "h2" in cell.html or "h3" in cell.html %}
        <li><a href="#section-{{ loop.index }}">Section {{ loop.index }}</a></li>
    {% endfor %}
        <li><a href="#figures">Figures</a></li>
    </ul>
</nav>
{% endif %}

{{ super() }}
{% endblock %}

{% block figures %}
{% if graphs %}
<section class="figures-section" id="figures">
    <h2>Figures</h2>
    {% for graph in graphs %}
    <figure id="figure-{{ loop.index }}">
        <img src="{{ graph.file_path }}" alt="{{ graph.caption }}">
        <figcaption>{{ graph.caption }}</figcaption>
    </figure>
    {% endfor %}
</section>
{% endif %}
{% endblock %}'''
    
    def _get_technical_template(self) -> str:
        return '''{% extends "base.html" %}

{% block extra_styles %}
<style>
    body {
        font-family: "Fira Sans", "Segoe UI", sans-serif;
        background: #fafafa;
    }
    
    .code-cell {
        background: #1e1e1e;
        border-radius: 8px;
    }
    
    .code-cell .highlight {
        background: transparent;
    }
    
    .output {
        background: #2d2d2d;
        color: #f0f0f0;
        border-left-color: #4CAF50;
    }
    
    figure {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
{% endblock %}'''
    
    def list_templates(self) -> List[str]:
        """List available templates."""
        return [f.name for f in self.templates_dir.glob("*.html")]
