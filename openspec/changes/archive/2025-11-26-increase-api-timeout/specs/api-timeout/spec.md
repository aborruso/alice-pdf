# Spec Delta: API Timeout Configuration

## MODIFIED Requirements

### Requirement: Default API Timeout Value

The CLI SHALL use a default timeout of 60 seconds (60000 milliseconds) for Mistral API requests.

#### Scenario: User runs CLI without timeout flag

- **WHEN** user executes `alice-pdf input.pdf output/` without `--timeout-ms` flag
- **THEN** system uses 60000ms timeout for API requests

#### Scenario: User overrides timeout

- **WHEN** user executes `alice-pdf input.pdf output/ --timeout-ms 45000`
- **THEN** system uses 45000ms timeout instead of default

### Requirement: Timeout Documentation

Help text and documentation SHALL reflect 60-second default timeout.

#### Scenario: User checks help text

- **WHEN** user runs `alice-pdf --help`
- **THEN** `--timeout-ms` help text shows "default: 60000"

#### Scenario: User reads README

- **WHEN** user reads README.md
- **THEN** timeout documentation mentions 60-second default
