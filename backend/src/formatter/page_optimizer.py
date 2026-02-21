"""
Page Optimizer - Optimizes content layout for printing.
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class PageElement:
    """Represents an element on a page."""
    element_type: str  # 'heading', 'code', 'text', 'figure', 'output'
    content: str
    estimated_height: float  # in relative units
    can_break: bool = True
    priority: int = 1  # Higher = keep together more strongly


@dataclass
class PageBreak:
    """Represents a suggested page break."""
    position: int  # Index in element list
    reason: str


class PageOptimizer:
    """Optimizes page layout and breaks for printed output."""
    
    # Approximate line heights in relative units
    LINE_HEIGHT = 1.0
    HEADING_HEIGHT = 2.5
    CODE_LINE_HEIGHT = 1.2
    FIGURE_HEIGHT = 15.0  # Average figure
    
    # Page dimensions (relative units)
    PAGE_HEIGHT = 50.0  # Approximate lines per page
    TOP_MARGIN = 3.0
    BOTTOM_MARGIN = 5.0
    USABLE_HEIGHT = PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN
    
    def __init__(self):
        pass
    
    def analyze_content(self, html_content: str) -> List[PageElement]:
        """Analyze HTML content and identify page elements."""
        elements = []
        
        # Simple parsing - in production, use BeautifulSoup
        patterns = [
            (r'<h1[^>]*>(.*?)</h1>', 'heading', 3.0, False, 10),
            (r'<h2[^>]*>(.*?)</h2>', 'heading', 2.5, False, 8),
            (r'<h3[^>]*>(.*?)</h3>', 'heading', 2.0, False, 6),
            (r'<pre[^>]*class="[^"]*output[^"]*"[^>]*>(.*?)</pre>', 'output', None, True, 3),
            (r'<div[^>]*class="[^"]*highlight[^"]*"[^>]*>(.*?)</div>', 'code', None, False, 5),
            (r'<figure[^>]*>(.*?)</figure>', 'figure', self.FIGURE_HEIGHT, False, 7),
            (r'<p[^>]*>(.*?)</p>', 'text', None, True, 2),
        ]
        
        for pattern, elem_type, height, can_break, priority in patterns:
            for match in re.finditer(pattern, html_content, re.DOTALL | re.IGNORECASE):
                content = match.group(1)
                
                if height is None:
                    # Calculate height based on content
                    height = self._estimate_height(content, elem_type)
                
                elements.append(PageElement(
                    element_type=elem_type,
                    content=content[:100],  # Truncate for storage
                    estimated_height=height,
                    can_break=can_break,
                    priority=priority,
                ))
        
        return elements
    
    def _estimate_height(self, content: str, elem_type: str) -> float:
        """Estimate the height of content."""
        # Strip HTML tags
        text = re.sub(r'<[^>]+>', '', content)
        lines = text.count('\n') + 1
        char_per_line = 80
        
        # Estimate wrapped lines
        wrapped_lines = max(lines, len(text) / char_per_line)
        
        if elem_type == 'code':
            return wrapped_lines * self.CODE_LINE_HEIGHT
        elif elem_type == 'output':
            return min(wrapped_lines * self.LINE_HEIGHT, 10)  # Cap output height
        else:
            return wrapped_lines * self.LINE_HEIGHT
    
    def suggest_page_breaks(self, elements: List[PageElement]) -> List[PageBreak]:
        """Suggest optimal page break positions."""
        breaks = []
        current_height = self.TOP_MARGIN
        
        for i, element in enumerate(elements):
            # Check if element fits on current page
            if current_height + element.estimated_height > self.USABLE_HEIGHT:
                # Need a page break
                
                # Find best position for break
                best_pos = self._find_best_break_position(elements, i, current_height)
                
                breaks.append(PageBreak(
                    position=best_pos,
                    reason=self._get_break_reason(elements, best_pos, i),
                ))
                
                # Reset height after break
                current_height = self.TOP_MARGIN
            
            current_height += element.estimated_height
        
        return breaks
    
    def _find_best_break_position(
        self, 
        elements: List[PageElement], 
        current_index: int,
        current_height: float
    ) -> int:
        """Find the best position for a page break."""
        # Look back for a good break point
        search_start = max(0, current_index - 5)
        
        best_pos = current_index
        best_score = -float('inf')
        
        for i in range(search_start, current_index + 1):
            score = self._calculate_break_score(elements, i)
            if score > best_score:
                best_score = score
                best_pos = i
        
        return best_pos
    
    def _calculate_break_score(self, elements: List[PageElement], position: int) -> float:
        """Calculate how good a break position is (higher = better)."""
        if position >= len(elements):
            return 0
        
        score = 0
        element = elements[position]
        
        # Prefer breaking before headings
        if element.element_type == 'heading':
            score += 10
        
        # Avoid breaking in middle of code
        if not element.can_break:
            score -= 20
        
        # Consider element priority
        score -= element.priority
        
        # Prefer keeping related elements together
        if position > 0:
            prev = elements[position - 1]
            # Don't break between heading and first paragraph
            if prev.element_type == 'heading':
                score -= 15
        
        return score
    
    def _get_break_reason(
        self, 
        elements: List[PageElement], 
        break_pos: int, 
        original_pos: int
    ) -> str:
        """Get a human-readable reason for the break."""
        if break_pos >= len(elements):
            return "End of content"
        
        element = elements[break_pos]
        
        if element.element_type == 'heading':
            return f"New section: heading"
        elif break_pos != original_pos:
            return "Moved to avoid breaking element"
        else:
            return "Content overflow"
    
    def add_page_breaks_to_html(
        self, 
        html_content: str, 
        breaks: List[PageBreak]
    ) -> str:
        """Insert page break markers into HTML."""
        # This is a simplified implementation
        # In production, use proper HTML parsing
        
        page_break_html = '\n<div class="page-break" style="page-break-after: always;"></div>\n'
        
        # For now, add breaks before major headings
        result = re.sub(
            r'(<h1[^>]*>)',
            page_break_html + r'\1',
            html_content
        )
        
        return result
    
    def optimize_code_blocks(self, html_content: str, max_lines: int = 40) -> str:
        """Split long code blocks to fit on pages."""
        def split_code(match):
            full_block = match.group(0)
            lines = full_block.count('\n')
            
            if lines <= max_lines:
                return full_block
            
            # Add a "continued" marker
            return full_block  # Simplified - keep as is with scroll
        
        return re.sub(
            r'<div class="highlight">.*?</div>',
            split_code,
            html_content,
            flags=re.DOTALL
        )
    
    def add_page_numbers(self, html_content: str) -> str:
        """Add CSS for page numbering in print."""
        page_number_css = '''
        <style>
        @media print {
            @page {
                @bottom-center {
                    content: counter(page);
                }
            }
            
            body {
                counter-reset: page;
            }
            
            .page-number::after {
                content: counter(page);
            }
        }
        </style>
        '''
        
        # Insert before </head>
        return html_content.replace('</head>', f'{page_number_css}</head>')
    
    def add_headers_footers(
        self, 
        html_content: str, 
        header_text: str = "",
        footer_text: str = ""
    ) -> str:
        """Add headers and footers for print."""
        header_footer_css = f'''
        <style>
        @media print {{
            @page {{
                @top-center {{
                    content: "{header_text}";
                    font-size: 10pt;
                    color: #666;
                }}
                @bottom-right {{
                    content: "{footer_text}" counter(page);
                    font-size: 10pt;
                    color: #666;
                }}
            }}
        }}
        </style>
        '''
        
        return html_content.replace('</head>', f'{header_footer_css}</head>')
