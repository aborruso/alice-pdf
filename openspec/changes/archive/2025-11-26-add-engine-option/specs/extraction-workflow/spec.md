# Extraction Workflow

## ADDED Requirements

### Requirement: Engine Routing

The system SHALL route to the correct extraction engine based on `--engine` parameter.

#### Scenario: Mistral engine routing

- **WHEN** `--engine mistral` (o default)
- **THEN** viene chiamato `extractor.extract_tables()` con parametri Mistral (api_key, model, schema, prompt, timeout_ms)

#### Scenario: Textract engine routing

- **WHEN** `--engine textract`
- **THEN** viene chiamato `textract_extractor.extract_tables_with_textract()` con parametri AWS (region, access_key_id, secret_access_key)

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
