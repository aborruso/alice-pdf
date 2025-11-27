# Spec Delta: Border Detection

**Capability**: `border-detection` (NEW)
**Type**: Core functionality

## Overview

Analyzes PDF pages to detect presence of table borders (grid lines) using PyMuPDF drawing instruction analysis.

---

## ADDED Requirements

### Requirement: BD-1 - Detect table borders in PDF pages

The system SHALL provide a function to detect whether a PDF page contains bordered tables.

**Rationale**: Enable automatic Camelot flavor selection without user intervention.

**Acceptance Criteria**:
- Function accepts PDF path and page number
- Returns boolean indicating border presence
- Returns confidence score (0.0-1.0)
- Processes typical page in <100ms

#### Scenario: Bordered table detected

**Given** a PDF page with visible grid lines forming table borders
**When** border detection is performed
**Then** the function returns `has_borders=True`
**And** confidence score is ≥0.7

**Example**:
```python
has_borders, confidence = detect_borders("invoice.pdf", page_num=1)
assert has_borders == True
assert confidence >= 0.7
```

#### Scenario: Borderless table detected

**Given** a PDF page with whitespace-separated table data (no grid lines)
**When** border detection is performed
**Then** the function returns `has_borders=False`
**And** confidence score is ≥0.7

**Example**:
```python
has_borders, confidence = detect_borders("report.pdf", page_num=1)
assert has_borders == False
assert confidence >= 0.7
```

#### Scenario: Text-only page (no tables)

**Given** a PDF page containing only text paragraphs
**When** border detection is performed
**Then** the function returns `has_borders=False`
**And** confidence score indicates low certainty

**Example**:
```python
has_borders, confidence = detect_borders("document.pdf", page_num=1)
assert has_borders == False
# Low confidence OK since no table present
```

---

### Requirement: BD-2 - Use heuristic-based line detection

Border detection SHALL analyze drawing instructions to identify horizontal and vertical lines forming grid patterns.

**Rationale**: PyMuPDF provides access to PDF drawing commands; heuristic approach is fast and dependency-free.

**Acceptance Criteria**:
- Extract drawing instructions using `page.get_drawings()`
- Filter for line types (ignore curves, filled shapes)
- Classify lines as horizontal or vertical
- Calculate border score based on line density
- Threshold-based decision (score ≥ 0.3 → bordered)

#### Scenario: Grid pattern with many lines

**Given** a PDF page with 10+ horizontal and 6+ vertical lines
**And** lines form regular grid pattern (table-like)
**When** border detection is performed
**Then** border score is calculated as `(h_lines + v_lines) / (page_width + page_height)`
**And** score exceeds 0.3 threshold
**And** function returns `has_borders=True`

#### Scenario: Few or no lines detected

**Given** a PDF page with 0-2 lines total
**When** border detection is performed
**Then** border score is very low (<0.1)
**And** function returns `has_borders=False`

---

### Requirement: BD-3 - Handle detection failures gracefully

Border detection SHALL handle errors (corrupt PDF, missing page, etc.) without crashing.

**Rationale**: Detection is a convenience feature; failure should not block extraction.

**Acceptance Criteria**:
- Catch exceptions from PyMuPDF operations
- Log warning with error details
- Return safe default (`has_borders=True` to use lattice)
- Allow extraction to proceed

#### Scenario: Corrupt PDF page

**Given** a PDF with corrupted page data
**When** border detection attempts to read drawing instructions
**And** PyMuPDF raises an exception
**Then** the function catches the exception
**And** logs a warning message
**And** returns `has_borders=True, confidence=0.0` (safe default)
**And** extraction can continue with lattice flavor

**Example**:
```python
try:
    has_borders, confidence = detect_borders("corrupt.pdf", page_num=1)
    # Should return True (safe default) instead of crashing
    assert has_borders == True
    assert confidence == 0.0  # No confidence in detection
except Exception:
    pytest.fail("Detection should not raise exceptions")
```

---

### Requirement: BD-4 - Log detection decisions

Detection results SHALL be logged at INFO level for transparency.

**Rationale**: Users should understand why a particular flavor was selected.

**Acceptance Criteria**:
- Log message includes: has_borders, score, selected flavor
- Format: `"Border detection: has_borders={bool}, score={float:.2f}, using flavor={str}"`
- Logged before extraction starts

#### Scenario: Detection logged for bordered PDF

**Given** border detection determines page has borders
**When** detection completes
**Then** an INFO log message is emitted
**And** log contains: `"Border detection: has_borders=True, score=0.42, using flavor=lattice"`

---

### Requirement: BD-5 - Provide flavor selection helper

A convenience function SHALL map detection result to Camelot flavor string.

**Rationale**: Simplify integration with Camelot extractor.

**Acceptance Criteria**:
- Function `select_flavor_auto(pdf_path, pages)` implemented
- Analyzes first page in range
- Returns `"lattice"` or `"stream"` string
- Handles `pages="all"` case (default to page 1)

#### Scenario: Auto-select lattice for bordered PDF

**Given** a PDF where first page has borders
**When** `select_flavor_auto(pdf_path, pages="1-5")` is called
**Then** the function detects borders on page 1
**And** returns `"lattice"`

#### Scenario: Auto-select stream for borderless PDF

**Given** a PDF where first page has no borders
**When** `select_flavor_auto(pdf_path, pages="all")` is called
**Then** the function detects no borders on page 1
**And** returns `"stream"`

---

## Implementation Notes

**File**: `alice_pdf/border_detector.py` (new module)

**Key Functions**:
```python
def detect_borders(pdf_path: str, page_num: int) -> tuple[bool, float]:
    """
    Detect if PDF page contains bordered tables.

    Returns:
        (has_borders, confidence_score)
    """
    pass

def select_flavor_auto(pdf_path: str, pages: str = "all") -> str:
    """
    Auto-select Camelot flavor based on border detection.

    Returns:
        "lattice" or "stream"
    """
    pass
```

**Dependencies**:
- PyMuPDF (fitz) - already in project
- No new dependencies required

**Performance Target**: <100ms per page detection
