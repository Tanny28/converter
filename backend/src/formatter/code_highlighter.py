"""
Code Highlighter - Syntax highlighting for code blocks.
"""
from typing import Optional, Dict
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer, PythonLexer
from pygments.formatters import HtmlFormatter, Terminal256Formatter
from pygments.styles import get_style_by_name, get_all_styles
from pygments.util import ClassNotFound


class CodeHighlighter:
    """Handles syntax highlighting for code blocks."""
    
    # Common language aliases
    LANGUAGE_ALIASES = {
        "py": "python",
        "python3": "python",
        "js": "javascript",
        "ts": "typescript",
        "rb": "ruby",
        "sh": "bash",
        "shell": "bash",
        "yml": "yaml",
        "md": "markdown",
    }
    
    def __init__(self, style: str = "monokai"):
        self.style = style
        self._formatter_cache: Dict[str, HtmlFormatter] = {}
    
    def highlight_code(
        self,
        code: str,
        language: str = "python",
        line_numbers: bool = True,
        wrap_code: bool = True,
    ) -> str:
        """Highlight code and return HTML."""
        # Normalize language name
        language = self.LANGUAGE_ALIASES.get(language.lower(), language.lower())
        
        # Get lexer
        try:
            lexer = get_lexer_by_name(language)
        except ClassNotFound:
            try:
                lexer = guess_lexer(code)
            except ClassNotFound:
                lexer = PythonLexer()
        
        # Get or create formatter
        formatter = self._get_formatter(line_numbers, wrap_code)
        
        return highlight(code, lexer, formatter)
    
    def _get_formatter(self, line_numbers: bool, wrap_code: bool) -> HtmlFormatter:
        """Get a cached HTML formatter."""
        cache_key = f"{self.style}_{line_numbers}_{wrap_code}"
        
        if cache_key not in self._formatter_cache:
            self._formatter_cache[cache_key] = HtmlFormatter(
                style=self.style,
                linenos="table" if line_numbers else False,
                cssclass="highlight",
                wrapcode=wrap_code,
                lineanchors="line" if line_numbers else None,
                anchorlinenos=line_numbers,
            )
        
        return self._formatter_cache[cache_key]
    
    def get_css(self, extra_css: str = "") -> str:
        """Get CSS styles for the highlighted code."""
        formatter = self._get_formatter(True, True)
        base_css = formatter.get_style_defs('.highlight')
        
        # Add custom styles for better print formatting
        custom_css = """
        .highlight {
            background: #f8f8f8;
            border-radius: 4px;
            padding: 0;
            margin: 1em 0;
            overflow-x: auto;
            font-size: 0.9em;
        }
        
        .highlight pre {
            margin: 0;
            padding: 1em;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .highlight table {
            border-collapse: collapse;
            width: 100%;
        }
        
        .highlight .linenos {
            background: #e8e8e8;
            padding-right: 0.5em;
            text-align: right;
            color: #999;
            border-right: 1px solid #ccc;
            user-select: none;
        }
        
        .highlight .code {
            padding-left: 1em;
        }
        
        @media print {
            .highlight {
                border: 1px solid #ddd;
                page-break-inside: avoid;
            }
        }
        """
        
        return f"{base_css}\n{custom_css}\n{extra_css}"
    
    def set_style(self, style: str) -> None:
        """Change the highlighting style."""
        # Validate style exists
        try:
            get_style_by_name(style)
            self.style = style
            self._formatter_cache.clear()
        except ClassNotFound:
            raise ValueError(f"Unknown style: {style}. Available: {list(get_all_styles())}")
    
    @staticmethod
    def get_available_styles() -> list:
        """Get list of available highlighting styles."""
        return list(get_all_styles())
    
    def highlight_inline(self, code: str) -> str:
        """Highlight inline code snippet."""
        return f'<code class="inline-code">{self._escape_html(code)}</code>'
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
    
    def highlight_diff(self, old_code: str, new_code: str) -> str:
        """Highlight code diff."""
        import difflib
        
        diff = difflib.unified_diff(
            old_code.splitlines(keepends=True),
            new_code.splitlines(keepends=True),
            lineterm="",
        )
        diff_text = "".join(diff)
        
        return self.highlight_code(diff_text, "diff", line_numbers=False)
