# Best Practices for alice-pdf

Comprehensive guide for optimal table extraction from PDFs.

## Development Guidelines

### Conventional Commits

Per contribuire al progetto, usa i **Conventional Commits** per versioning automatico:

```bash
# Nuove funzionalità (incrementa MINOR)
git commit -m "feat: add support for hierarchical table output"
git commit -m "feat(mistral): implement retry mechanism for API timeouts"

# Bug fixes (incrementa PATCH)
git commit -m "fix: resolve CSV encoding issues with special characters"
git commit -m "fix(camelot): handle tables without borders properly"

# Breaking changes (incrementa MAJOR)
git commit -m "BREAKING: rename --pdf-path to --input-file for consistency"

# Documentazione (no cambio versione)
git commit -m "docs: add migration guide for v2.0 breaking changes"
git commit -m "docs(best-practices): update Conventional Commits section"

# Manutenzione (no cambio versione)
git commit -m "chore: upgrade dependencies to latest stable versions"
git commit -m "chore: improve error messages for missing API keys"

# Test (no cambio versione)
git commit -m "test: add integration tests for all three engines"
git commit -m "test: add edge case tests for malformed PDFs"
```

### Messaggi Commit Pattern

```bash
# Format: type[scope]: description

# Types disponibili:
feat:     # Nuove features
fix:      # Bug fixes
docs:     # Documentazione
style:    # Formatting, style changes
refactor: # Code refactoring
test:     # Test aggiuntivi
chore:    # Manutenzione, dependencies

# Scope opzionale (engine interessato):
feat(mistral): # Cambiamenti specifici a engine mistral
fix(textract): # Bug fixes per textract
feat(camelot): # Features per camelot
feat(cli):     # Modifiche alla CLI
```

### Versioning Automatico

Il progetto usa **Semantic Versioning (SemVer) automatico**:

1. **Push su `main`** → GitHub Actions analizza i commit
2. **Calcolo versione** → Basato su Conventional Commits
3. **Release GitHub** → Creata automaticamente con changelog
4. **Tag Git** → Applicato automaticamente

**NON aggiornare manualmente** i numeri di versione in:
- `pyproject.toml`
- `alice_pdf/__init__.py`
- `alice_pdf/cli.py`

Vengono aggiornati automaticamente durante il processo di release.

## Choosing the Right Engine

alice-pdf supports three extraction engines (`--engine`):

### Mistral OCR (default)

**When to use**:

- Scanned PDFs or images
- Complex tables with merged cells or irregular layouts
- When semantic interpretation of data is needed

**Pros**:

- Works on any PDF (including scans)
- Interprets content semantically
- Handles complex layouts

**Cons**:

- Requires Mistral API key (cost per token)
- May misinterpret without schema
- Slower than Camelot

**How to optimize**:

**ALWAYS use a YAML schema** for complex tables. Without schema, the API may put data in wrong columns.

### AWS Textract

**When to use**:

- Scanned PDFs or complex documents
- When you already have AWS credentials
- For batch processing of large volumes

**Pros**:

- Enterprise-grade AWS OCR
- Excellent for multi-page documents
- Form and key-value pair extraction

**Cons**:

- Requires AWS credentials
- Cost per page processed
- More complex setup

### Camelot

**When to use**:

- Native PDFs (NOT scans)
- Tables with clear borders (lattice mode)
- When you have NO budget for APIs

**Pros**:

- Free, no API required
- Very fast
- Excellent for native PDFs with borders

**Cons**:

- Does NOT work on scanned PDFs
- Requires extractable text in PDF
- May fail on borderless layouts

**Options**:

- `--camelot-flavor lattice`: for tables with borders (default)
- `--camelot-flavor stream`: for tables without borders

## Writing YAML Schemas for Mistral

A YAML schema is **essential** for accurate extraction with Mistral.

### Schema Structure

```yaml
name: "table_name"
description: "Brief table description"

columns:
  - name: "COLUMN_NAME"
    description: "What this column contains"
    examples:
      - "example 1"
      - "example 2"
      - "example 3"

  - name: "ANOTHER_COLUMN"
    description: "..."
    examples:
      - "..."

notes:
  - "Critical note 1: specific instructions for the API"
  - "Critical note 2: what NOT to do"
```

### Key Elements

**1. Column Names**

Use names that exactly reflect the headers in the PDF (case, spaces, underscores).

```yaml
# If PDF has "TIPO CANONE", use:
- name: "TIPO_CANONE"  # or "TIPO CANONE" if you prefer
```

**2. Description**

Explain the semantic content, don't just repeat the name.

```yaml
# ❌ Bad
description: "Fee type"

# ✅ Good
description: "Type of rental fee: 'percepito' (received) or 'corrisposto' (paid)"
```

**3. Examples**

Provide 2-4 REAL examples from the PDF. They help the API understand the format.

```yaml
examples:
  - "€ 6.923,03"   # with thousands separator
  - "€ 3.349,12"   # without thousands separator
  - "€ 2.750,00"   # round amount
```

**4. Notes - CRITICAL**

Notes guide the API on critical cases. Use clear imperative sentences.

```yaml
notes:
  - "CRITICAL: The IMPORTO column must contain BOTH the € symbol AND amount together"
  - "CRITICAL: Do NOT put € symbol in PIVA_CODFISC column - it belongs in IMPORTO"
  - "All rows must have exactly 10 columns"
  - "Empty cells should be empty strings, not omitted"
```

### Complete Example: Rental Fees Table

```yaml
name: "rental_fees"
description: "Rental fees and lease contract information table"

columns:
  - name: "TIPO_CANONE"
    description: "Type of rental fee (percepito/corrisposto)"
    examples:
      - "percepito"
      - "corrisposto"

  - name: "IMPORTO"
    description: "Amount in euros - MUST include € symbol and numeric value together"
    examples:
      - "€ 6.923,03"
      - "€ 3.349,12"
      - "€ 2.750,00"

  - name: "ESTREMI_CONTRATTO"
    description: "Contract reference (contract number, deed, often empty)"
    examples:
      - "Atto di subentro n. 16"
      - "Contratto n. 21"
      - ""

notes:
  - "CRITICAL: IMPORTO must contain € symbol AND amount together (e.g., '€ 6.923,03')"
  - "All rows must have exactly N columns"
  - "Empty cells should be empty strings"
```

## Common Use Cases

### Basic Extraction Without Schema

For quick tests or very simple tables only:

```bash
alice-pdf input.pdf output/
```

⚠️ **Risks**: wrong columns, mixed data

### Extraction With Schema (RECOMMENDED)

```bash
# 1. Create schema by inspecting the PDF
cat > schema.yaml << 'EOF'
name: "my_table"
columns:
  - name: "COL1"
    description: "..."
    examples: ["...", "..."]
notes:
  - "CRITICAL: ..."
EOF

# 2. Run extraction
alice-pdf input.pdf output/ --schema schema.yaml
```

### Specific Pages

```bash
# Single page
alice-pdf input.pdf output/ --pages 1

# Range
alice-pdf input.pdf output/ --pages 1-5

# List
alice-pdf input.pdf output/ --pages 1,3,5,7-10

# All pages (default)
alice-pdf input.pdf output/
```

### Merge Output

Combines all CSVs into a single file:

```bash
alice-pdf input.pdf output/ --merge

# Generates:
# - output/input_page1_table0.csv
# - output/input_page2_table0.csv
# - output/input_merged.csv  ← all tables combined
```

⚠️ **Note**: merge standardizes column names (spaces → underscores)

### Debug Issues

```bash
# See raw API response
alice-pdf input.pdf output/ --debug

# Increase timeout for slow pages
alice-pdf input.pdf output/ --timeout-ms 120000  # 2 minutes
```

## Troubleshooting

### "X columns passed, data had Y columns"

**Cause**: API returns rows with different number of columns than headers

**Solution**:

1. Create YAML schema with precise examples
2. Add critical notes about column count
3. alice-pdf now pads/trims automatically (with warning)

### Data in Wrong Columns (e.g., € in P.IVA column)

**Cause**: API misinterprets structure without schema

**Solution**: Create schema with CRITICAL notes:

```yaml
notes:
  - "CRITICAL: Column X must contain Y, NOT Z"
  - "CRITICAL: Do NOT put symbol € in column A - it belongs in column B"
```

### Timeout on Complex Pages

**Cause**: API takes too long

**Solution**:

```bash
# Increase timeout (default 60s)
alice-pdf input.pdf output/ --timeout-ms 120000

# alice-pdf retries automatically with doubled timeout:
# - Attempt 1: 60s
# - Attempt 2: 120s
# - Attempt 3: 240s
```

### Camelot Doesn't Find Tables

**Cause**: Scanned PDF or borderless table

**Solutions**:

```bash
# 1. Try stream mode instead of lattice
alice-pdf input.pdf output/ --engine camelot --camelot-flavor stream

# 2. If scanned, use Mistral
alice-pdf input.pdf output/ --engine mistral --schema schema.yaml
```

## Recommended Workflow

### 1. Initial Analysis

```bash
# Test first page without schema
alice-pdf input.pdf test/ --pages 1 --debug
```

### 2. Schema Creation

Review output and create `schema.yaml` with:

- Exact column names
- Real examples from the PDF
- Critical notes for issues found

### 3. Test With Schema

```bash
# Retry first page with schema
alice-pdf input.pdf test/ --pages 1 --schema schema.yaml
```

### 4. Full Extraction

```bash
# If test OK, extract everything
alice-pdf input.pdf output/ --schema schema.yaml --merge
```

### 5. Validation

```bash
# Check output
head output/input_merged.csv
wc -l output/input_merged.csv
```

## Performance and Costs

### Mistral API

- **Cost**: ~$0.001-0.005 per page (depends on image size)
- **Speed**: 5-15 seconds per page
- **Rate limit**: 1 req/sec (alice-pdf handles automatically)

**Optimizations**:

- Use `--pages` to process only needed pages
- Default DPI of 150 is optimal (quality/cost balance)
- Schema reduces output tokens = lower cost

### AWS Textract

- **Cost**: $0.0015 per page (DetectDocumentText)
- **Speed**: 1-3 seconds per page
- **Limit**: 1000 pages/request

### Camelot

- **Cost**: zero
- **Speed**: <1 second per page
- **Limit**: native PDFs only

## Example: Real Project

```bash
# Setup
mkdir extraction_project
cd extraction_project
export MISTRAL_API_KEY="your-key"

# 1. Test first page
alice-pdf document.pdf test/ --pages 1 --debug > debug.log

# 2. Analyze debug.log and create schema
cat > document_schema.yaml << 'EOF'
name: "rental_fees"
description: "Municipal rental fees table"

columns:
  - name: "TIPO_CANONE"
    description: "Fee type"
    examples: ["percepito", "corrisposto"]

  - name: "IMPORTO"
    description: "Amount with € symbol"
    examples: ["€ 6.923,03", "€ 3.349,12"]

  # ... other columns ...

notes:
  - "CRITICAL: IMPORTO must include € and amount together"
  - "All rows have exactly 10 columns"
EOF

# 3. Test schema
alice-pdf document.pdf test/ --pages 1-3 --schema document_schema.yaml

# 4. Full extraction if OK
alice-pdf document.pdf final_output/ \
  --schema document_schema.yaml \
  --merge \
  --timeout-ms 90000

# 5. Verify
wc -l final_output/*.csv
head final_output/document_merged.csv
```
