# Smart Notebook Print Formatter (SNPF)

A tool to convert Jupyter/Python notebooks into professionally formatted printable reports with optimized graph handling.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Features

- **Notebook Conversion**: Convert `.ipynb` and `.py` files to HTML or DOCX
- **Graph Extraction**: Automatically extract visualizations and place them in a figures section
- **Professional Formatting**: Academic and technical templates with syntax highlighting
- **Print Optimization**: Page breaks, headers/footers, and table of contents
- **Privacy-Focused**: Runs completely offline on your local machine
- **Batch Processing**: Convert multiple notebooks at once

## Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/notebook-formatter.git
cd notebook-formatter
```

2. Create a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

4. Run the server:
```bash
uvicorn src.main:app --reload
```

5. Open your browser to `http://localhost:8000`

### Using the Frontend

1. Start the frontend server:
```bash
cd frontend
npx serve src -p 3000
```

2. Open `http://localhost:3000` in your browser

## API Usage

### Upload a Notebook

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@your_notebook.ipynb"
```

### Convert to DOCX

```bash
curl -X POST "http://localhost:8000/api/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your_session_id",
    "filename": "your_notebook.ipynb",
    "options": {
      "format": "docx",
      "template": "academic_report.html"
    }
  }'
```

### Download Result

```bash
curl -O "http://localhost:8000/api/download/{session_id}/{filename}.pdf"
```

## Project Structure

```
notebook-formatter/
├── backend/
│   ├── src/
│   │   ├── api/           # FastAPI routes and schemas
│   │   ├── parser/        # Notebook parsing
│   │   ├── graph_handler/ # Graph extraction
│   │   ├── formatter/     # Code highlighting, templates
│   │   ├── exporter/      # PDF, HTML, DOCX export
│   │   └── utils/         # File handling, validation
│   ├── templates/         # HTML templates
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── index.html
│       ├── styles/
│       └── scripts/
├── tests/
├── docs/
└── README.md
```

## Configuration

Copy `.env.example` to `.env` and customize:

```env
DEBUG=false
MAX_FILE_SIZE_MB=50
CODE_THEME=monokai
DEFAULT_EXPORT_FORMAT=pdf
```

## Templates

Three templates are included:

1. **Academic Report** (`academic_report.html`)
   - Table of contents
   - Serif fonts
   - Centered figures section
   - Suitable for academic submissions

2. **Technical Documentation** (`technical_doc.html`)
   - Modern sans-serif design
   - Dark code blocks
   - Suitable for technical reports

3. **Basic** (`base.html`)
   - Clean, minimal design
   - Good starting point for customization

## Development

### Running Tests

```bash
cd backend
pytest tests/ -v
```

### Code Quality

```bash
ruff check src/
mypy src/
```

## Deployment

### Docker

Build and run with Docker:

```bash
docker build -t notebook-formatter .
docker run -p 8000:8000 notebook-formatter
```

Or use Docker Compose:

```bash
docker-compose up
```

## Roadmap

- [x] Phase 1: MVP
  - [x] Notebook parsing
  - [x] Graph extraction
  - [x] PDF export
  - [x] Basic frontend

- [ ] Phase 2: Enhanced Features
  - [ ] DOCX improvements
  - [ ] Custom templates UI
  - [ ] Batch conversion UI
  - [ ] Progress indicators

- [ ] Phase 3: AI Integration
  - [ ] Auto summaries
  - [ ] Smart captions
  - [ ] Code explanations

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [WeasyPrint](https://weasyprint.org/) - PDF generation
- [Pygments](https://pygments.org/) - Syntax highlighting
- [nbformat](https://nbformat.readthedocs.io/) - Notebook parsing
