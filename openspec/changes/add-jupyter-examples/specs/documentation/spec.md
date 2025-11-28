## ADDED Requirements

### Requirement: Jupyter Example Notebook

The documentation SHALL include a Jupyter notebook demonstrating interactive extraction workflows.

#### Scenario: Basic extraction example

- **WHEN** user opens `sample/extraction_example.ipynb`
- **THEN** notebook contains working code cells for extracting tables
- **AND** includes inline visualization of extracted tables
- **AND** runs without errors on sample PDFs

#### Scenario: Parameter exploration

- **WHEN** user follows parameter exploration section
- **THEN** notebook demonstrates testing different DPI values
- **AND** compares extraction quality across engines
- **AND** shows inline pandas DataFrames for visual comparison

#### Scenario: Schema iteration workflow

- **WHEN** user follows schema iteration section
- **THEN** notebook demonstrates loading YAML schema
- **AND** shows iterating on schema definitions
- **AND** visualizes schema impact on extraction results

### Requirement: Cache Inspection Examples

The notebook SHALL demonstrate inspecting cached API responses for debugging.

#### Scenario: Reading cached responses

- **WHEN** user follows cache inspection section
- **THEN** notebook shows loading cached JSON responses
- **AND** demonstrates parsing raw API responses
- **AND** shows comparing cached vs fresh extractions

### Requirement: Installation Instructions

The documentation SHALL provide clear installation instructions for Jupyter support.

#### Scenario: Optional Jupyter dependencies

- **WHEN** user reads installation section
- **THEN** instructions include `pip install alice-pdf[jupyter]`
- **AND** list optional visualization dependencies
- **AND** explain when Jupyter support is useful

### Requirement: Multi-Engine Demonstration

The notebook SHALL demonstrate all three extraction engines.

#### Scenario: Engine comparison

- **WHEN** user follows multi-engine section
- **THEN** notebook shows extraction with Camelot, Mistral, Textract
- **AND** compares results on same PDF page
- **AND** highlights engine-specific strengths
