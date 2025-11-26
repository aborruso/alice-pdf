# CLI Interface

## MODIFIED Requirements

### Requirement: Engine Selection

The CLI SHALL allow engine selection via `--engine` option including Camelot.

#### Scenario: Camelot engine selection

- **WHEN** user runs `alice-pdf input.pdf output/ --engine camelot`
- **THEN** Camelot library is used for extraction

#### Scenario: Invalid engine with camelot option

- **WHEN** user specifies `--engine unknown`
- **THEN** CLI exits with error showing valid engines: `mistral`, `textract`, `camelot`

## ADDED Requirements

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
