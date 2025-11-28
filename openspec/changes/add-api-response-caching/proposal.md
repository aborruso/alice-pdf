# Change: Add API Response Caching

## Why

Repeated processing of same pages wastes tokens and API costs. When debugging prompts or experimenting with schemas, users must re-process pages they already extracted. Raw API responses are lost after CSV conversion, making offline analysis impossible.

## What Changes

- Cache raw API responses (JSON) alongside CSV outputs
- Resume from cache when available (skip API calls)
- Enable offline experimentation with cached responses
- Provide `--no-cache` flag to force fresh API calls

## Impact

- Affected specs: `extraction-workflow`
- Affected code:
  - `alice_pdf/extractor.py` (save/load cache logic)
  - `alice_pdf/textract_extractor.py` (save/load cache logic)
  - `alice_pdf/cli.py` (add --no-cache flag)
- Reduces API costs for iterative workflows
- Enables debugging without re-processing
