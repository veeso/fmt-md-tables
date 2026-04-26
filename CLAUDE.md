# CLAUDE.md

Project guide for Claude Code sessions.

## What this is

`fmt-md-tables` — small Python CLI that pretty-prints markdown tables (pads
cells so column pipes align). Single-module package, zero runtime
dependencies. Distributed on PyPI, installable via `uv tool install`.

## Layout

```
.
├── fmt_md_tables.py        # The whole tool: parsing + formatting + CLI
├── tests/
│   └── test_format.py      # pytest suite: unit + CLI tests
├── pyproject.toml          # Hatchling build, project metadata, console script
├── LICENSE                 # MIT
├── README.md               # User-facing docs + badges
├── CLAUDE.md               # This file
├── .gitignore
└── .github/workflows/
    ├── ci.yml              # Matrix test (OS × Py 3.8–3.13), build artifact
    └── release.yml         # Tag v* → PyPI (OIDC) + GitHub release
```

Single-module on purpose. Do not split into a package directory unless the
tool grows substantially. If splitting becomes needed, also update
`[tool.hatch.build.targets.*]` in `pyproject.toml`.

## Build system

- Backend: **hatchling** (declared in `pyproject.toml`).
- Package manager / runner: **uv**. Use uv, not pip/poetry/pipx.
- Console script entry point: `fmt-md-tables = "fmt_md_tables:main"`.

## Common commands

```sh
uv build                          # produce sdist + wheel in dist/
uv pip install -e .               # editable install (needs active venv)
uv tool install .                 # install CLI globally
uvx --from . fmt-md-tables FILE   # one-shot run without installing
python3 fmt_md_tables.py FILE     # run directly without install
```

Tests:

```sh
uv run --group dev pytest -q     # full pytest suite
```

Smoke test:

```sh
printf '| a | b |\n|---|---|\n| 1 | 2 |\n' | python3 fmt_md_tables.py -
```

## Code conventions

- Python 3.8+ (matrix in CI). Use `from __future__ import annotations`
  so `list[str]` / `int | None` work on 3.8/3.9.
- Standard library only. No runtime deps. Resist adding any.
- Functions have docstrings; keep them tight and behavioral, not narrative.
- Avoid inline comments restating what code already says — docstrings cover
  intent.
- Type hints on every public function signature.

## Behavioral rules of the formatter

These are *invariants*; tests/changes must not break them:

1. Fenced code blocks (` ``` ` and `~~~`) are left untouched. State toggles
   on each fence line.
2. A "table" requires a separator row (cells matching `:?-+:?`). Without
   one, the line group is emitted verbatim.
3. Column widths come from data rows only. Separator min width is 3
   (GFM spec).
4. Alignment markers (`:---`, `---:`, `:---:`) are preserved and applied
   to cell padding.
5. Escaped pipes (`\|`) are not column delimiters.
6. Short rows are padded with empty cells to the widest row.
7. Trailing newline of input is preserved.

When changing formatter logic, re-check all seven.

## Releasing

1. Bump `version` in `pyproject.toml`.
2. Commit with a Conventional Commits message.
3. Tag: `git tag vX.Y.Z && git push origin vX.Y.Z`.
4. `release.yml` builds, publishes to PyPI via OIDC trusted publishing,
   creates a GitHub release with autogen notes.

PyPI trusted publisher must be configured at pypi.org (project
`fmt-md-tables`, workflow `release.yml`, environment `pypi`). The `pypi`
environment must exist in repo Settings → Environments. No secrets.

Tag version must match `pyproject.toml` version (minus the `v`).

## CI

`ci.yml` runs on push to `main` and PRs. Matrix: ubuntu/macos/windows ×
Python 3.8–3.13. Steps: install uv, install package + pytest, run pytest
suite, then run `--help` and format a sample stdin table as a smoke test.
Test deps live in the `dev` `[dependency-groups]` group.

## Things to avoid

- Adding runtime dependencies.
- Splitting the module before it warrants it.
- `Co-Authored-By` lines in commits (per global user instructions).
- Changing the build backend without reason. Hatchling is intentional.
- Skipping CI hooks (`--no-verify`) on commits.
