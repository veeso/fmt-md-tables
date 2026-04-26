# fmt-md-tables

[![license-mit](https://img.shields.io/pypi/l/fmt-md-tables.svg?logo=python)](https://opensource.org/licenses/MIT)
[![repo-stars](https://img.shields.io/github/stars/veeso/fmt-md-tables?style=flat)](https://github.com/veeso/fmt-md-tables/stargazers)
[![downloads](https://img.shields.io/pypi/dm/fmt-md-tables.svg?logo=python)](https://pypi.org/project/fmt-md-tables/)
[![latest-version](https://img.shields.io/pypi/v/fmt-md-tables.svg?logo=python)](https://pypi.org/project/fmt-md-tables/)
[![python-versions](https://img.shields.io/pypi/pyversions/fmt-md-tables.svg?logo=python)](https://pypi.org/project/fmt-md-tables/)
[![conventional-commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://conventionalcommits.org)

[![ci](https://github.com/veeso/fmt-md-tables/actions/workflows/ci.yml/badge.svg)](https://github.com/veeso/fmt-md-tables/actions)

Format markdown tables in a file so columns align.

## Install

With [uv](https://docs.astral.sh/uv/) — install as a global CLI tool:

```sh
uv tool install .
```

Editable / dev:

```sh
uv pip install -e .
```

Run without installing:

```sh
uvx --from . fmt-md-tables FILE
```

From PyPI (once published):

```sh
uv tool install fmt-md-tables
```

## Usage

```sh
fmt-md-tables FILE          # print formatted output to stdout
fmt-md-tables -i FILE       # rewrite file in place
fmt-md-tables -             # read from stdin
```

## Features

- Pads cells to max column width per table.
- Preserves alignment markers (`:---`, `:---:`, `---:`).
- Skips fenced code blocks (``` and `~~~`).
- Handles escaped pipes (`\|`).
- Pads short rows with empty cells.

## Example

Input:

```md
| Filter | Index plan | Notes |
|--------|-----------|-------|
| `Filter::eq("col", val)` | Exact match | Best case |
| `Filter::ge("col", val)` | Range scan (start bound) | Uses linked-leaf traversal |
```

Output:

```md
| Filter                   | Index plan               | Notes                      |
| ------------------------ | ------------------------ | -------------------------- |
| `Filter::eq("col", val)` | Exact match              | Best case                  |
| `Filter::ge("col", val)` | Range scan (start bound) | Uses linked-leaf traversal |
```

## License

MIT
