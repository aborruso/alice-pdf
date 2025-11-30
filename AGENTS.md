<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# Repository Guidelines

## Project Structure & Module Organization
- Core package lives in `alice_pdf/`: `cli.py` (entrypoint), `extractor.py` (PDF → images → Mistral tables → CSV), and `prompt_generator.py` (builds prompts from YAML/JSON schemas).  
- Tests sit in `tests/` with mirrors for each module plus fixtures under `tests/fixtures/`.  
- Sample assets for quick runs are in `sample/` (`edilizia-residenziale_comune_2024.pdf` + matching schema).  
- CLI installs as `alice-pdf` via the `project.scripts` entry in `pyproject.toml`.

## Build, Test, and Development Commands
- Install deps (isolated): `uv sync` or `uv tool install .` for a global CLI.  
- Run the tool locally: `uv run alice-pdf sample/edilizia-residenziale_comune_2024.pdf output/ --merge`.  
- Execute tests: `uv run pytest -v` (respects markers in `pytest.ini`).  
- Coverage check (optional): `uv run pytest --cov=alice_pdf --cov-report=term-missing`.  
- Lint/format: follow PEP8; if you use `ruff` or `black`, run them before committing (not enforced yet).

## Coding Style & Naming Conventions
- Python ≥3.8, 4-space indentation, PEP8 naming (`snake_case` for functions/vars, `CapWords` for classes).  
- Keep CLI argument parsing consistent with `argparse` patterns already in `cli.py`.  
- Prefer small, pure functions; add docstrings describing side effects and inputs.  
- Logging: use the module-level `logger`; INFO for progress, DEBUG for payloads; no `print`.  
- File outputs should be UTF-8 with BOM for CSVs (matches existing behavior).

## Testing Guidelines
- Write tests with `pytest`; name files `test_*.py` and functions `test_*`.  
- Use markers from `pytest.ini`: tag longer tests with `@pytest.mark.slow` or `integration`.  
- Mock external APIs (Mistral) to keep tests offline; see `tests/test_extractor.py` for patterns.  
- Prefer fixture reuse under `tests/fixtures/`; include representative PDFs/schemas when adding new features.

## Commit & Pull Request Guidelines
- Commit messages: short imperative lines (e.g., `Add schema prompt examples`); include scope like `feat:`, `fix:`, or `chore:` when helpful.  
- Keep commits focused; separate refactors from functional changes.  
- PRs should describe motivation, key changes, and testing performed; link issues when available.  
- For UI/CLI changes, paste example commands and resulting output snippet; for behavior changes, note compatibility (e.g., default DPI/model).

## Release Checklist (PyPI + GitHub tag/release)
- Bump version in `pyproject.toml` **and** `alice_pdf/__init__.py` (keep them in sync).
- Clean build artifacts: `rm -rf dist build *.egg-info`.
- Build sdist+wheel: `python3 -m build` (or `uv build`).
- Sanity check: `python3 -m twine check dist/*`.
- Publish to PyPI: `python3 -m twine upload dist/*` (or `--repository testpypi` first).
- Update docs/examples for install/flags if changed (README, docs/cli-tests/*).
- Commit release changes (version, docs, CLI flags) with a message like `release: X.Y.Z`.
- Tag annotated: `git tag -a vX.Y.Z -m "Release X.Y.Z"` and push main + tags.
- Create GitHub Release from the tag (e.g., `gh release create vX.Y.Z --title "vX.Y.Z" --notes "…"`).

## Security & Configuration Tips
- Never commit secrets; load Mistral API keys via `MISTRAL_API_KEY` env var or `--api-key`.  
- `.env` is optional for local dev; keep it gitignored.  
- Respect API rate limiting already implemented in `extractor.py` (`time.sleep(1.2)`); avoid removing without adding backoff logic.  
- Before publishing, clear generated CSVs under `output/` to keep the repo clean.
