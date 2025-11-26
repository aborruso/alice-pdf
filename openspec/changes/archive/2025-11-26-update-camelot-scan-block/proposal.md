# Change: Block Camelot on scanned PDFs

## Why
- Camelot fails or produces empty tables on scanned (image-only) PDFs.
- Users should get a clear, early error instead of partial/garbled output.

## What Changes
- Detect whether the input PDF is scanned before running Camelot.
- If scanned, abort Camelot extraction with a helpful message suggesting other engines.
- Keep existing Camelot behavior unchanged for native/text PDFs.

## Impact
- Affected specs: extraction-workflow (Camelot preflight/guardrail)
- Affected code: `alice_pdf/camelot_extractor.py`, possibly CLI error handling/logging
