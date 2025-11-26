# Timeout Retry Capability

## Purpose

Provide robust error handling for API timeouts through progressive retry logic with configurable timeouts and comprehensive logging.

## Requirements

### Requirement: Progressive Timeout Retry on Failure

When a page extraction times out, the system SHALL retry with progressively longer timeouts before skipping.

#### Scenario: First timeout triggers retry with extended timeout

- **WHEN** page extraction times out after 60 seconds
- **THEN** system retries same page with 90-second timeout (base + 30s)

#### Scenario: Second timeout triggers final retry

- **WHEN** page extraction times out after 90 seconds on retry
- **THEN** system retries same page with 120-second timeout (base + 60s)

#### Scenario: Third timeout skips page

- **WHEN** page extraction times out after 120 seconds on second retry
- **THEN** system skips page and continues to next page

#### Scenario: Successful extraction on retry

- **WHEN** page extraction succeeds on second attempt (90s timeout)
- **THEN** system processes extracted tables normally without further retries

### Requirement: Retry Attempt Logging

The system SHALL log each retry attempt with timeout value and attempt number.

#### Scenario: Log first retry

- **WHEN** retrying page after first timeout
- **THEN** log message shows "Retry attempt 1/2 with timeout 90000ms"

#### Scenario: Log second retry

- **WHEN** retrying page after second timeout
- **THEN** log message shows "Retry attempt 2/2 with timeout 120000ms"

#### Scenario: Log final skip

- **WHEN** skipping page after all retries exhausted
- **THEN** log message shows "All retry attempts failed, skipping page"

### Requirement: Timeout Detection

The system SHALL detect timeout errors specifically to trigger progressive retry.

#### Scenario: Timeout error triggers retry

- **WHEN** API exception contains "timeout" or "timed out" in error message
- **THEN** system initiates progressive retry sequence

#### Scenario: Non-timeout error skips retry

- **WHEN** API exception is not timeout-related (e.g., authentication error)
- **THEN** system skips page immediately without retry