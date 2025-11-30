## ADDED Requirements
### Requirement: pdfplumber Table Extraction
The system SHALL extract tables from PDF using pdfplumber library.

#### Scenario: pdfplumber table detection
- **WHEN** pdfplumber processes a PDF page
- **THEN** it detects table structures using text positioning and line analysis
- **AND** creates table objects with cell boundaries

#### Scenario: Scanned PDF processing
- **WHEN** pdfplumber processes a scanned PDF with extractable text
- **THEN** it extracts text and attempts table structure detection
- **AND** outputs CSV files per table per page

#### Scenario: Native PDF processing
- **WHEN** pdfplumber processes a native PDF with text
- **THEN** it extracts text coordinates and detects table boundaries
- **AND** creates structured table data

### Requirement: pdfplumber Page Processing
The system SHALL process PDF pages with pdfplumber using common parameters.

#### Scenario: Page selection
- **WHEN** pages parameter is provided (e.g., "1-3,5")
- **THEN** only specified pages are processed with pdfplumber

#### Scenario: Merge output
- **WHEN** merge_output is True
- **THEN** all pdfplumber-extracted tables are merged into single CSV with page column

#### Scenario: Resume processing
- **WHEN** resume is True and page CSV already exists
- **THEN** pdfplumber skips processing that page and loads existing CSV for merge

### Requirement: pdfplumber Error Handling
The system SHALL handle pdfplumber-specific errors gracefully.

#### Scenario: No tables found
- **WHEN** pdfplumber finds no tables on a page
- **THEN** page is logged with warning and skipped
- **AND** processing continues with next page

#### Scenario: PDF parsing error
- **WHEN** pdfplumber fails to parse a page
- **THEN** error is logged with page number
- **AND** page is added to failed_pages list
- **AND** processing continues with next page

#### Scenario: Empty table extraction
- **WHEN** pdfplumber extracts a table with no data
- **THEN** table is logged as empty and skipped
- **AND** processing continues with next table

### Requirement: pdfplumber Engine Routing
The system SHALL route to pdfplumber extraction engine based on `--engine pdfplumber` parameter.

#### Scenario: pdfplumber engine routing
- **WHEN** `--engine pdfplumber` is specified
- **THEN** `pdfplumber_extractor.extract_tables_with_pdfplumber()` is called with common parameters

#### Scenario: Common parameters passed
- **WHEN** pdfplumber engine is invoked
- **THEN** it receives common parameters: `pdf_path`, `output_dir`, `pages`, `merge_output`, `resume`

## MODIFIED Requirements
### Requirement: Engine Routing

The system SHALL route to the correct extraction engine based on `--engine` parameter including Camelot.

#### Scenario: pdfplumber engine routing
- **WHEN** `--engine pdfplumber`
- **THEN** `pdfplumber_extractor.extract_tables_with_pdfplumber()` is called