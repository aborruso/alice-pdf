# Delta: Extraction Workflow

## ADDED Requirements

### Requirement: Hierarchical Output Organization

The system SHALL organize output files in subdirectories by artifact type.

#### Scenario: Default hierarchical layout

- **WHEN** user extracts `canoni.pdf` to `output/` without `--flat-output`
- **THEN** directory structure is:
  ```
  output/
    canoni/
      responses/
        canoni_page1_response.json
        canoni_page2_response.json
      tables/
        canoni_page1_table0.csv
        canoni_page2_table0.csv
      canoni_merged.csv
  ```

#### Scenario: Flat output compatibility

- **WHEN** user runs with `--flat-output` flag
- **THEN** all files placed directly in output_dir (legacy behavior)
- **AND** no subdirectories created

#### Scenario: Multiple PDFs organized separately

- **WHEN** user processes `doc1.pdf` and `doc2.pdf` to same output_dir
- **THEN** outputs organized as:
  ```
  output/
    doc1/
      responses/...
      tables/...
    doc2/
      responses/...
      tables/...
  ```

### Requirement: Merged File Location

Merged output SHALL be placed at PDF-specific root in hierarchical mode.

#### Scenario: Merged file in hierarchical mode

- **WHEN** user runs with `--merge` in hierarchical mode
- **THEN** merged CSV placed at `output/{pdf_stem}/{pdf_stem}_merged.csv`

#### Scenario: Merged file in flat mode

- **WHEN** user runs with `--merge --flat-output`
- **THEN** merged CSV placed at `output/{pdf_stem}_merged.csv` (legacy behavior)
