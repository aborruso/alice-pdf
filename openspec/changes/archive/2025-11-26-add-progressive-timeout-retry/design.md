# Design: Progressive Timeout Retry

## Context

Current implementation uses Mistral client's built-in retry for connection errors but doesn't handle timeout retries progressively. When a timeout occurs, the page is skipped immediately. Complex pages may need more processing time, and a single timeout doesn't necessarily mean the page is unprocessable.

## Goals / Non-Goals

**Goals:**

- Retry timeout failures with progressively longer timeouts
- Three attempts total: 60s, 90s, 120s
- Clear logging of retry attempts
- Skip page only after all retries exhausted

**Non-Goals:**

- Retry non-timeout errors (auth, API limits, etc.)
- Make timeout configurable per retry (fixed progression)
- Implement exponential backoff (fixed +30s increments)

## Decisions

### Decision 1: Implement retry at extract_tables() level, not in extract_tables_with_mistral()

**Rationale:** The `extract_tables()` function already handles page iteration and error handling (extractor.py:267-275). Implementing retry here allows creating new client instances with different timeouts for each attempt.

**Alternative considered:** Modify `extract_tables_with_mistral()` to handle retries internally. Rejected because client timeout is set at initialization, requiring client recreation for each retry.

### Decision 2: Fixed timeout progression (60s → 90s → 120s)

**Rationale:** Simple, predictable behavior. 30-second increments provide meaningful additional time without excessive delays.

**Alternative considered:** Exponential backoff (60s → 120s → 240s). Rejected because 240s (4 minutes) per page is too long for typical use cases.

### Decision 3: Detect timeout via exception message inspection

**Rationale:** Mistral SDK doesn't expose specific timeout exception types. Message inspection is pragmatic and already used in current code (extractor.py:130).

**Alternative considered:** Wrap all API calls in timeout decorator. Rejected as more complex and doesn't leverage SDK's timeout handling.

## Implementation Strategy

1. Wrap `extract_tables_with_mistral()` call in retry loop at extractor.py:268
2. On timeout exception:
   - Log retry attempt with new timeout value
   - Create new client with increased timeout
   - Retry extraction
3. After 3 failed attempts, log final skip and continue to next page
4. Non-timeout exceptions skip retry and immediately continue

## Risks / Trade-offs

**Risk:** Problematic pages increase total processing time significantly (up to 4.5 minutes per page: 60+90+120 = 270s)

**Mitigation:** Users already have `--pages` flag to skip problematic pages in subsequent runs

**Trade-off:** More API calls and costs for pages that ultimately fail

**Justification:** Better extraction success rate worth the cost for most use cases

## Migration Plan

No migration needed - backward compatible behavior change. Existing users get automatic retry benefits.

## Open Questions

None
