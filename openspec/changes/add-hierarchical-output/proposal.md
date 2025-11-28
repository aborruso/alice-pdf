# Change: Add Hierarchical Output Organization

## Why

Current flat output structure mixes all artifacts in single directory. With caching and multiple file types (CSVs, JSON responses, optional images), organization becomes chaotic. Difficult to find files and manage outputs from multiple PDFs.

## What Changes

- Organize outputs in subdirectories by type
- Create PDF-specific folders when processing multiple PDFs
- Maintain backward compatibility via `--flat-output` flag
- Group related artifacts (responses, tables, images) logically

## Impact

- Affected specs: `extraction-workflow`, `cli-interface`
- Affected code:
  - `alice_pdf/extractor.py` (directory structure logic)
  - `alice_pdf/textract_extractor.py` (directory structure logic)
  - `alice_pdf/camelot_extractor.py` (directory structure logic)
  - `alice_pdf/cli.py` (add --flat-output flag)
- Improves organization for batch processing
- Cleaner output directories
