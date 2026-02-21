# User Guide

## Getting Started

### What is Smart Notebook Print Formatter?

Smart Notebook Print Formatter (SNPF) is a tool that converts your Jupyter notebooks and Python scripts into professionally formatted, print-ready documents. It automatically:

- Extracts graphs and places them in a dedicated Figures section
- Applies syntax highlighting to code
- Formats markdown content
- Generates table of contents
- Optimizes page breaks

### Supported File Types

- Jupyter Notebooks (`.ipynb`)
- Python scripts (`.py`) with cell markers

### Output Formats

- **PDF**: Best for printing and sharing
- **HTML**: Good for web viewing
- **DOCX**: Microsoft Word format

---

## Basic Usage

### Step 1: Upload Your Notebook

1. Click the upload area or drag-and-drop your file
2. Wait for the upload to complete
3. The file will appear in the file list

### Step 2: Preview

After uploading, you'll see:
- Notebook title
- Cell count and types
- Number of figures detected
- Preview of cell contents

### Step 3: Configure Options

Choose your export settings:

#### Format
- **PDF**: Recommended for printing
- **HTML**: Creates a standalone webpage
- **DOCX**: Editable in Microsoft Word

#### Template
- **Academic Report**: Formal academic style
- **Technical Documentation**: Modern technical style
- **Basic**: Minimal, clean design

#### Options
- **Line numbers**: Show/hide code line numbers
- **Include outputs**: Include cell outputs
- **Table of contents**: Generate TOC from headings
- **Page numbers**: Add page numbers (PDF/print)

### Step 4: Convert

1. Click "Convert & Download"
2. Wait for processing to complete
3. Download your formatted document

---

## Advanced Features

### Working with Python Scripts

Python scripts can include cell markers for better conversion:

```python
# %% 
# This is a code cell
import numpy as np

# %% md
# This is a markdown cell
# ## My Heading
# Some **formatted** text

# %%
# Another code cell
print("Hello!")
```

### Custom Templates

Templates are HTML files with Jinja2 syntax. Key variables:

- `{{ title }}`: Notebook title
- `{{ cells }}`: List of processed cells
- `{{ graphs }}`: List of extracted figures
- `{{ css }}`: Syntax highlighting CSS

### Batch Conversion

Using the API, you can convert multiple notebooks:

```bash
curl -X POST "http://localhost:8000/api/convert/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your_session",
    "filenames": ["nb1.ipynb", "nb2.ipynb"],
    "options": {"format": "pdf"}
  }'
```

---

## Tips for Best Results

### 1. Use Clear Headings

Structure your notebook with markdown headings:
```markdown
# Main Title
## Section 1
### Subsection 1.1
```

### 2. Add Plot Titles

Include titles in your plots for better captions:
```python
plt.title("Sales Over Time")
```

### 3. Add Comments

Add descriptive comments above visualizations:
```python
# Distribution of Customer Ages
plt.hist(ages)
```

### 4. Keep Code Cells Reasonable

Very long code cells may not format well. Consider splitting:
- Imports in one cell
- Data processing in another
- Visualization in a separate cell

---

## Troubleshooting

### File Won't Upload

- Check file size (max 50MB)
- Verify file extension (.ipynb or .py)
- Try a different browser

### Graphs Not Detected

- Ensure plots are rendered (not just defined)
- Check that output cells contain images
- Re-run notebook cells before uploading

### PDF Formatting Issues

- Try a different template
- Simplify very long code blocks
- Check for special characters in titles

### Slow Conversion

- Large notebooks take longer
- Many high-resolution graphs increase time
- Consider splitting into smaller notebooks

---

## FAQ

**Q: Is my data uploaded to the cloud?**
A: No, SNPF runs entirely locally. Your notebooks never leave your machine.

**Q: Can I customize the look?**
A: Yes, create custom templates or modify existing ones.

**Q: What about LaTeX equations?**
A: LaTeX in markdown is preserved. PDF rendering depends on font support.

**Q: Can I use this for academic papers?**
A: Yes! The Academic Report template is designed for this purpose.
