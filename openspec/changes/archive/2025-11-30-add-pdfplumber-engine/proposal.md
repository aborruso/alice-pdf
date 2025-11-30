# Change: Add pdfplumber as new extraction engine

## Why
Add pdfplumber as a fourth extraction engine option for users who need a balance between Camelot's text extraction limitations and the cost/API complexity of Mistral/Textract. pdfplumber offers better text extraction from scanned PDFs than Camelot while being completely free and local.

## What Changes
- Add `pdfplumber` option to `--engine` parameter in CLI
- Create new `pdfplumber_extractor.py` module following existing patterns
- Add pdfplumber-specific CLI options for table extraction settings
- Integrate pdfplumber engine into existing parameter routing system
- Add dependency check for pdfplumber installation
- Test on sample/test.pdf to validate effectiveness on scanned documents

## Impact
- Affected specs: `cli-interface`, `extraction-workflow`
- Affected code: `alice_pdf/cli.py`, `alice_pdf/pdfplumber_extractor.py` (new)
- Dependencies: Add pdfplumber as optional dependency
- User experience: New free engine option that works on both native and scanned PDFs