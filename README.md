# Alice PDF
[![PyPI](https://img.shields.io/pypi/v/alice-pdf.svg)](https://pypi.org/project/alice-pdf/)

CLI tool to extract tables from PDFs using **Camelot** (default, free), **Mistral OCR** (Pixtral vision model), **AWS Textract**, or **pdfplumber** and convert them to machine-readable CSV files.

Dedicated to Alice Corona e Marco Corona, and the entire onData community.

![](assets/images/alice-pdf.jpg)

## Features

- **Four extraction engines**: Camelot (free, local, native PDFs), Mistral (schema-driven, scanned PDFs), AWS Textract (managed service), or pdfplumber (robust, works on both native and scanned PDFs)
- Extract tables from multi-page PDFs
- Support page selection (ranges or lists)
- Optional YAML schema for improved extraction accuracy (Mistral only)
- CSV output per page or merged into single file
- Configurable DPI and engine-specific options

## Installation

Prerequisites: Python 3.8+.

Quick install (pip): `pip install -U alice-pdf`

Install globally from PyPI (choose one):

- `pip install alice-pdf`
- `uv tool install alice-pdf` (requires [`uv`](https://docs.astral.sh/uv/getting-started/installation/))

Upgrade to the latest release at any time:

```bash
pip install -U alice-pdf
# or
uv tool upgrade alice-pdf
```

## Requirements

**For Camelot engine:**

- Python 3.8+
- camelot-py library (included in install)
- Works with native PDFs (not scanned images)

**For Mistral engine:**

- Python 3.8+
- Mistral API key (https://console.mistral.ai/)
- Best for scanned PDFs and complex tables

**For pdfplumber engine:**

- Python 3.8+
- pdfplumber library (included in install)
- Works on both native and scanned PDFs
- Handles complex table structures better than Camelot
- Free and local extraction

**For Textract engine:**

- Python 3.8+
- AWS credentials with Textract permissions
- boto3 library (included in install)

## Usage

### Setup

**Camelot (default, no setup needed):**

No API key required! Just install and use.

**Mistral:**

Option 1 - Environment variables (recommended for `uv run`):
```bash
export MISTRAL_API_KEY="your-api-key"
```

Option 2 - CLI parameters (recommended for `uv tool install`):
```bash
alice-pdf input.pdf output/ --engine mistral --api-key "your-api-key"
# alias: --mistral-api-key
```

Option 3 - .env file (only works with `uv run`, not with `uv tool install`):
```bash
# Create .env file in project directory
echo 'MISTRAL_API_KEY="your-api-key"' > .env
uv run alice-pdf input.pdf output/ --engine mistral
```

**Textract:**

Option 1 - Environment variables (recommended):
```bash
export AWS_ACCESS_KEY_ID="your-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="eu-west-1"
```

Option 2 - CLI parameters:
```bash
alice-pdf input.pdf output/ --engine textract \
  --aws-region eu-west-1 \
  --aws-access-key-id "your-key-id" \
  --aws-secret-access-key "your-secret-key"
```

Costi: il motore Textract qui usa solo `FeatureTypes=["TABLES"]` per tenere il costo a ~0,015 USD/pagina. Il feature FORMS (~0,050 USD/pagina) non è abilitato.

**Note:** `.env` file support is only available for Mistral and only when running with `uv run`.
For Textract, always use environment variables or CLI parameters.

### Basic commands

```bash
# Extract with Camelot (default, free, no API)
alice-pdf input.pdf output/

# Extract with Mistral (for scanned PDFs)
alice-pdf input.pdf output/ --engine mistral

# Extract with Textract
alice-pdf input.pdf output/ --engine textract --aws-region eu-west-1

# Extract with pdfplumber (robust, works on both native and scanned PDFs)
alice-pdf input.pdf output/ --engine pdfplumber

# Extract with pdfplumber with minimum table size constraints
alice-pdf input.pdf output/ --engine pdfplumber --pdfplumber-min-rows 2 --pdfplumber-min-cols 3

# Extract with Camelot (local, fast for native PDFs)
alice-pdf input.pdf output/ --engine camelot --camelot-flavor stream

# Camelot: fix for tables with merged cells
alice-pdf input.pdf output/ --engine camelot --camelot-split-text --merge

# Specific pages
alice-pdf input.pdf output/ --pages "1-3,5"

# Merge all tables into one CSV
alice-pdf input.pdf output/ --merge

# With table schema for better accuracy (Mistral only)
alice-pdf input.pdf output/ --schema table_schema.yaml

# Debug mode
alice-pdf input.pdf output/ --debug
```

### Options

**Common:**

- `--engine {mistral,textract,camelot,pdfplumber}`: Extraction engine (default: camelot)
- `--pages`: Pages to process (default: all). Examples: "1", "1-3", "1,3,5"
- `--dpi`: Image resolution (default: 150)
- `-m, --merge`: Merge all tables into single CSV
- `--no-resume`: Clear output and reprocess all pages
- `-d, --debug`: Enable debug logging

**Mistral-specific:**

- `--model`: Mistral model (default: pixtral-12b-2409)
- `--schema`: Path to YAML/JSON schema file for custom prompt generation
- `--prompt`: Custom prompt (overrides --schema)
- `--api-key`: Mistral API key (alternative to env var)
- `--timeout-ms`: HTTP timeout in milliseconds (default: 60000)

**Textract-specific:**

- `--aws-region`: AWS region (or set AWS_DEFAULT_REGION)
- `--aws-access-key-id`: AWS access key (or set AWS_ACCESS_KEY_ID)
- `--aws-secret-access-key`: AWS secret key (or set AWS_SECRET_ACCESS_KEY)

**Camelot-specific:**

- `--camelot-flavor {lattice,stream}`: Extraction mode (default: lattice)
  - `lattice`: For tables with visible borders
  - `stream`: For tables without borders (whitespace-based)
- `--camelot-split-text`: Split text spanning multiple cells (useful for complex tables with merged cells)

**pdfplumber-specific:**

- `--pdfplumber-min-rows`: Minimum number of rows for table detection (default: 1)
- `--pdfplumber-min-cols`: Minimum number of columns for table detection (default: 1)
- `--pdfplumber-strip-text` / `--no-pdfplumber-strip-text`: Enable/disable whitespace stripping in extracted text (default: strip)

## Table Schema

To improve extraction accuracy, create a YAML file describing the table structure:

```yaml
name: "housing_properties"
description: "Housing properties table"

columns:
  - name: "PROPERTY"
    description: "Property owner name"
    examples:
      - "ATER DI VENEZIA"
      - "COMUNE DI VENEZIA"

  - name: "UNIT"
    description: "Housing unit number"
    examples:
      - "2950010"
      - "170"

notes:
  - "Keep columns separate"
  - "Do NOT merge adjacent cells"
  - "All rows should have exactly N columns"
```

## How it works

### Camelot engine (default)

1. Converts PDF pages to raster images (150 DPI default)
2. Sends images to Mistral API with structured prompt
3. Mistral API (Pixtral) analyzes image and extracts tables as JSON
4. Converts JSON to pandas DataFrame
5. Saves CSV per page + optional merge
6. Adds 'page' column for traceability

**Progressive Timeout Retry:**

When a page times out, the tool automatically retries with doubled timeouts:

- **Attempt 1**: 60 seconds (default timeout)
- **Attempt 2**: 120 seconds (2x timeout, if first attempt times out)
- **Attempt 3**: 240 seconds (4x timeout, if second attempt times out)

After 3 failed attempts, the page is skipped and processing continues with the next page. Non-timeout errors (authentication, rate limits, etc.) skip retry and move to the next page immediately.

### Textract engine

1. Converts PDF pages to raster images (150 DPI default)
2. Sends images to AWS Textract API
3. Textract analyzes document structure and extracts tables
4. Converts Textract response to pandas DataFrame
5. Saves CSV per page + optional merge
6. Adds 'page' column for traceability

**Note:** Textract does not support schema/prompt customization. Use Mistral if you need custom prompts.

### Camelot engine

1. Reads native PDF structure (no image conversion needed)
2. Detects tables using borders (`lattice`) or whitespace (`stream`)
3. Converts to pandas DataFrame
4. Saves CSV per page + optional merge
5. Adds 'page' column for traceability

**Best for:** Native PDFs (not scanned) with clear table structure. Fast and free (local processing).

## Output

Each extracted table is saved as:

- `{pdf_name}_page{N}_table{i}.csv`: CSV per table
- `{pdf_name}_merged.csv`: All tables merged (if --merge)

## Examples

### Example 1: Basic extraction (Camelot)

```bash
alice-pdf document.pdf output/
```

### Example 2: Mistral extraction (for scanned PDFs)

```bash
alice-pdf document.pdf output/ \
  --engine mistral \
  --merge
```

### Example 3: pdfplumber extraction (robust, works on both native and scanned PDFs)

```bash
alice-pdf document.pdf output/ \
  --engine pdfplumber \
  --pdfplumber-min-rows 2 \
  --pdfplumber-min-cols 3 \
  --merge
```

### Example 4: Textract extraction

```bash
alice-pdf document.pdf output/ \
  --engine textract \
  --aws-region eu-west-1 \
  --merge
```

### Example 5: Mistral with schema and merge

```bash
alice-pdf document.pdf output/ \
  --engine mistral \
  --schema table_schema.yaml \
  --pages "2-10" \
  --merge
```

### Example 6: High resolution and debug

```bash
alice-pdf document.pdf output/ \
  --dpi 300 \
  --debug
```

## Choosing an engine

**Use Mistral when:**

- You need custom prompts or schema-driven extraction
- Tables have complex structure requiring specific instructions
- You want fine control over extraction behavior

**Use Textract when:**

- You need fast, reliable extraction on standard tables
- You prefer managed AWS infrastructure
- Schema customization is not required

**Use Camelot when:**

- PDF is native (not scanned)
- Tables have clear structure (borders or consistent spacing)
- You want local, free extraction (no API costs)
- Speed is critical for simple PDFs

**Use pdfplumber when:**

- PDF can be native or scanned
- Tables have complex structures or inconsistent borders
- You want robust local extraction (no API costs)
- Camelot fails to detect tables properly

## Project Structure

```
alice-pdf/
├── alice_pdf/          # Main package source code
│   ├── cli.py          # CLI entry point and argument parsing
│   ├── extractor.py    # Mistral engine implementation
│   ├── textract_extractor.py  # AWS Textract engine
│   ├── camelot_extractor.py   # Camelot engine
│   ├── pdfplumber_extractor.py # pdfplumber engine
│   └── prompt_generator.py    # YAML schema to prompt converter
├── docs/               # Documentation
│   └── best-practices.md  # Comprehensive usage guide
├── sample/             # Example PDFs and schemas
│   ├── *.pdf           # Sample PDF files for testing
│   └── *.yaml          # Example table schemas
├── openspec/           # OpenSpec specifications
│   ├── AGENTS.md       # Agent instructions
│   └── specs/          # Change proposals and documentation
├── tests/              # Unit tests
└── tmp/                # Temporary test outputs (gitignored)
```

**Key directories:**

- `alice_pdf/`: Core library code
- `docs/`: User guides and best practices
- `sample/`: Example files and schemas for testing
- `openspec/`: Project specifications using OpenSpec format
- `tmp/`: Temporary directory for test outputs (not tracked in git)

## License

MIT License - Copyright (c) 2025 Andrea Borruso <aborruso@gmail.com>
