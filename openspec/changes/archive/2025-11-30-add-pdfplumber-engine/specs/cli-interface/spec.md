## ADDED Requirements
### Requirement: pdfplumber Engine Selection
The CLI SHALL allow engine selection via `--engine` option including pdfplumber.

#### Scenario: pdfplumber engine selection
- **WHEN** user runs `alice-pdf input.pdf output/ --engine pdfplumber`
- **THEN** pdfplumber library is used for extraction

#### Scenario: Engine choices help
- **WHEN** user runs `alice-pdf --help`
- **THEN** engine choices show: `mistral`, `textract`, `camelot`, `pdfplumber`

### Requirement: pdfplumber Engine Configuration
The CLI SHALL provide options to configure pdfplumber table extraction settings.

#### Scenario: Default pdfplumber settings
- **WHEN** user runs `alice-pdf input.pdf output/ --engine pdfplumber`
- **THEN** pdfplumber uses default table detection settings
- **AND** extracts tables using vertical and horizontal line boundaries

#### Scenario: PDF table boundaries
- **WHEN** pdfplumber processes a PDF
- **THEN** it analyzes text positioning and whitespace to detect table structure
- **AND** extracts cells based on text coordinate boundaries

#### Scenario: pdfplumber dependency missing
- **WHEN** user runs `alice-pdf --engine pdfplumber` but pdfplumber is not installed
- **THEN** CLI exits with error: `pdfplumber support required. Install with: pip install pdfplumber`

### Requirement: Engine-Specific Options Validation
The CLI SHALL validate that engine-specific options are not used with incompatible engines.

#### Scenario: Mistral options with pdfplumber
- **WHEN** user runs `alice-pdf input.pdf output/ --engine pdfplumber --schema table.yaml`
- **THEN** CLI exits with error: `--schema is only compatible with --engine mistral`

#### Scenario: Textract options with pdfplumber
- **WHEN** user runs `alice-pdf input.pdf output/ --engine pdfplumber --aws-region eu-west-1`
- **THEN** CLI exits with error: `--aws-region is only compatible with --engine textract`

#### Scenario: Camelot options with pdfplumber
- **WHEN** user runs `alice-pdf input.pdf output/ --engine pdfplumber --camelot-flavor stream`
- **THEN** CLI exits with error: `--camelot-flavor is only compatible with --engine camelot`

## MODIFIED Requirements
### Requirement: Engine Selection
The CLI SHALL allow engine selection via `--engine` option including Camelot.

#### Scenario: Invalid engine with pdfplumber option
- **WHEN** user specifies `--engine unknown`
- **THEN** CLI exits with error showing valid engines: `mistral`, `textract`, `camelot`, `pdfplumber`