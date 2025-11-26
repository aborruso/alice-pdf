# Extraction Workflow

## ADDED Requirements

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
