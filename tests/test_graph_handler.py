"""
Tests for graph handler module.
"""
import pytest
from unittest.mock import MagicMock, patch
import base64

from backend.src.graph_handler import GraphExtractor, CaptionGenerator
from backend.src.parser.notebook_parser import ParsedNotebook, NotebookCell, CellOutput


class TestGraphExtractor:
    """Tests for GraphExtractor class."""
    
    def setup_method(self):
        self.extractor = GraphExtractor()
    
    def create_mock_notebook(self, cells_with_images=1):
        """Create a mock notebook with image outputs."""
        cells = []
        
        for i in range(cells_with_images):
            cell = NotebookCell(
                cell_type="code",
                source=f"plt.plot([{i}, {i+1}, {i+2}])",
                execution_count=i + 1,
                outputs=[
                    CellOutput(
                        output_type="display_data",
                        is_image=True,
                        mime_type="image/png",
                        image_data=base64.b64encode(b"fake_image_data").decode(),
                    )
                ]
            )
            cells.append(cell)
        
        return ParsedNotebook(
            title="Test Notebook",
            cells=cells,
            metadata={},
            nbformat=4,
            nbformat_minor=5,
        )
    
    def test_extract_all_returns_list(self):
        """Test that extract_all returns a list."""
        notebook = self.create_mock_notebook(2)
        graphs = self.extractor.extract_all(notebook)
        
        assert isinstance(graphs, list)
        assert len(graphs) == 2
    
    def test_extracted_graph_has_required_fields(self):
        """Test that extracted graphs have required fields."""
        notebook = self.create_mock_notebook(1)
        graphs = self.extractor.extract_all(notebook)
        
        assert len(graphs) == 1
        graph = graphs[0]
        
        assert hasattr(graph, 'index')
        assert hasattr(graph, 'cell_index')
        assert hasattr(graph, 'image_data')
        assert hasattr(graph, 'mime_type')
        assert hasattr(graph, 'format')
        assert hasattr(graph, 'caption')
    
    def test_is_plotting_code(self):
        """Test plotting code detection."""
        plotting_codes = [
            "plt.plot([1, 2, 3])",
            "df.plot()",
            "sns.heatmap(data)",
            "px.scatter(df, x='a', y='b')",
            "fig, ax = plt.subplots()",
        ]
        
        for code in plotting_codes:
            assert self.extractor.is_plotting_code(code), f"Should detect: {code}"
        
        non_plotting_codes = [
            "print('hello')",
            "x = 5",
            "import pandas as pd",
        ]
        
        for code in non_plotting_codes:
            assert not self.extractor.is_plotting_code(code), f"Should not detect: {code}"
    
    def test_identify_plot_library(self):
        """Test plot library identification."""
        assert self.extractor.identify_plot_library("import matplotlib.pyplot as plt") == "matplotlib"
        assert self.extractor.identify_plot_library("import seaborn as sns") == "seaborn"
        assert self.extractor.identify_plot_library("import plotly.express as px") == "plotly"
        assert self.extractor.identify_plot_library("print('hello')") is None
    
    def test_remove_inline_graphs(self):
        """Test removing inline graphs from notebook."""
        notebook = self.create_mock_notebook(2)
        
        cleaned = self.extractor.remove_inline_graphs(notebook)
        
        # Original should still have images
        assert len(notebook.cells[0].outputs) == 1
        
        # Cleaned should not have image outputs
        for cell in cleaned.cells:
            for output in cell.outputs:
                assert not output.is_image


class TestCaptionGenerator:
    """Tests for CaptionGenerator class."""
    
    def setup_method(self):
        self.generator = CaptionGenerator()
    
    def create_mock_graph(self, source_code):
        """Create a mock extracted graph."""
        from backend.src.graph_handler.graph_extractor import ExtractedGraph
        
        return ExtractedGraph(
            index=0,
            cell_index=0,
            image_data=b"fake",
            mime_type="image/png",
            format="png",
            source_code=source_code,
        )
    
    def test_generate_from_title(self):
        """Test caption generation from title in code."""
        graph = self.create_mock_graph('''
plt.figure()
plt.plot(x, y)
plt.title("Sales Over Time")
plt.show()
''')
        
        caption = self.generator.generate(graph)
        
        assert "Sales Over Time" in caption.text
        assert caption.source == "title"
        assert caption.confidence > 0.8
    
    def test_generate_from_comment(self):
        """Test caption generation from comment."""
        graph = self.create_mock_graph('''
# Plot showing the distribution of ages
plt.hist(ages)
plt.show()
''')
        
        caption = self.generator.generate(graph)
        assert "distribution" in caption.text.lower() or "Figure" in caption.text
    
    def test_generate_default(self):
        """Test default caption generation."""
        graph = self.create_mock_graph("plt.plot(x)")
        
        caption = self.generator.generate(graph)
        
        assert caption.figure_number == 1
        assert "Figure" in caption.text
    
    def test_format_caption_academic(self):
        """Test academic caption formatting."""
        from backend.src.graph_handler.caption_generator import GeneratedCaption
        
        caption = GeneratedCaption(
            text="Figure 1: Test Caption",
            confidence=0.9,
            source="title",
            figure_number=1,
        )
        
        formatted = self.generator.format_caption_for_report(caption, "academic")
        assert "**" in formatted  # Bold markdown
