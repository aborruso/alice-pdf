# Alice PDF

CLI tool to extract tables from PDFs using Mistral OCR (Pixtral vision model) and convert them to machine-readable CSV files.

Dedicated to Alice Cortella, Marco Corona, and the entire onData community.

## Features

- Extract tables from multi-page PDFs
- Support page selection (ranges or lists)
- Optional YAML schema for improved extraction accuracy
- CSV output per page or merged into single file
- Configurable DPI and Mistral model

## Installation

```bash
uv tool install alice-pdf
```

Or from source:

```bash
git clone https://github.com/aborruso/alice-pdf.git
cd alice-pdf
uv tool install .
```

## Requirements

- Python 3.8+
- Mistral API key (https://console.mistral.ai/)

## Usage

### Setup API key

```bash
export MISTRAL_API_KEY="your-api-key"
```

### Basic commands

```bash
# Extract all tables
alice-pdf input.pdf output/

# Specific pages
alice-pdf input.pdf output/ --pages "1-3,5"

# Merge all tables into one CSV
alice-pdf input.pdf output/ --merge

# With table schema for better accuracy
alice-pdf input.pdf output/ --schema table_schema.yaml

# Debug mode
alice-pdf input.pdf output/ --debug
```

### Options

- `--pages`: Pages to process (default: all). Examples: "1", "1-3", "1,3,5"
- `--model`: Mistral model (default: pixtral-12b-2409)
- `--dpi`: Image resolution (default: 150)
- `-m, --merge`: Merge all tables into single CSV
- `--schema`: Path to YAML/JSON schema file for custom prompt generation
- `--prompt`: Custom prompt (overrides --schema)
- `--api-key`: Mistral API key (alternative to env var)
- `-d, --debug`: Enable debug logging

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

1. Converts PDF pages to raster images (150 DPI default)
2. Sends images to Mistral API with structured prompt
3. Mistral API (Pixtral) analyzes image and extracts tables as JSON
4. Converts JSON to pandas DataFrame
5. Saves CSV per page + optional merge
6. Adds 'page' column for traceability

## Output

Each extracted table is saved as:

- `{pdf_name}_page{N}_table{i}.csv`: CSV per table
- `{pdf_name}_merged.csv`: All tables merged (if --merge)

## Examples

### Example 1: Basic extraction

```bash
alice-pdf document.pdf output/
```

### Example 2: With schema and merge

```bash
alice-pdf document.pdf output/ \
  --schema table_schema.yaml \
  --pages "2-10" \
  --merge
```

### Example 3: High resolution and debug

```bash
alice-pdf document.pdf output/ \
  --dpi 300 \
  --debug
```

## License

MIT License - Copyright (c) 2025 Andrea Borruso <aborruso@gmail.com>
