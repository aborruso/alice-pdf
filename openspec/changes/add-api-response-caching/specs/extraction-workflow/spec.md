# Delta: Extraction Workflow

## ADDED Requirements

### Requirement: API Response Caching

The system SHALL cache raw API responses to avoid redundant API calls and enable offline analysis.

#### Scenario: First extraction caches response

- **WHEN** user extracts page 3 with Mistral engine
- **THEN** raw JSON response saved to `output_dir/responses/{pdf_stem}_page3_response.json`

#### Scenario: Cache hit skips API call

- **WHEN** user re-extracts page 3 and cache exists
- **THEN** system loads cached response instead of calling API
- **AND** logs "Page 3: loaded from cache"

#### Scenario: No-cache flag forces fresh API call

- **WHEN** user runs with `--no-cache` flag
- **THEN** system ignores existing cache
- **AND** makes fresh API call
- **AND** overwrites cache with new response

#### Scenario: Cache works with page ranges

- **WHEN** user extracts pages 1-5
- **AND** cache exists for pages 1,3
- **THEN** system loads cache for pages 1,3
- **AND** calls API only for pages 2,4,5

### Requirement: Cache Storage Format

Cached responses SHALL be stored as JSON files with specific naming convention.

#### Scenario: Cache file naming

- **WHEN** processing `canoni.pdf` page 7
- **THEN** cache stored as `responses/canoni_page7_response.json`

#### Scenario: Cache directory creation

- **WHEN** first cache write occurs
- **THEN** system creates `output_dir/responses/` directory
- **AND** sets appropriate permissions

## MODIFIED Requirements

### Requirement: Resume Processing

The system SHALL resume processing by loading existing outputs or cached responses.

#### Scenario: Resume from CSV files

- **WHEN** CSV files exist for pages 1-3
- **THEN** skip processing those pages
- **AND** process remaining pages

#### Scenario: Resume from cache

- **WHEN** cache exists but CSV missing
- **THEN** load cached API response
- **AND** regenerate CSV from cache
- **AND** skip API call
