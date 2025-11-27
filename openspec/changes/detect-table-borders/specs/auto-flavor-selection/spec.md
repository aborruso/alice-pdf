# Spec Delta: Auto Flavor Selection

**Capability**: `auto-flavor-selection` (NEW)
**Type**: Feature enhancement

## Overview

Automatically selects Camelot extraction flavor (lattice or stream) based on PDF border detection, with user override support.

---

## ADDED Requirements

### Requirement: AFS-1 - Enable auto flavor selection by default

When using Camelot engine, the system SHALL automatically detect table borders and select appropriate flavor unless user specifies `--camelot-flavor`.

**Rationale**: Improve user experience by eliminating flavor guessing; users shouldn't need PDF structure knowledge.

**Acceptance Criteria**:
- Auto-detection enabled by default for Camelot engine
- User-specified `--camelot-flavor` takes precedence (no detection)
- Detection logged at INFO level
- Backward compatible with existing scripts

#### Scenario: Auto-select flavor for Camelot extraction

**Given** user runs `alice-pdf document.pdf output/ --engine camelot`
**And** user does NOT specify `--camelot-flavor`
**When** extraction starts
**Then** border detection is performed on first page
**And** appropriate flavor (lattice or stream) is automatically selected
**And** detection decision is logged
**And** extraction proceeds with selected flavor

**Example**:
```bash
$ alice-pdf invoice.pdf output/ --engine camelot
INFO - Border detection: has_borders=True, score=0.45, using flavor=lattice
INFO - Processing PDF: invoice.pdf
INFO - Flavor: lattice, Pages: all
...
```

#### Scenario: User overrides auto-detection

**Given** user runs `alice-pdf document.pdf output/ --camelot-flavor stream`
**When** extraction starts
**Then** border detection is SKIPPED
**And** user-specified flavor `stream` is used
**And** no detection log message appears

**Example**:
```bash
$ alice-pdf invoice.pdf output/ --camelot-flavor stream
INFO - Processing PDF: invoice.pdf
INFO - Flavor: stream, Pages: all
# No border detection log
```

---

### Requirement: AFS-2 - Provide opt-out flag

Users SHALL be able to disable auto-detection and use explicit default flavor.

**Rationale**: Power users may want deterministic behavior or faster processing.

**Acceptance Criteria**:
- CLI flag `--no-auto-detect-borders` disables detection
- Falls back to `lattice` flavor (current default)
- Flag documented in help text

#### Scenario: Disable auto-detection

**Given** user runs `alice-pdf document.pdf output/ --no-auto-detect-borders`
**When** extraction starts
**Then** border detection is SKIPPED
**And** default `lattice` flavor is used
**And** extraction proceeds normally

---

### Requirement: AFS-3 - Integrate detection with Camelot extractor

The `extract_tables_with_camelot()` function SHALL call border detection when appropriate.

**Rationale**: Centralize flavor selection logic in extractor module.

**Acceptance Criteria**:
- Function accepts `auto_detect` boolean parameter
- When `auto_detect=True` and `flavor` not explicitly set, call `select_flavor_auto()`
- Pass detected flavor to Camelot
- Log selected flavor

#### Scenario: Extractor uses auto-detected flavor

**Given** `extract_tables_with_camelot()` is called with `auto_detect=True`
**And** `flavor` parameter is default `"lattice"`
**When** function executes
**Then** it calls `select_flavor_auto(pdf_path, pages)`
**And** uses returned flavor for extraction
**And** logs: `"Auto-detected flavor: {flavor}"`

---

### Requirement: AFS-4 - Analyze first requested page only

Auto-detection SHALL analyze only the first page in the user-specified range.

**Rationale**: Faster than per-page detection; tables usually consistent within document.

**Acceptance Criteria**:
- Parse `pages` parameter to get first page number
- Detect borders on that page only
- Use same flavor for all pages in extraction

#### Scenario: Detect on first page of range

**Given** user specifies `--pages 5-10`
**When** auto-detection runs
**Then** it analyzes page 5 only
**And** applies detected flavor to pages 5-10

#### Scenario: Handle "all" pages

**Given** user specifies `--pages all` or no pages argument
**When** auto-detection runs
**Then** it analyzes page 1 (first page of PDF)
**And** applies detected flavor to all pages

---

## MODIFIED Requirements

### Modified: CLI Interface - Add auto-detection flags

**Spec**: `cli-interface`
**Requirement**: CLI-3 (Engine-specific options)

**Change**: ADD Camelot auto-detection flags

**New flags**:
```python
--auto-detect-borders
    Enable automatic border detection for Camelot flavor selection (default)

--no-auto-detect-borders
    Disable auto-detection, use --camelot-flavor or default to lattice
```

**Updated help text**:
```
Camelot-specific:
  --camelot-flavor {lattice,stream}
                        Camelot extraction mode: lattice (bordered tables) or
                        stream (whitespace-based) (default: auto-detect)
  --auto-detect-borders
                        Auto-detect table borders (default: enabled)
  --no-auto-detect-borders
                        Disable auto-detection, use explicit flavor
```

#### Scenario: Help text shows auto-detection flags

**Given** user runs `alice-pdf --help`
**When** help text is displayed
**Then** it includes `--auto-detect-borders` flag
**And** it includes `--no-auto-detect-borders` flag
**And** default behavior is documented as "auto-detect"

---

### Modified: Extraction Workflow - Use auto-detection

**Spec**: `extraction-workflow`
**Requirement**: EW-2 (Engine routing)

**Change**: ADD auto-detection step before Camelot extraction

**Updated workflow**:
```
User Input → Validation → Engine Selection
                                ↓
                           [Camelot]
                                ↓
                    Auto-detect borders? (if enabled)
                                ↓
                          Select flavor
                                ↓
                         Call Camelot API
                                ↓
                          Process tables
                                ↓
                          Save CSVs
```

#### Scenario: Extraction workflow with auto-detection

**Given** user selects Camelot engine
**And** auto-detection is enabled (default)
**When** extraction workflow executes
**Then** border detection runs BEFORE calling Camelot
**And** detected flavor is used in Camelot call
**And** extraction completes successfully

---

## Implementation Notes

**Modified Files**:
- `alice_pdf/camelot_extractor.py`:
  - Add `auto_detect` parameter
  - Import `select_flavor_auto` from `border_detector`
  - Call flavor selection conditionally

- `alice_pdf/cli.py`:
  - Add `--auto-detect-borders` / `--no-auto-detect-borders` flags
  - Pass `auto_detect` to `extract_tables_with_camelot()`
  - Update help text

**Example Integration**:
```python
# In camelot_extractor.py
def extract_tables_with_camelot(
    pdf_path,
    output_dir,
    pages="all",
    flavor="lattice",
    auto_detect=False,  # NEW parameter
    merge_output=False,
    resume=True,
):
    # NEW: Auto-detect flavor if enabled
    if auto_detect and flavor == "lattice":  # lattice is default
        from .border_detector import select_flavor_auto
        flavor = select_flavor_auto(pdf_path, pages)
        logger.info(f"Auto-detected flavor: {flavor}")

    # Rest unchanged
    logger.info(f"Flavor: {flavor}, Pages: {pages}")
    tables = camelot.read_pdf(str(pdf_path), pages=pages, flavor=flavor)
    ...
```

**Backward Compatibility**:
- Existing scripts without flags: Auto-detection enabled (may select different flavor)
- Scripts with `--camelot-flavor`: Explicit flavor used (no change)
- Migration: Users can add `--no-auto-detect-borders` to preserve old behavior
