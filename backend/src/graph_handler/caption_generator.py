"""
Caption Generator - Generates automatic captions for graphs and figures.
"""
import re
from typing import Optional, List, Dict
from dataclasses import dataclass

from .graph_extractor import ExtractedGraph


@dataclass
class GeneratedCaption:
    """Represents a generated caption with metadata."""
    text: str
    confidence: float  # 0.0 to 1.0
    source: str  # 'title', 'comment', 'code', 'default'
    figure_number: int


class CaptionGenerator:
    """Generates captions for figures based on code analysis."""
    
    # Common plot function patterns with their descriptions
    PLOT_DESCRIPTIONS = {
        "plt.plot": "Line plot",
        "plt.scatter": "Scatter plot",
        "plt.bar": "Bar chart",
        "plt.barh": "Horizontal bar chart",
        "plt.hist": "Histogram",
        "plt.boxplot": "Box plot",
        "plt.pie": "Pie chart",
        "plt.imshow": "Image visualization",
        "plt.contour": "Contour plot",
        "plt.heatmap": "Heatmap",
        "sns.heatmap": "Heatmap",
        "sns.lineplot": "Line plot",
        "sns.scatterplot": "Scatter plot",
        "sns.barplot": "Bar plot",
        "sns.countplot": "Count plot",
        "sns.boxplot": "Box plot",
        "sns.violinplot": "Violin plot",
        "sns.pairplot": "Pair plot",
        "sns.distplot": "Distribution plot",
        "sns.histplot": "Histogram",
        "sns.kdeplot": "KDE plot",
        "sns.regplot": "Regression plot",
        "px.scatter": "Scatter plot",
        "px.line": "Line chart",
        "px.bar": "Bar chart",
        "px.histogram": "Histogram",
        "px.box": "Box plot",
        "px.pie": "Pie chart",
        "go.Figure": "Custom figure",
    }
    
    # Variable name patterns that indicate data types
    DATA_PATTERNS = {
        r'accuracy|acc': 'accuracy',
        r'loss': 'loss',
        r'error': 'error',
        r'train|training': 'training',
        r'test|testing': 'testing',
        r'valid|validation': 'validation',
        r'epoch': 'training epochs',
        r'time|date': 'time series',
        r'price': 'price',
        r'count': 'count',
        r'distribution': 'distribution',
        r'correlation': 'correlation',
        r'confus': 'confusion matrix',
    }
    
    def __init__(self):
        pass
    
    def generate(self, graph: ExtractedGraph) -> GeneratedCaption:
        """Generate a caption for an extracted graph."""
        code = graph.source_code
        figure_num = graph.index + 1
        
        # Strategy 1: Look for explicit title in code
        title = self._extract_title_from_code(code)
        if title:
            return GeneratedCaption(
                text=f"Figure {figure_num}: {title}",
                confidence=0.9,
                source="title",
                figure_number=figure_num,
            )
        
        # Strategy 2: Look for descriptive comments
        comment = self._extract_comment(code)
        if comment:
            return GeneratedCaption(
                text=f"Figure {figure_num}: {comment}",
                confidence=0.8,
                source="comment",
                figure_number=figure_num,
            )
        
        # Strategy 3: Analyze code to determine plot type and data
        analysis = self._analyze_code(code)
        if analysis:
            return GeneratedCaption(
                text=f"Figure {figure_num}: {analysis}",
                confidence=0.6,
                source="code",
                figure_number=figure_num,
            )
        
        # Fallback
        return GeneratedCaption(
            text=f"Figure {figure_num}",
            confidence=0.3,
            source="default",
            figure_number=figure_num,
        )
    
    def generate_all(self, graphs: List[ExtractedGraph]) -> List[GeneratedCaption]:
        """Generate captions for all graphs."""
        return [self.generate(g) for g in graphs]
    
    def _extract_title_from_code(self, code: str) -> Optional[str]:
        """Extract title from plotting code."""
        patterns = [
            r'\.set_title\s*\(\s*["\']([^"\']+)["\']',
            r'\.suptitle\s*\(\s*["\']([^"\']+)["\']',
            r'title\s*=\s*["\']([^"\']+)["\']',
            r'plt\.title\s*\(\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, code)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_comment(self, code: str) -> Optional[str]:
        """Extract descriptive comments from code."""
        lines = code.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for comments that describe the visualization
            if line.startswith('#'):
                comment = line[1:].strip()
                # Filter out non-descriptive comments
                if len(comment) > 10 and len(comment) < 100:
                    lower = comment.lower()
                    if any(word in lower for word in ['plot', 'chart', 'graph', 'visual', 'show', 'display', 'figure']):
                        return comment
                    # Accept capitalized comments (likely titles)
                    if comment[0].isupper() and not comment.startswith('TODO') and not comment.startswith('FIXME'):
                        return comment
        
        return None
    
    def _analyze_code(self, code: str) -> Optional[str]:
        """Analyze code to generate a descriptive caption."""
        # Identify plot type
        plot_type = None
        for func, description in self.PLOT_DESCRIPTIONS.items():
            if func in code:
                plot_type = description
                break
        
        if not plot_type:
            return None
        
        # Try to identify what data is being plotted
        data_type = None
        for pattern, description in self.DATA_PATTERNS.items():
            if re.search(pattern, code, re.IGNORECASE):
                data_type = description
                break
        
        # Extract axis labels if present
        xlabel = self._extract_label(code, 'xlabel')
        ylabel = self._extract_label(code, 'ylabel')
        
        # Build caption
        parts = [plot_type]
        
        if data_type:
            parts.append(f"showing {data_type}")
        
        if xlabel and ylabel:
            parts.append(f"({xlabel} vs {ylabel})")
        elif xlabel:
            parts.append(f"of {xlabel}")
        elif ylabel:
            parts.append(f"of {ylabel}")
        
        return " ".join(parts)
    
    def _extract_label(self, code: str, label_type: str) -> Optional[str]:
        """Extract axis label from code."""
        patterns = [
            rf'\.set_{label_type}\s*\(\s*["\']([^"\']+)["\']',
            rf'plt\.{label_type}\s*\(\s*["\']([^"\']+)["\']',
            rf'{label_type}\s*=\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, code)
            if match:
                return match.group(1).strip()
        
        return None
    
    def format_caption_for_report(self, caption: GeneratedCaption, style: str = "academic") -> str:
        """Format caption according to report style."""
        if style == "academic":
            return f"**{caption.text}**"
        elif style == "technical":
            return caption.text
        elif style == "minimal":
            return f"Fig. {caption.figure_number}"
        else:
            return caption.text
