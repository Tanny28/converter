"""
Markdown Extractor - Processes and cleans markdown content from notebooks.
"""
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class MarkdownSection:
    """Represents a markdown section."""
    level: int  # Heading level (1-6, 0 for no heading)
    title: Optional[str]
    content: str
    start_line: int = 0


class MarkdownExtractor:
    """Extracts and processes markdown content."""
    
    # Regex patterns
    HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    CODE_BLOCK_PATTERN = re.compile(r'```[\s\S]*?```', re.MULTILINE)
    INLINE_CODE_PATTERN = re.compile(r'`[^`]+`')
    LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    BOLD_PATTERN = re.compile(r'\*\*([^*]+)\*\*|__([^_]+)__')
    ITALIC_PATTERN = re.compile(r'\*([^*]+)\*|_([^_]+)_')
    LIST_PATTERN = re.compile(r'^[\s]*[-*+]\s+', re.MULTILINE)
    NUMBERED_LIST_PATTERN = re.compile(r'^[\s]*\d+\.\s+', re.MULTILINE)
    LATEX_BLOCK_PATTERN = re.compile(r'\$\$[\s\S]*?\$\$', re.MULTILINE)
    LATEX_INLINE_PATTERN = re.compile(r'\$[^$]+\$')
    
    def __init__(self):
        pass
    
    def extract_sections(self, markdown: str) -> List[MarkdownSection]:
        """Extract markdown into hierarchical sections based on headings."""
        sections = []
        lines = markdown.split("\n")
        current_section = MarkdownSection(level=0, title=None, content="", start_line=0)
        content_lines = []
        
        for i, line in enumerate(lines):
            heading_match = self.HEADING_PATTERN.match(line)
            
            if heading_match:
                # Save previous section
                if content_lines or current_section.title:
                    current_section.content = "\n".join(content_lines).strip()
                    sections.append(current_section)
                
                # Start new section
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                current_section = MarkdownSection(
                    level=level,
                    title=title,
                    content="",
                    start_line=i,
                )
                content_lines = []
            else:
                content_lines.append(line)
        
        # Add final section
        if content_lines or current_section.title:
            current_section.content = "\n".join(content_lines).strip()
            sections.append(current_section)
        
        return sections
    
    def extract_table_of_contents(self, markdown: str) -> List[Dict[str, any]]:
        """Generate a table of contents from markdown headings."""
        toc = []
        for match in self.HEADING_PATTERN.finditer(markdown):
            level = len(match.group(1))
            title = match.group(2).strip()
            # Create anchor from title
            anchor = self._create_anchor(title)
            toc.append({
                "level": level,
                "title": title,
                "anchor": anchor,
            })
        return toc
    
    def _create_anchor(self, title: str) -> str:
        """Create an anchor ID from a heading title."""
        # Remove special characters, convert spaces to hyphens, lowercase
        anchor = re.sub(r'[^\w\s-]', '', title.lower())
        anchor = re.sub(r'[\s]+', '-', anchor)
        return anchor
    
    def extract_links(self, markdown: str) -> List[Tuple[str, str]]:
        """Extract all links from markdown."""
        return self.LINK_PATTERN.findall(markdown)
    
    def extract_images(self, markdown: str) -> List[Tuple[str, str]]:
        """Extract all image references from markdown."""
        return self.IMAGE_PATTERN.findall(markdown)
    
    def extract_code_blocks(self, markdown: str) -> List[Dict[str, str]]:
        """Extract fenced code blocks with language info."""
        blocks = []
        pattern = re.compile(r'```(\w*)\n([\s\S]*?)```', re.MULTILINE)
        
        for match in pattern.finditer(markdown):
            language = match.group(1) or "text"
            code = match.group(2).strip()
            blocks.append({
                "language": language,
                "code": code,
            })
        
        return blocks
    
    def extract_latex(self, markdown: str) -> Dict[str, List[str]]:
        """Extract LaTeX equations from markdown."""
        return {
            "block": self.LATEX_BLOCK_PATTERN.findall(markdown),
            "inline": self.LATEX_INLINE_PATTERN.findall(markdown),
        }
    
    def clean_for_print(self, markdown: str) -> str:
        """Clean markdown for print output."""
        cleaned = markdown
        
        # Remove image references (they'll be in figures section)
        cleaned = self.IMAGE_PATTERN.sub('', cleaned)
        
        # Clean up multiple blank lines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        return cleaned.strip()
    
    def to_plain_text(self, markdown: str) -> str:
        """Convert markdown to plain text."""
        text = markdown
        
        # Remove code blocks
        text = self.CODE_BLOCK_PATTERN.sub('[code block]', text)
        
        # Remove images
        text = self.IMAGE_PATTERN.sub(r'\1', text)
        
        # Convert links to text
        text = self.LINK_PATTERN.sub(r'\1', text)
        
        # Remove formatting
        text = self.BOLD_PATTERN.sub(r'\1\2', text)
        text = self.ITALIC_PATTERN.sub(r'\1\2', text)
        text = self.INLINE_CODE_PATTERN.sub(lambda m: m.group(0)[1:-1], text)
        
        # Remove headings markers
        text = self.HEADING_PATTERN.sub(r'\2', text)
        
        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def get_summary(self, markdown: str, max_length: int = 500) -> str:
        """Get a summary of markdown content."""
        # Convert to plain text first
        plain = self.to_plain_text(markdown)
        
        # Get first paragraph or truncate
        paragraphs = plain.split("\n\n")
        summary = paragraphs[0] if paragraphs else plain
        
        if len(summary) > max_length:
            summary = summary[:max_length].rsplit(" ", 1)[0] + "..."
        
        return summary
