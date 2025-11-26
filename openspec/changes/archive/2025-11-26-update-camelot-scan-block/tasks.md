## 1. Preflight detection
- [ ] Add a Camelot-only preflight that checks if the PDF is scanned (e.g., no extractable text across selected pages) using existing PDF tooling.
- [ ] Fail fast with a clear, user-facing error when scanned; include hint to use `--engine textract` or `mistral`.

## 2. Wiring & logging
- [ ] Ensure CLI surfaces the scan-block error with exit code 1 and without partial outputs.
- [ ] Keep resume/merge behavior unchanged for valid PDFs.

## 3. Tests/validation
- [ ] Add/adjust tests or fixtures to cover scanned-PDF detection path.
- [ ] Run relevant test/CLI command to demonstrate failure on scanned sample (or mock).

## 4. Spec alignment
- [ ] Update extraction-workflow spec delta for the new Camelot scanned-PDF guard.
- [ ] Run `openspec validate update-camelot-scan-block --strict` and fix any findings.
