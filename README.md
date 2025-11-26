# Alice PDF

CLI tool to extract tables from PDFs using **Mistral OCR** (Pixtral vision model), **AWS Textract**, or **Camelot** and convert them to machine-readable CSV files.

Dedicated to Alice Cortella, Marco Corona, and the entire onData community.

## Features

- **Triple extraction engines**: Mistral (schema-driven), AWS Textract (managed), or Camelot (local, native PDFs)
- Extract tables from multi-page PDFs
- Support page selection (ranges or lists)
- Optional YAML schema for improved extraction accuracy (Mistral only)
- CSV output per page or merged into single file
- Configurable DPI and engine-specific options

## Installation

```bash
uv tool install alice-pdf
```

For all engines:

```bash
uv tool install alice-pdf --with boto3 --with "camelot-py[cv]"
```

Or from source:

```bash
git clone https://github.com/aborruso/alice-pdf.git
cd alice-pdf
uv tool install . --with boto3 --with "camelot-py[cv]"
```

## Requirements

**For Mistral engine (default):**

- Python 3.8+
- Mistral API key (https://console.mistral.ai/)

**For Textract engine:**

- Python 3.8+
- AWS credentials with Textract permissions
- boto3 library

**For Camelot engine:**

- Python 3.8+
- camelot-py[cv] library (includes OpenCV)

## Usage

### Setup

**Mistral (default):**

```bash
export MISTRAL_API_KEY="your-api-key"
```

**Textract:**

```bash
export AWS_ACCESS_KEY_ID="your-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="eu-west-1"
```

### Basic commands

```bash
# Extract with Mistral (default)
alice-pdf input.pdf output/

# Extract with Textract
alice-pdf input.pdf output/ --engine textract --aws-region eu-west-1

# Extract with Camelot (local, fast for native PDFs)
alice-pdf input.pdf output/ --engine camelot --camelot-flavor stream

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

- `--engine {mistral,textract,camelot}`: Extraction engine (default: mistral)
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

### Mistral engine (default)

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

### Example 1: Basic extraction (Mistral)

```bash
alice-pdf document.pdf output/
```

### Example 2: Camelot extraction (native PDFs)

```bash
alice-pdf document.pdf output/ \
  --engine camelot \
  --camelot-flavor stream \
  --merge
```

### Example 3: Textract extraction

```bash
alice-pdf document.pdf output/ \
  --engine textract \
  --aws-region eu-west-1 \
  --merge
```

### Example 4: Mistral with schema and merge

```bash
alice-pdf document.pdf output/ \
  --engine mistral \
  --schema table_schema.yaml \
  --pages "2-10" \
  --merge
```

### Example 5: High resolution and debug

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

## License

MIT License - Copyright (c) 2025 Andrea Borruso <aborruso@gmail.com>
