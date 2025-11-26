# Implementation Tasks

## 1. Core Retry Logic

- [x] 1.1 Add retry loop wrapper around extract_tables_with_mistral call (extractor.py:268-275)
- [x] 1.2 Implement timeout detection logic (check exception message for "timeout" or "timed out")
- [x] 1.3 Create new client instance with increased timeout on retry
- [x] 1.4 Implement 3-attempt limit with timeouts: 60s, 90s, 120s

## 2. Logging

- [x] 2.1 Add log message for retry attempt with timeout value and attempt number
- [x] 2.2 Add log message when all retries exhausted
- [x] 2.3 Preserve existing timeout error message for final failure

## 3. Error Handling

- [x] 3.1 Distinguish timeout errors from other API errors
- [x] 3.2 Skip retry for non-timeout errors (immediate continue to next page)
- [x] 3.3 Ensure failed_pages list includes pages that fail after all retries

## 4. Testing

- [ ] 4.1 Test timeout retry with mock slow API responses
- [ ] 4.2 Test successful extraction on second retry
- [ ] 4.3 Test page skip after 3 failed attempts
- [ ] 4.4 Test non-timeout errors skip retry logic
- [ ] 4.5 Verify log messages show correct attempt numbers and timeouts

## 5. Documentation

- [x] 5.1 Update CLAUDE.md to document retry behavior
- [x] 5.2 Update README.md to explain progressive retry feature
