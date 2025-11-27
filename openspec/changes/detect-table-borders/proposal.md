# Proposal: Automatic Table Border Detection for Camelot

**Change ID**: `detect-table-borders`
**Status**: Draft
**Created**: 2025-11-27

## Why

Users must manually choose between Camelot's `lattice` (bordered) and `stream` (borderless) flavors, requiring prior knowledge of PDF structure. Wrong choice leads to poor extraction. Auto-detection eliminates guesswork and improves success rate.

## Problem Statement

Currently, users must manually specify `--camelot-flavor lattice` or `--camelot-flavor stream` when using the Camelot engine. This requires prior knowledge of whether the PDF contains bordered or borderless tables.

**Pain points**:
- Users may not know which flavor to use
- Wrong flavor choice leads to poor extraction results
- Trial and error is required for unfamiliar PDFs
- No guidance provided when extraction fails

## Proposed Solution

Implement automatic border detection that analyzes PDF pages to determine if tables have visible borders (grid lines) and automatically selects the appropriate Camelot flavor:

- **Bordered tables** → `lattice` mode (default)
- **Borderless tables** → `stream` mode

Detection happens before extraction, per-page or per-PDF, with results logged for transparency.

## Goals

1. **Auto-select Camelot flavor** based on border presence
2. **Maintain backward compatibility** - `--camelot-flavor` flag overrides auto-detection
3. **Log detection results** - inform user of decision
4. **Fast detection** - add <100ms overhead per page
5. **Accurate detection** - ≥90% correct flavor selection

## Non-Goals

- Detect other table features (multi-line headers, merged cells, etc.)
- Support mixed bordered/borderless tables on same page (use first detected)
- Implement ML-based detection (use heuristics)

## Success Criteria

- [ ] Auto-detection works for 90%+ of test PDFs
- [ ] User can still override with `--camelot-flavor`
- [ ] Detection time <100ms per page
- [ ] Detection results logged (INFO level)
- [ ] Tests cover bordered, borderless, and ambiguous cases

## Implementation Scope

**New capabilities**:
1. `border-detection`: Core logic to detect borders in PDF pages
2. `auto-flavor-selection`: Integration with Camelot extractor

**Modified capabilities**:
- `cli-interface`: Add `--auto-detect-borders` flag (default: true)
- `extraction-workflow`: Use auto-detection when flavor not specified

## Impact Analysis

**Benefits**:
- Better user experience (no flavor guessing)
- Higher extraction success rate
- Fewer support questions

**Risks**:
- Detection may be incorrect for ambiguous cases
- Slight performance overhead (~50-100ms/page)

**Mitigation**:
- Log detection decision for transparency
- Allow manual override via `--camelot-flavor`
- Fall back to `lattice` (current default) on detection failure

## Open Questions

1. Should detection be per-page or per-PDF?
   - **Decision**: Per-PDF (analyze first selected page, use result for all)
   - **Rationale**: Faster, tables usually consistent within document

2. What threshold determines "bordered"?
   - **Decision**: If ≥30% of detected lines form grid pattern → bordered
   - **Rationale**: Based on empirical testing (see design.md)

3. Should auto-detection be opt-in or opt-out?
   - **Decision**: Opt-out (enabled by default, disable with `--no-auto-detect-borders`)
   - **Rationale**: Maximizes user benefit, power users can override

## Alternatives Considered

**1. Prompt user for flavor**
- Rejected: Not suitable for batch processing, breaks automation

**2. Try both flavors and pick best result**
- Rejected: Doubles processing time, wasted computation

**3. Use Camelot's built-in detection**
- Rejected: Camelot doesn't expose border detection API

## Dependencies

- None (uses existing PyMuPDF functionality)

## Timeline

**Phase 1: Core Detection** (2-3 days)
- Implement border detection algorithm
- Unit tests with sample PDFs

**Phase 2: Integration** (1-2 days)
- Integrate with Camelot extractor
- CLI flag support
- Logging

**Phase 3: Testing & Docs** (1 day)
- Comprehensive testing
- Update documentation
- Update best-practices.md

**Total**: 4-6 days
