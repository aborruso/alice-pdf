# Project Context

## Purpose

Alice PDF is a CLI tool for extracting tables from PDF documents using Mistral OCR (Pixtral vision model). It converts PDF pages to images, sends them to Mistral API with structured prompts, and outputs machine-readable CSV files.

Key goals:

- Extract tables from multi-page PDFs with high accuracy
- Support flexible page selection (ranges or lists)
- Enable schema-driven extraction for improved accuracy
- Provide CSV output per page or merged into single file
- Offer simple CLI interface with sensible defaults

Dedicated to Alice Cortella, Marco Corona, and the onData community.

## Tech Stack

- **Python**: 3.8+ (core language)
- **PyMuPDF (fitz)**: PDF manipulation and page conversion
- **Pillow (PIL)**: Image processing
- **Mistral AI SDK**: API client for Pixtral vision model
- **Pandas**: DataFrame operations and CSV output
- **PyYAML**: Schema file parsing
- **argparse**: CLI argument handling
- **pytest**: Testing framework

Build tools:

- **hatchling**: Build backend
- **uv**: Package installation and dependency management

## Project Conventions

### Code Style

- Python3 with pip3 for package management
- Use `uv tool install` for CLI package installation
- Snake_case for functions, variables, and module names
- Clear, descriptive names over brevity
- Type hints encouraged but not required (Python 3.8 compatibility)
- Docstrings for modules and complex functions
- Line references in code discussions: `file_path:line_number` format

Markdown style:

- No numbered headings (hard to maintain)
- Empty line after colons before lists
- Empty line before/after code blocks with triple backticks

### Architecture Patterns

Three-layer architecture:

1. **CLI layer** (`cli.py`): Argument parsing, logging setup, API key management
2. **Orchestration layer** (`extractor.py`): Page processing, output management, merging
3. **Service layer** (`prompt_generator.py`): Schema-to-prompt conversion

Key design decisions:

- Output directory cleared on each run for clean state (unless `--resume` used)
- Page tracking via inserted 'page' column for traceability
- Column name standardization (space → underscore) before merge
- JSON parsing handles markdown code blocks from API responses
- Base64 image encoding for API transmission
- DPI default: 150 (balance quality/performance)

### Testing Strategy

- pytest for unit and integration tests
- Mock external API calls (Mistral API)
- Test fixtures for PDF samples
- Environment variable override: `ALICE_PDF_IGNORE_ENV=1` for testing missing keys
- Coverage tracking with pytest-cov
- Debug mode (`--debug`) for development troubleshooting

### Git Workflow

- Main branch: `main`
- Concise commit messages (sacrifice grammar for brevity)
- Use `gh` CLI for GitHub operations (not MCP server)
- `LOG.md` updated with key changes (YYYY-MM-DD headings, most recent first)
- OpenSpec workflow for major changes (see `@/openspec/AGENTS.md`)

## Domain Context

**PDF table extraction workflow:**

1. PDF pages → raster images at configurable DPI (default 150)
2. Images converted to base64 encoding
3. Sent to Mistral Pixtral vision model with structured prompt
4. Model returns JSON with table data (may be wrapped in markdown code blocks)
5. JSON parsed → pandas DataFrame → CSV files
6. Optional merge: all tables combined with 'page' column

**Schema-driven extraction:**

YAML/JSON schema describes expected table structure:

- Column names, descriptions, examples
- Critical extraction notes (e.g., "do NOT merge adjacent cells")
- Converted to detailed prompt via `generate_prompt_from_schema()`

## Important Constraints

- **Python version**: 3.8+ minimum (for broad compatibility)
- **Mistral API key**: Required via env var, CLI flag, or .env file
- **API rate limits**: Mistral API throttling may apply
- **Memory**: Images loaded in memory (high DPI + many pages = high RAM usage)
- **Output directory**: Cleared on each run unless `--resume` flag used
- **Page column**: Always inserted, may conflict with existing 'page' column in source tables

## External Dependencies

**Mistral API:**

- Service: Mistral AI Console (https://console.mistral.ai/)
- Model: `pixtral-12b-2409` (default, configurable)
- Authentication: API key via `MISTRAL_API_KEY` env var
- Timeout: Configurable via `--timeout-ms` (default 30000ms)
- Retry logic: Built-in for transient failures
- Response format: JSON (may be wrapped in markdown code blocks)

**Third-party libraries:**

- PyMuPDF: PDF parsing and rendering
- Pillow: Image format conversion
- Pandas: CSV I/O and data manipulation
- PyYAML: Schema file parsing
