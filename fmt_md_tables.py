#!/usr/bin/env python3
"""Format markdown tables in a file so columns align."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SEP_CELL = re.compile(r"^\s*:?-+:?\s*$")


def split_row(line: str) -> list[str]:
    """Split a markdown table row into stripped cell strings.

    Strips outer pipes if present and splits on unescaped ``|``. A backslash
    escapes the following character, so ``\\|`` is treated as literal pipe
    content rather than a column delimiter.

    Args:
        line: Raw table row line, with or without leading/trailing pipes.

    Returns:
        List of cell contents, each trimmed of surrounding whitespace.
    """
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    # split on unescaped pipes
    out, buf, i = [], [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            buf.append(s[i:i + 2])
            i += 2
            continue
        if c == "|":
            out.append("".join(buf).strip())
            buf = []
        else:
            buf.append(c)
        i += 1
    out.append("".join(buf).strip())
    return out


def is_table_line(line: str) -> bool:
    """Return True if the line could belong to a markdown table.

    A table line must contain at least one pipe beyond any leading pipes,
    so plain text and code lines containing a single leading ``|`` are
    rejected.
    """
    return "|" in line.strip().lstrip("|")


def is_separator(cells: list[str]) -> bool:
    """Return True if every cell matches the GFM separator pattern.

    Separator cells consist of dashes with optional surrounding colons for
    alignment (e.g. ``---``, ``:---``, ``:---:``, ``---:``). An empty cell
    list is not a separator.
    """
    return bool(cells) and all(SEP_CELL.match(c) for c in cells)


def cell_width(s: str) -> int:
    """Return display width of a cell. Currently character count.

    Kept as a function so wide-character / ANSI-aware width logic can be
    added later without touching call sites.
    """
    return len(s)


def align_of(sep_cell: str) -> str:
    """Decode column alignment from a separator cell.

    Returns one of ``"left"``, ``"right"``, ``"center"``, or ``"default"``
    based on the placement of colons in the separator.
    """
    s = sep_cell.strip()
    left = s.startswith(":")
    right = s.endswith(":")
    if left and right:
        return "center"
    if right:
        return "right"
    if left:
        return "left"
    return "default"


def pad(text: str, width: int, align: str) -> str:
    """Pad ``text`` to ``width`` characters according to ``align``.

    ``"left"`` and ``"default"`` left-justify; ``"right"`` right-justifies;
    ``"center"`` distributes padding evenly with any extra space on the
    right.
    """
    if align == "right":
        return text.rjust(width)
    if align == "center":
        n = width - len(text)
        l = n // 2
        r = n - l
        return " " * l + text + " " * r
    return text.ljust(width)


def make_sep(width: int, align: str) -> str:
    """Build a separator cell of ``width`` characters with alignment markers.

    Width is clamped to a minimum of 3 to satisfy the GFM spec. Colons are
    placed at one or both ends to encode the alignment; ``"default"`` emits
    plain dashes.
    """
    w = max(width, 3)
    if align == "center":
        return ":" + "-" * (w - 2) + ":"
    if align == "right":
        return "-" * (w - 1) + ":"
    if align == "left":
        return ":" + "-" * (w - 1)
    return "-" * w


def format_table(rows: list[list[str]], sep_idx: int | None) -> list[str]:
    """Render a parsed table as aligned, pipe-delimited lines.

    Short rows are padded with empty cells to match the widest row. Column
    widths are computed from data rows only (the separator does not
    influence width). When ``sep_idx`` is provided, that row is rebuilt as
    a proper separator using each column's alignment marker.

    Args:
        rows: Parsed cells per row.
        sep_idx: Index of the separator row, or ``None`` if absent.

    Returns:
        Formatted table lines, one per row, each wrapped in ``| ... |``.
    """
    ncols = max(len(r) for r in rows)
    for r in rows:
        while len(r) < ncols:
            r.append("")

    aligns = ["default"] * ncols
    if sep_idx is not None:
        sep_row = rows[sep_idx]
        aligns = [align_of(c) for c in sep_row]

    widths = [0] * ncols
    for i, r in enumerate(rows):
        if i == sep_idx:
            continue
        for j, c in enumerate(r):
            widths[j] = max(widths[j], cell_width(c))
    widths = [max(w, 3) for w in widths]

    out = []
    for i, r in enumerate(rows):
        if i == sep_idx:
            cells = [make_sep(widths[j], aligns[j]) for j in range(ncols)]
        else:
            cells = [pad(r[j], widths[j], aligns[j]) for j in range(ncols)]
        out.append("| " + " | ".join(cells) + " |")
    return out


def format_text(text: str) -> str:
    """Format every markdown table inside ``text`` and return the new text.

    Walks the input line by line, toggling fenced-code-block state on
    ``````` or ``~~~`` markers so tables inside code blocks
    are left untouched. Contiguous runs of table-like lines are collected,
    parsed, and re-emitted via :func:`format_table` when a separator row is
    found; otherwise the run is returned verbatim. The trailing newline of
    the original text is preserved.
    """
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    in_fence = False
    fence_re = re.compile(r"^(\s*)(```+|~~~+)")
    while i < len(lines):
        line = lines[i]
        if fence_re.match(line):
            in_fence = not in_fence
            out.append(line)
            i += 1
            continue
        if not in_fence and is_table_line(line):
            block = []
            while i < len(lines) and is_table_line(lines[i]) and not fence_re.match(lines[i]):
                block.append(lines[i])
                i += 1
            rows = [split_row(l) for l in block]
            sep_idx = None
            for k, r in enumerate(rows):
                if is_separator(r):
                    sep_idx = k
                    break
            if sep_idx is None or len(rows) < 2:
                out.extend(block)
            else:
                out.extend(format_table(rows, sep_idx))
            continue
        out.append(line)
        i += 1

    result = "\n".join(out)
    if text.endswith("\n"):
        result += "\n"
    return result


def main() -> int:
    """CLI entry point.

    Parses arguments and dispatches based on input source. One or more
    file paths may be passed; each is processed independently:

    * ``-`` reads from stdin (only meaningful as a single argument).
    * With ``-i`` / ``--in-place``, every path is rewritten on disk.
    * Without ``-i``, formatted output for every path is written to
      stdout, concatenated in argument order.

    Returns:
        Process exit code (``0`` on success, ``1`` if any file fails).
    """
    ap = argparse.ArgumentParser(description="Format markdown tables in files.")
    ap.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Markdown file(s); use - for stdin",
    )
    ap.add_argument("-i", "--in-place", action="store_true", help="Write back to each file")
    args = ap.parse_args()

    rc = 0
    for f in args.files:
        try:
            if f == "-":
                if args.in_place:
                    print("fmt-md-tables: -i cannot be used with stdin", file=sys.stderr)
                    rc = 1
                    continue
                sys.stdout.write(format_text(sys.stdin.read()))
                continue

            path = Path(f)
            text = path.read_text(encoding="utf-8")
            formatted = format_text(text)
            if args.in_place:
                path.write_text(formatted, encoding="utf-8")
            else:
                sys.stdout.write(formatted)
        except OSError as e:
            print(f"fmt-md-tables: {f}: {e}", file=sys.stderr)
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
