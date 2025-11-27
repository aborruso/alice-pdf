# Tasks: Automatic Table Border Detection

**Change ID**: `detect-table-borders`

Implementation tasks in priority order. Mark completed with `[x]`.

## Phase 1: Core Detection (Days 1-3)

### Task 1: Implement Border Detection Module
- [ ] Create `alice_pdf/border_detector.py`
- [ ] Implement `detect_borders(pdf_path, page_num)` function
  - [ ] Extract drawing instructions with PyMuPDF
  - [ ] Filter for line types
  - [ ] Classify horizontal vs vertical lines
  - [ ] Calculate border score
  - [ ] Return boolean + confidence score
- [ ] Add docstrings with examples
- [ ] Handle edge cases (no drawings, corrupt PDF)

**Validation**: Unit test with 2-3 sample PDFs (bordered, borderless, text-only)

### Task 2: Implement Flavor Selection Logic
- [ ] Add `select_flavor_auto(pdf_path, pages)` to `border_detector.py`
  - [ ] Parse first page from pages string
  - [ ] Call `detect_borders()` for that page
  - [ ] Map boolean to flavor string ("lattice" or "stream")
  - [ ] Log detection decision (INFO level)
- [ ] Handle "all" pages case (default to page 1)

**Validation**: Function returns correct flavor for test cases

### Task 3: Unit Tests for Border Detection
- [ ] Create `tests/test_border_detector.py`
- [ ] Test: Bordered PDF → `has_borders=True`
- [ ] Test: Borderless PDF → `has_borders=False`
- [ ] Test: Text-only PDF → `has_borders=False`
- [ ] Test: Error handling (corrupt PDF)
- [ ] Test: Edge case - ambiguous score near threshold

**Validation**: All tests pass, coverage ≥ 80% for border_detector.py

## Phase 2: Integration (Days 4-5)

### Task 4: Integrate with Camelot Extractor
- [ ] Modify `camelot_extractor.py`:
  - [ ] Add `auto_detect` parameter to `extract_tables_with_camelot()`
  - [ ] Import `select_flavor_auto` from `border_detector`
  - [ ] Call flavor selection when `auto_detect=True` and flavor not specified
  - [ ] Log auto-selected flavor
  - [ ] Preserve backward compatibility (default to lattice if detection disabled)

**Validation**: Extraction works with auto-detection enabled/disabled

### Task 5: CLI Integration
- [ ] Modify `cli.py`:
  - [ ] Add `--auto-detect-borders` flag (default: True)
  - [ ] Add `--no-auto-detect-borders` flag (sets auto_detect=False)
  - [ ] Pass `auto_detect` flag to `extract_tables_with_camelot()`
  - [ ] Update help text with new flags
  - [ ] Ensure `--camelot-flavor` overrides auto-detection
- [ ] Update CLI examples in docstring

**Validation**: `alice-pdf --help` shows new flags, manual override works

### Task 6: Integration Tests
- [ ] Create `tests/test_auto_detection.py`
- [ ] Test: Auto-detection with bordered PDF
  - [ ] Run `alice-pdf bordered.pdf output/`
  - [ ] Verify lattice mode was used (check logs)
  - [ ] Verify successful extraction
- [ ] Test: Auto-detection with borderless PDF
  - [ ] Run `alice-pdf borderless.pdf output/`
  - [ ] Verify stream mode was used
  - [ ] Verify successful extraction
- [ ] Test: User override
  - [ ] Run `alice-pdf bordered.pdf output/ --camelot-flavor stream`
  - [ ] Verify stream mode was used (user choice wins)
- [ ] Test: Disable auto-detection
  - [ ] Run `alice-pdf pdf.pdf output/ --no-auto-detect-borders`
  - [ ] Verify default lattice mode used

**Validation**: All integration tests pass

## Phase 3: Documentation & Polish (Day 6)

### Task 7: Update Documentation
- [ ] Update `README.md`:
  - [ ] Add auto-detection feature description
  - [ ] Add usage examples with/without override
  - [ ] Update "Choosing an engine" section
- [ ] Update `CLAUDE.md`:
  - [ ] Document new `border_detector.py` module
  - [ ] Update Camelot section with auto-detection
- [ ] Update `docs/best-practices.md`:
  - [ ] Add section on auto-detection
  - [ ] Explain when to override (edge cases)
  - [ ] Add troubleshooting tips

**Validation**: Documentation review

### Task 8: Performance Testing
- [ ] Measure detection time on sample PDFs:
  - [ ] Simple PDF (10-20 pages)
  - [ ] Complex PDF (50+ pages)
  - [ ] Large file (100+ MB)
- [ ] Verify overhead <100ms per page
- [ ] Profile if needed, optimize hot paths

**Validation**: Performance meets target (<100ms)

### Task 9: Update LOG.md
- [ ] Add entry for 2025-11-27:
  - [ ] "Add automatic table border detection for Camelot"
  - [ ] "Auto-selects lattice/stream flavor based on PDF analysis"
  - [ ] "New flags: --auto-detect-borders / --no-auto-detect-borders"

**Validation**: Changelog updated

### Task 10: Final Validation
- [ ] Run `pytest` - all tests pass
- [ ] Run `openspec validate detect-table-borders --strict` - no errors
- [ ] Test on real PDFs (bordered, borderless, mixed)
- [ ] Verify logging output is clear and helpful
- [ ] Check backward compatibility (existing scripts still work)

**Validation**: All checks pass, ready for deployment

## Deployment Checklist

- [ ] All tasks completed and marked `[x]`
- [ ] Tests pass (unit + integration)
- [ ] Documentation updated
- [ ] Performance validated
- [ ] Backward compatibility confirmed
- [ ] LOG.md updated
- [ ] OpenSpec validation passes
- [ ] Code reviewed (if applicable)

## Post-Deployment

- [ ] Monitor user feedback on auto-detection accuracy
- [ ] Collect metrics on flavor selection (lattice vs stream usage)
- [ ] Identify edge cases for future improvement
- [ ] Consider Phase 2 enhancements (per-page detection, ML, etc.)
