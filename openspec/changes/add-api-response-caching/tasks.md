# Implementation Tasks

## 1. Cache Infrastructure

- [ ] 1.1 Add `responses/` subdirectory in output_dir
- [ ] 1.2 Implement cache save: `{pdf_stem}_page{N}_response.json`
- [ ] 1.3 Implement cache load with existence check
- [ ] 1.4 Add `--no-cache` flag to CLI arguments

## 2. Mistral Engine Integration

- [ ] 2.1 Save raw Mistral API response before CSV conversion
- [ ] 2.2 Check cache before API call in `extract_tables()`
- [ ] 2.3 Log cache hit/miss for transparency
- [ ] 2.4 Handle cache format validation

## 3. Textract Engine Integration

- [ ] 3.1 Save raw Textract API response before CSV conversion
- [ ] 3.2 Check cache before API call
- [ ] 3.3 Log cache hit/miss

## 4. Testing

- [ ] 4.1 Test cache creation on first run
- [ ] 4.2 Test cache resume on second run
- [ ] 4.3 Test `--no-cache` forces fresh API calls
- [ ] 4.4 Test cache with `--merge` output
- [ ] 4.5 Verify cache works across page ranges
