# cli-interface Specification

## Purpose
TBD - created by archiving change add-engine-option. Update Purpose after archive.
## Requirements
### Requirement: Engine Selection

The CLI SHALL allow engine selection via `--engine` option including Camelot.

#### Scenario: Camelot engine selection

- **WHEN** user runs `alice-pdf input.pdf output/ --engine camelot`
- **THEN** Camelot library is used for extraction

#### Scenario: Invalid engine with camelot option

- **WHEN** user specifies `--engine unknown`
- **THEN** CLI exits with error showing valid engines: `mistral`, `textract`, `camelot`

### Requirement: AWS Textract Configuration

The CLI SHALL provide options to configure AWS Textract credentials and region.

#### Scenario: AWS credentials via CLI args

- **WHEN** l'utente esegue `alice-pdf input.pdf output/ --engine textract --aws-access-key-id KEY --aws-secret-access-key SECRET --aws-region eu-west-1`
- **THEN** Textract usa le credenziali specificate via argomenti

#### Scenario: AWS credentials via env vars

- **WHEN** l'utente esegue `alice-pdf input.pdf output/ --engine textract` con `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` configurati
- **THEN** Textract usa le credenziali da environment variables

#### Scenario: Missing boto3 dependency

- **WHEN** l'utente esegue `alice-pdf --engine textract` ma boto3 non è installato
- **THEN** il CLI termina con errore chiaro: `boto3 is required for Textract. Install with: pip install boto3`

### Requirement: Engine-Specific Options Validation

The CLI SHALL validate that engine-specific options are not used with incompatible engines.

#### Scenario: Mistral options with Textract

- **WHEN** l'utente esegue `alice-pdf input.pdf output/ --engine textract --schema table.yaml`
- **THEN** il CLI termina con errore: `--schema is only compatible with --engine mistral`

#### Scenario: Prompt option with Textract

- **WHEN** l'utente esegue `alice-pdf input.pdf output/ --engine textract --prompt "Extract table"`
- **THEN** il CLI termina con errore: `--prompt is only compatible with --engine mistral`

#### Scenario: Model option with Textract

- **WHEN** l'utente esegue `alice-pdf input.pdf output/ --engine textract --model pixtral-12b`
- **THEN** il CLI termina con errore: `--model is only compatible with --engine mistral`

### Requirement: Help Documentation

The CLI help output SHALL clearly document options for each engine.

#### Scenario: Help output includes engine info

- **WHEN** l'utente esegue `alice-pdf --help`
- **THEN** l'output include:
  - Descrizione opzione `--engine {mistral,textract}`
  - Elenco opzioni specifiche Mistral: `--schema`, `--prompt`, `--model`, `--api-key`, `--timeout-ms`
  - Elenco opzioni specifiche Textract: `--aws-region`, `--aws-access-key-id`, `--aws-secret-access-key`

### Requirement: Camelot Flavor Selection

The CLI SHALL provide option to select Camelot extraction flavor.

#### Scenario: Default lattice flavor

- **WHEN** user runs `alice-pdf input.pdf output/ --engine camelot` without `--camelot-flavor`
- **THEN** Camelot uses `lattice` mode (table borders detection)

#### Scenario: Stream flavor

- **WHEN** user runs `alice-pdf input.pdf output/ --engine camelot --camelot-flavor stream`
- **THEN** Camelot uses `stream` mode (whitespace detection)

#### Scenario: Invalid flavor

- **WHEN** user specifies `--camelot-flavor invalid`
- **THEN** CLI exits with error showing valid flavors: `lattice`, `stream`

### Requirement: Camelot Dependency Check

The CLI SHALL check for camelot-py installation when using Camelot engine.

#### Scenario: Missing camelot-py

- **WHEN** user runs `alice-pdf --engine camelot` but camelot-py is not installed
- **THEN** CLI exits with error: `Camelot support requires camelot-py. Install with: pip install camelot-py[cv]`

#### Scenario: Camelot installed

- **WHEN** user runs `alice-pdf --engine camelot` and camelot-py is installed
- **THEN** extraction proceeds normally

