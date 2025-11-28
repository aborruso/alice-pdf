# Implementation Tasks

## 1. Directory Structure Design

- [ ] 1.1 Define hierarchical layout: `{pdf_stem}/responses/`, `{pdf_stem}/tables/`, `{pdf_stem}/images/`
- [ ] 1.2 Add `--flat-output` flag for backward compatibility
- [ ] 1.3 Implement directory creation helper function
- [ ] 1.4 Update path resolution in all extractors

## 2. Mistral Engine Integration

- [ ] 2.1 Update cache paths to use `responses/` subdirectory
- [ ] 2.2 Update CSV paths to use `tables/` subdirectory
- [ ] 2.3 Update merged file path
- [ ] 2.4 Preserve flat mode when `--flat-output` used

## 3. Textract Engine Integration

- [ ] 3.1 Update cache paths to use `responses/` subdirectory
- [ ] 3.2 Update CSV paths to use `tables/` subdirectory
- [ ] 3.3 Update merged file path

## 4. Camelot Engine Integration

- [ ] 4.1 Update CSV paths to use `tables/` subdirectory
- [ ] 4.2 Update merged file path

## 5. Documentation

- [ ] 5.1 Update README with new directory structure
- [ ] 5.2 Update CLAUDE.md with output organization
- [ ] 5.3 Add examples showing hierarchical vs flat output

## 6. Testing

- [ ] 6.1 Test hierarchical output creation
- [ ] 6.2 Test `--flat-output` backward compatibility
- [ ] 6.3 Test with all three engines
- [ ] 6.4 Test with `--merge` flag
- [ ] 6.5 Verify paths in all log messages
