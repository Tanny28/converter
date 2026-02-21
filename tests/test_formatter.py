"""
Tests for formatter module.
"""
import pytest

from backend.src.formatter import CodeHighlighter, PageOptimizer


class TestCodeHighlighter:
    """Tests for CodeHighlighter class."""
    
    def setup_method(self):
        self.highlighter = CodeHighlighter()
    
    def test_highlight_python_code(self):
        """Test Python code highlighting."""
        code = '''def hello():
    print("Hello, World!")
'''
        
        result = self.highlighter.highlight_code(code, "python")
        
        assert "<" in result  # Contains HTML
        assert "highlight" in result
    
    def test_highlight_with_line_numbers(self):
        """Test highlighting with line numbers."""
        code = "x = 1\ny = 2"
        
        result = self.highlighter.highlight_code(code, "python", line_numbers=True)
        
        assert "linenos" in result or "line" in result
    
    def test_highlight_without_line_numbers(self):
        """Test highlighting without line numbers."""
        code = "x = 1"
        
        result = self.highlighter.highlight_code(code, "python", line_numbers=False)
        
        # Should still highlight but without line table
        assert "highlight" in result
    
    def test_get_css(self):
        """Test CSS generation."""
        css = self.highlighter.get_css()
        
        assert ".highlight" in css
        assert "background" in css
    
    def test_set_style(self):
        """Test changing style."""
        self.highlighter.set_style("friendly")
        assert self.highlighter.style == "friendly"
    
    def test_set_invalid_style(self):
        """Test setting invalid style raises error."""
        with pytest.raises(ValueError):
            self.highlighter.set_style("nonexistent_style_12345")
    
    def test_available_styles(self):
        """Test getting available styles."""
        styles = CodeHighlighter.get_available_styles()
        
        assert isinstance(styles, list)
        assert len(styles) > 0
        assert "monokai" in styles
    
    def test_language_aliases(self):
        """Test language alias handling."""
        # Should work with alias
        result = self.highlighter.highlight_code("x = 1", "py")
        assert "highlight" in result
        
        # Should work with full name
        result = self.highlighter.highlight_code("x = 1", "python")
        assert "highlight" in result


class TestPageOptimizer:
    """Tests for PageOptimizer class."""
    
    def setup_method(self):
        self.optimizer = PageOptimizer()
    
    def test_analyze_content(self):
        """Test content analysis."""
        html = '''
        <h1>Title</h1>
        <p>Some paragraph text.</p>
        <pre class="output">Output text</pre>
        <div class="highlight">Code block</div>
        '''
        
        elements = self.optimizer.analyze_content(html)
        
        assert isinstance(elements, list)
    
    def test_suggest_page_breaks(self):
        """Test page break suggestion."""
        from backend.src.formatter.page_optimizer import PageElement
        
        elements = [
            PageElement("heading", "Title", 2.5, False, 10),
            PageElement("text", "Para 1", 5.0, True, 2),
            PageElement("code", "Code", 20.0, False, 5),
            PageElement("heading", "Section 2", 2.5, False, 10),
            PageElement("text", "Para 2", 30.0, True, 2),
        ]
        
        breaks = self.optimizer.suggest_page_breaks(elements)
        
        assert isinstance(breaks, list)
    
    def test_add_page_numbers(self):
        """Test adding page numbers."""
        html = "<html><head></head><body>Content</body></html>"
        
        result = self.optimizer.add_page_numbers(html)
        
        assert "@media print" in result or "@page" in result
    
    def test_add_headers_footers(self):
        """Test adding headers and footers."""
        html = "<html><head></head><body>Content</body></html>"
        
        result = self.optimizer.add_headers_footers(html, "Header Text", "Page ")
        
        assert "@page" in result
        assert "Header Text" in result
