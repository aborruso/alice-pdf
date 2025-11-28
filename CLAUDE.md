<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Alice PDF is a CLI tool for extracting tables from PDFs using three engines: Camelot (default, free), Mistral OCR (Pixtral vision model), or AWS Textract. It converts PDF pages to images at specified DPI (for Mistral/Textract) or processes native PDF structure (for Camelot), and outputs CSV files.

Core workflow:

1. PDF → image conversion at 150 DPI (Mistral/Textract) OR native structure parsing (Camelot)
2. Process selected pages (ranges or lists)
3. Send to API or process locally with optional YAML schema (Mistral only)
4. Get CSV per page + optional merged output

## Engines

- `camelot` (default): Local, free extraction for native PDFs. Use `--camelot-flavor {lattice,stream}`. Does NOT work on scanned PDFs (requires extractable text).
- `mistral`: OCR via Pixtral vision for scanned PDFs. Supports `--schema` and `--prompt`. Requires MISTRAL_API_KEY.
- `textract`: AWS Textract for managed extraction. Needs AWS creds via env or flags (`--aws-region`, `--aws-access-key-id`, `--aws-secret-access-key`).

## Project Structure

```
alice-pdf/
├── alice_pdf/          # Main package source code
│   ├── cli.py          # CLI entry point and argument parsing
│   ├── extractor.py    # Mistral engine implementation
│   ├── textract_extractor.py  # AWS Textract engine
│   ├── camelot_extractor.py   # Camelot engine
│   └── prompt_generator.py    # YAML schema to prompt converter
├── docs/               # Documentation
│   └── best-practices.md  # Comprehensive usage guide
├── sample/             # Example PDFs and schemas
│   ├── *.pdf           # Sample PDF files for testing
│   └── *.yaml          # Example table schemas (e.g., canoni_schema.yaml)
├── openspec/           # OpenSpec specifications
│   ├── AGENTS.md       # Agent instructions for proposals
│   └── specs/          # Change proposals and documentation
├── tests/              # Unit tests
└── tmp/                # Temporary test outputs (gitignored)
```

**Key directories:**

- `alice_pdf/`: Core library code with three extraction engines
- `docs/`: User guides including best-practices.md (engine selection, YAML schemas, troubleshooting)
- `sample/`: Example PDFs and YAML schemas for testing extractions
- `openspec/`: Project specifications using OpenSpec format for change management
- `tmp/`: Use this for temporary test outputs (not tracked in git)

## Commands

### OpenSpec

```bash
# List changes
openspec list

# List specs
openspec list --specs

# Show specific change or spec
openspec show <item-name>

# Validate change or spec
openspec validate <item-name>
```

### Running the tool

```bash
# Basic usage with Camelot (default, free, no API key)
alice-pdf input.pdf output/

# Specific pages
alice-pdf input.pdf output/ --pages "1-3,5"

# Camelot stream mode for tables without borders
alice-pdf input.pdf output/ --camelot-flavor stream

# Mistral engine for scanned PDFs (requires MISTRAL_API_KEY env var)
alice-pdf input.pdf output/ --engine mistral

# Mistral with custom schema for better accuracy
alice-pdf input.pdf output/ --engine mistral --schema table_schema.yaml

# Textract engine
alice-pdf input.pdf output/ --engine textract --aws-region eu-west-1

# Merge all tables into one CSV
alice-pdf input.pdf output/ --merge

# Debug mode
alice-pdf input.pdf output/ --debug
```

### Development

```bash
# Install in editable mode
uv tool install --editable .

# Test CLI
alice-pdf --version
alice-pdf --help
```

## Architecture

### alice_pdf/cli.py

Main CLI entry point with argparse configuration.

- Handles command-line arguments
- Sets up logging
- Loads API key from env var or --api-key flag
- Generates prompt from schema if --schema is provided
- Calls `extract_tables()` from extractor module

### alice_pdf/extractor.py

Core extraction logic with three main functions:

- `pdf_page_to_base64()` (extractor.py:21): Converts PDF page to base64 image using PyMuPDF and PIL
- `extract_tables_with_mistral()` (extractor.py:52): Sends image + prompt to Mistral API, parses JSON response with markdown code block handling
- `extract_tables()` (extractor.py:132): Orchestrates processing, handles page ranges, merges outputs

Key features:

- Clears output directory on each run (extractor.py:154-157)
- Adds 'page' column to track source pages
- Standardizes column names (spaces → underscores) before merging
- Sorts merged output by page number
- Progressive timeout retry: on timeout, retries with increased timeouts (60s → 90s → 120s) before skipping page (extractor.py:267-315)

### alice_pdf/prompt_generator.py

Schema-to-prompt converter that reads YAML/JSON table schemas and generates structured prompts for Mistral API.

- `generate_prompt_from_schema()` (prompt_generator.py:10): Builds detailed prompt with column descriptions, examples, and critical notes from schema

### table_schema.yaml

Template defining expected table structure:

- Column definitions with names, descriptions, examples
- Notes section for critical extraction rules (e.g., "do NOT merge adjacent cells")

## Dependencies

- `fitz` (PyMuPDF): PDF manipulation
- `PIL` (Pillow): Image processing
- `mistralai`: Mistral API client
- `pandas`: CSV output
- `pyyaml`: Schema parsing

Install with: `uv tool install alice-pdf` or for development: `uv tool install --editable .`

## Versioning

This project uses **Semantic Versioning (SemVer) automatico** con **Conventional Commits**:

### Version Format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (non retrocompatibili)
- **MINOR**: Nuove features (retrocompatibili)
- **PATCH**: Bug fixes (retrocompatibili)

### Conventional Commits

```bash
# Features (incrementa MINOR)
git commit -m "feat: add hierarchical output support"
git commit -m "feat(mistral): improve OCR accuracy"

# Bug fixes (incrementa PATCH)
git commit -m "fix: handle timeout errors gracefully"
git commit -m "fix(camelot): resolve parsing edge cases"

# Breaking changes (incrementa MAJOR)
git commit -m "BREAKING: rename --api-key to --mistral-api-key"

# Documentazione e manutenzione (non cambiano versione)
git commit -m "docs: update installation guide"
git commit -m "chore: upgrade dependencies"
git commit -m "test: add integration tests"
```

### Automatic Release Setup

Il progetto è configurato per versioning automatico tramite GitHub Actions:

1. **Automatico su merge in `main`**: I commit triggerano analisi SemVer
2. **Release GitHub**: Crea automaticamente tag e release notes
3. **Changelog**: Generato automaticamente dai commit messaggi
4. **Package version**: Aggiornata in `pyproject.toml` e `__init__.py`

### Vantaggi

- **Zero gestione manuale** delle versioni
- **Release automatiche** senza intervento umano
- **Changelog sempre aggiornato**
- **Prevenzione errori** di versioning

Per i developer: Seguire strictly le Conventional Commits per garantire versioning corretto.

## Key Design Decisions

- Output directory is cleared on each run to ensure clean state
- Default DPI is 150 for balance between quality and performance
- JSON parsing handles markdown code blocks (```json) from API responses
- Column standardization (space → underscore) before merge to handle variations
- Page tracking via inserted 'page' column for traceability
- Progressive timeout retry: 3 attempts with doubled timeouts (60s, 120s, 240s) to handle slow pages before giving up
- Only timeout errors trigger retry; other API errors (auth, limits) skip immediately
