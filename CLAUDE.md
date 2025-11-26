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

Alice PDF is a CLI tool for extracting tables from PDFs using Mistral OCR (Pixtral vision model). It converts PDF pages to images at specified DPI, sends them to Mistral API with custom prompts, and outputs CSV files.

Core workflow:

1. PDF → temp raster copy at 150 DPI
2. Process selected pages (ranges or lists)
3. Send to Mistral API with optional YAML schema describing table structure
4. Get CSV per page + optional merged output

## Engines

- `mistral` (default): OCR via Pixtral vision. Supports `--schema` and `--prompt`.
- `textract`: AWS Textract. Needs AWS creds via env or flags (`--aws-region`, `--aws-access-key-id`, `--aws-secret-access-key`).
- `camelot`: Native PDF tables. Use `--camelot-flavor {lattice,stream}`; blocked on scanned PDFs (no extractable text).

## Commands

### Running the tool

```bash
# Basic usage (requires MISTRAL_API_KEY env var)
alice-pdf input.pdf output/

# Specific pages
alice-pdf input.pdf output/ --pages "1-3,5"

# With custom schema for better accuracy
alice-pdf input.pdf output/ --schema table_schema.yaml

# Textract engine (example)
alice-pdf input.pdf output/ --engine textract --aws-region eu-west-1

# Camelot stream mode
alice-pdf input.pdf output/ --engine camelot --camelot-flavor stream

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

## Key Design Decisions

- Output directory is cleared on each run to ensure clean state
- Default DPI is 150 for balance between quality and performance
- JSON parsing handles markdown code blocks (```json) from API responses
- Column standardization (space → underscore) before merge to handle variations
- Page tracking via inserted 'page' column for traceability
- Progressive timeout retry: 3 attempts with doubled timeouts (60s, 120s, 240s) to handle slow pages before giving up
- Only timeout errors trigger retry; other API errors (auth, limits) skip immediately
