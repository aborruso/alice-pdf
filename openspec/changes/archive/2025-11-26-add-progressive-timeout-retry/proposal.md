# Change: Add progressive timeout retry before skipping pages

## Why

When a page times out, immediately skipping loses potentially extractable data. Complex pages may need more time. Progressive retry with increased timeouts (60s → 90s → 120s) gives problematic pages multiple chances before giving up.

## What Changes

- Add retry logic with progressive timeout increases when timeout occurs
- Attempt 1: 60s (default timeout)
- Attempt 2: 90s (default + 30s)
- Attempt 3: 120s (default + 60s)
- After 3 failed attempts, skip page and continue
- Log each retry attempt with timeout value

## Impact

- Affected specs: timeout-retry
- Affected code: alice_pdf/extractor.py (extract_tables_with_mistral function and retry logic)
- Users: Better extraction success rate for slow pages, but longer processing time for problematic pages
- **BREAKING**: Changes function signature to accept retry configuration
