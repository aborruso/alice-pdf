# Change: Increase API timeout to 60 seconds

## Why

Current 30-second timeout is insufficient for slower API responses or complex pages. Users need more time for API to process images before skipping to next page.

## What Changes

- Increase default `--timeout-ms` from 30000 to 60000 milliseconds
- Update help text and documentation to reflect new default

## Impact

- Affected specs: api-timeout
- Affected code: alice_pdf/cli.py (default parameter), README.md (documentation)
- Users: Slower processing but fewer skipped pages due to timeout
