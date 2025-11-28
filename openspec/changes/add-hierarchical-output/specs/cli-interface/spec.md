# Delta: CLI Interface

## ADDED Requirements

### Requirement: Flat Output Flag

The system SHALL provide `--flat-output` flag for backward-compatible output structure.

#### Scenario: Flat output flag available

- **WHEN** user runs `alice-pdf --help`
- **THEN** `--flat-output` flag is documented
- **AND** description explains legacy flat directory structure

#### Scenario: Flat output overrides hierarchy

- **WHEN** user runs with `--flat-output`
- **THEN** all outputs placed directly in output_dir
- **AND** no PDF-specific subdirectories created
- **AND** no type-specific subdirectories (responses/, tables/) created
