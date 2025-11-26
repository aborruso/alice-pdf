# extraction-workflow Specification

## Purpose
TBD - created by archiving change update-camelot-scan-block. Update Purpose after archive.
## Requirements
### Requirement: Camelot Scan Guard
The system SHALL detect image-only (scanned) PDFs before invoking Camelot and abort Camelot extraction with a clear error.

#### Scenario: Scanned PDF blocked
- **WHEN** the user selects `--engine camelot` for a PDF whose selected pages have no extractable text
- **THEN** the tool SHALL stop before extraction
- **AND** exit with a non-zero status and an error message that Camelot cannot process scanned PDFs
- **AND** suggest using a different engine (e.g., `textract` or `mistral`).

#### Scenario: Native PDF allowed
- **WHEN** the user selects `--engine camelot` for a PDF whose selected pages contain extractable text
- **THEN** Camelot extraction proceeds as today (respecting flavor, merge, resume options).

### Requirement: Engine Routing

The system SHALL route to the correct extraction engine based on `--engine` parameter including Camelot.

#### Scenario: Camelot engine routing

- **WHEN** `--engine camelot`
- **THEN** `camelot_extractor.extract_tables_with_camelot()` is called with flavor parameter

### Requirement: Common Parameters

The system SHALL pass common parameters to both extraction engines.

#### Scenario: Common parameters passed

- **WHEN** un motore viene invocato
- **THEN** riceve parametri comuni: `pdf_path`, `output_dir`, `pages`, `dpi`, `merge_output`, `resume`

### Requirement: Textract-Specific Behavior

The system SHALL handle Textract-specific behavior correctly.

#### Scenario: No schema/prompt support

- **WHEN** viene usato Textract
- **THEN** non viene generato prompt da schema (Textract estrae tabelle senza prompt strutturato)

#### Scenario: Textract API timeout

- **WHEN** Textract API supera il timeout
- **THEN** la pagina viene saltata con warning (no retry automatico come Mistral)

### Requirement: Camelot Extraction

The system SHALL extract tables from PDF using Camelot library.

#### Scenario: Lattice mode extraction

- **WHEN** Camelot is invoked with `flavor='lattice'`
- **THEN** tables are detected using border lines
- **AND** output CSV files are created per table per page

#### Scenario: Stream mode extraction

- **WHEN** Camelot is invoked with `flavor='stream'`
- **THEN** tables are detected using whitespace/alignment
- **AND** output CSV files are created per table per page

### Requirement: Camelot Page Processing

The system SHALL process PDF pages with Camelot using common parameters.

#### Scenario: Page selection

- **WHEN** pages parameter is provided (e.g., "1-3,5")
- **THEN** only specified pages are processed with Camelot

#### Scenario: Merge output

- **WHEN** merge_output is True
- **THEN** all Camelot-extracted tables are merged into single CSV with page column

### Requirement: Camelot Error Handling

The system SHALL handle Camelot-specific errors gracefully.

#### Scenario: No tables found

- **WHEN** Camelot finds no tables on a page
- **THEN** page is logged with warning and skipped
- **AND** processing continues with next page

#### Scenario: PDF parsing error

- **WHEN** Camelot fails to parse a page
- **THEN** error is logged with page number
- **AND** page is added to failed_pages list
- **AND** processing continues with next page

