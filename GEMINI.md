# Alice PDF - Project Context

## Project Overview

**Alice PDF** is a CLI tool designed to extract tabular data from PDF documents using Mistral's OCR capabilities (specifically the Pixtral vision model). It converts PDF pages into images, processes them via the Mistral API with structured prompts, and outputs the extracted data as machine-readable CSV files.

### Key Features
- **Multi-page Extraction**: Process entire documents or specific page ranges/lists.
- **Schema-Driven Accuracy**: Optional YAML/JSON schemas to guide the model's extraction for specific table structures.
- **Flexible Output**: Generate individual CSVs per page or a single merged file.
- **Mistral Integration**: Uses the Pixtral 12B model for high-quality vision-based text extraction.

## Tech Stack

*   **Language**: Python 3.8+
*   **Core Libraries**:
    *   `pymupdf` (fitz): PDF manipulation and rendering.
    *   `mistralai`: Client for Mistral AI API.
    *   `pandas`: Data manipulation and CSV export.
    *   `pillow`: Image processing.
    *   `pyyaml`: Schema parsing.
*   **Build & Management**: `uv` (recommended), `hatchling` (backend).
*   **Testing**: `pytest`, `pytest-mock`, `pytest-cov`.

## Project Structure

```text
/
├── alice_pdf/              # Source code
│   ├── __init__.py
│   ├── cli.py              # Entry point and argument parsing
│   ├── extractor.py        # Core extraction and orchestration logic
│   └── prompt_generator.py # Schema-to-prompt conversion
├── tests/                  # Test suite
├── openspec/               # Project specifications and design documents
├── sample/                 # Sample input files
├── output/                 # Default output directory
├── pyproject.toml          # Project configuration and dependencies
├── uv.lock                 # Dependency lock file
├── README.md               # User documentation
└── PRD.md                  # Product Requirement Document
```

## Building and Running

### Installation
This project uses `uv` for management.

```bash
# Install from source
uv tool install .
```

### Usage
The main command is `alice-pdf`.

```bash
# Basic extraction
alice-pdf input.pdf output/

# With options
alice-pdf input.pdf output/ --pages "1-3,5" --merge --schema schema.yaml
```

**Key Arguments:**
*   `pdf_path`: Input PDF file.
*   `output_dir`: Directory for generated CSVs.
*   `--api-key`: Mistral API key (or set `MISTRAL_API_KEY` env var).
*   `--pages`: Specific pages to process (e.g., "1-5", "1,3").
*   `--merge`: Combine all extracted tables into one CSV.
*   `--schema`: Path to a YAML file defining table structure.
*   `--debug`: Enable verbose logging.

### Development

To set up the development environment:

```bash
# Install dependencies including dev tools
uv sync
# OR
pip install -e ".[dev]"
```

### Testing

Run the test suite using `pytest`:

```bash
pytest
```

## Development Conventions

*   **Code Style**: Follow standard Python conventions (snake_case). Type hints are encouraged.
*   **Architecture**:
    *   **CLI Layer** (`cli.py`): Handles user input, logging config, and top-level flow.
    *   **Orchestration** (`extractor.py`): Manages the PDF-to-Image-to-Data pipeline.
    *   **Service** (`prompt_generator.py`): Generates specific prompts based on user schemas.
*   **Logging**: Unbuffered output to stdout. Debug mode available via flag.
*   **Output Handling**: By default, the tool clears the output directory before running unless `--resume` or `--no-resume` logic dictates otherwise.
*   **Git**: Commit messages should be concise. Update `LOG.md` with significant changes.

## Environment Variables

*   `MISTRAL_API_KEY`: Required for API access.
*   `ALICE_PDF_IGNORE_ENV`: Set to `1` to ignore `.env` file loading (useful for testing).
