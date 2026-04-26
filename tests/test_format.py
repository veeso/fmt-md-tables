"""Unit tests for the formatter functions in :mod:`fmt_md_tables`."""
from __future__ import annotations

import textwrap

import pytest

from fmt_md_tables import (
    align_of,
    format_text,
    is_separator,
    is_table_line,
    make_sep,
    pad,
    split_row,
)


# ---------------------------------------------------------------------------
# split_row
# ---------------------------------------------------------------------------

class TestSplitRow:
    def test_strips_outer_pipes(self):
        assert split_row("| a | b | c |") == ["a", "b", "c"]

    def test_no_outer_pipes(self):
        assert split_row("a | b | c") == ["a", "b", "c"]

    def test_only_leading_pipe(self):
        assert split_row("| a | b") == ["a", "b"]

    def test_only_trailing_pipe(self):
        assert split_row("a | b |") == ["a", "b"]

    def test_strips_whitespace(self):
        assert split_row("|   a   |  b |") == ["a", "b"]

    def test_escaped_pipe_is_kept(self):
        assert split_row(r"| a \| b | c |") == [r"a \| b", "c"]

    def test_empty_cells(self):
        assert split_row("| | b | |") == ["", "b", ""]


# ---------------------------------------------------------------------------
# is_table_line / is_separator
# ---------------------------------------------------------------------------

class TestIsTableLine:
    @pytest.mark.parametrize("line", ["| a | b |", "a | b", "|x|"])
    def test_yes(self, line: str):
        assert is_table_line(line)

    @pytest.mark.parametrize("line", ["plain text", "", "|", "  |  "])
    def test_no(self, line: str):
        assert not is_table_line(line)


class TestIsSeparator:
    @pytest.mark.parametrize("cells", [
        ["---"],
        ["---", "---"],
        [":---", "---:", ":---:"],
        ["-" * 10],
    ])
    def test_yes(self, cells: list[str]):
        assert is_separator(cells)

    @pytest.mark.parametrize("cells", [
        [],
        ["---", "abc"],
        ["a", "b"],
        ["::---"],
    ])
    def test_no(self, cells: list[str]):
        assert not is_separator(cells)


# ---------------------------------------------------------------------------
# align_of / pad / make_sep
# ---------------------------------------------------------------------------

class TestAlignOf:
    @pytest.mark.parametrize("cell,expected", [
        ("---", "default"),
        (":---", "left"),
        ("---:", "right"),
        (":---:", "center"),
        ("  :---:  ", "center"),
    ])
    def test_align(self, cell: str, expected: str):
        assert align_of(cell) == expected


class TestPad:
    def test_left_default(self):
        assert pad("ab", 5, "default") == "ab   "
        assert pad("ab", 5, "left") == "ab   "

    def test_right(self):
        assert pad("ab", 5, "right") == "   ab"

    def test_center_even(self):
        assert pad("ab", 6, "center") == "  ab  "

    def test_center_odd_extra_right(self):
        assert pad("ab", 5, "center") == " ab  "


class TestMakeSep:
    def test_default(self):
        assert make_sep(5, "default") == "-----"

    def test_left(self):
        assert make_sep(5, "left") == ":----"

    def test_right(self):
        assert make_sep(5, "right") == "----:"

    def test_center(self):
        assert make_sep(5, "center") == ":---:"

    def test_min_width_3(self):
        assert make_sep(1, "default") == "---"
        assert make_sep(2, "center") == ":-:"


# ---------------------------------------------------------------------------
# format_text — behavioural invariants
# ---------------------------------------------------------------------------

class TestFormatText:
    def test_pads_to_max_column_width(self):
        src = textwrap.dedent("""\
            | a | bbb |
            |---|-----|
            | longer | x |
        """)
        out = format_text(src)
        assert out == textwrap.dedent("""\
            | a      | bbb |
            | ------ | --- |
            | longer | x   |
        """)

    def test_preserves_alignment_markers(self):
        src = textwrap.dedent("""\
            | l | c | r |
            |:--|:-:|--:|
            | 1 | 2 | 3 |
        """)
        out = format_text(src).splitlines()
        # separator row
        assert out[1] == "| :-- | :-: | --: |"
        # right-aligned column should right-justify
        assert out[2].endswith("3 |")
        assert "| " + " " * 2 + "3 |" in out[2]

    def test_skips_fenced_code_block(self):
        src = textwrap.dedent("""\
            ```
            | a | b |
            |---|---|
            | 1 | 2 |
            ```
        """)
        assert format_text(src) == src

    def test_skips_tilde_fenced_block(self):
        src = textwrap.dedent("""\
            ~~~
            | a | b |
            |---|---|
            ~~~
        """)
        assert format_text(src) == src

    def test_table_outside_fence_still_formatted(self):
        src = textwrap.dedent("""\
            | a | b |
            |---|---|
            | 1 | 2 |

            ```
            | x | y |
            ```
        """)
        out = format_text(src)
        assert "| a   | b   |" in out
        assert "| x | y |" in out  # untouched inside fence

    def test_block_without_separator_left_alone(self):
        src = "| a | b |\n| 1 | 2 |\n"
        assert format_text(src) == src

    def test_short_rows_padded(self):
        src = textwrap.dedent("""\
            | a | b | c |
            |---|---|---|
            | 1 | 2 |
        """)
        out = format_text(src)
        last = [l for l in out.splitlines() if l.strip()][-1]
        assert last.count("|") == 4  # 3 cells + outer pipes
        assert last.endswith("|     |")  # padded empty cell (min col width 3)

    def test_escaped_pipe_kept(self):
        src = textwrap.dedent(r"""
            | col |
            |-----|
            | a \| b |
        """).lstrip()
        out = format_text(src)
        assert r"a \| b" in out

    def test_trailing_newline_preserved(self):
        with_nl = "| a |\n|---|\n| 1 |\n"
        without_nl = "| a |\n|---|\n| 1 |"
        assert format_text(with_nl).endswith("\n")
        assert not format_text(without_nl).endswith("\n")

    def test_separator_min_width_three(self):
        src = "| a |\n|-|\n| b |\n"
        out = format_text(src).splitlines()
        assert out[1] == "| --- |"

    def test_multiple_tables(self):
        src = textwrap.dedent("""\
            | a | b |
            |---|---|
            | 1 | 2 |

            text

            | x | y |
            |---|---|
            | 9 | 10 |
        """)
        out = format_text(src)
        assert "| a   | b   |" in out
        assert "| 9   | 10  |" in out

    def test_idempotent(self):
        src = textwrap.dedent("""\
            | a | bbb |
            |---|-----|
            | longer | x |
        """)
        once = format_text(src)
        twice = format_text(once)
        assert once == twice


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class TestCli:
    def _write(self, path, text: str) -> None:
        path.write_text(text, encoding="utf-8")

    def test_in_place_single(self, tmp_path, monkeypatch):
        from fmt_md_tables import main

        f = tmp_path / "a.md"
        self._write(f, "| a | b |\n|---|---|\n| 1 | 2 |\n")
        monkeypatch.setattr("sys.argv", ["fmt-md-tables", "-i", str(f)])
        assert main() == 0
        assert "| a   | b   |" in f.read_text()

    def test_in_place_multi(self, tmp_path, monkeypatch):
        from fmt_md_tables import main

        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        self._write(a, "| a | b |\n|---|---|\n| 1 | 2 |\n")
        self._write(b, "| x | y |\n|---|---|\n| 9 | 10 |\n")
        monkeypatch.setattr("sys.argv", ["fmt-md-tables", "-i", str(a), str(b)])
        assert main() == 0
        assert "| a   | b   |" in a.read_text()
        assert "| 9   | 10  |" in b.read_text()

    def test_stdout_concatenates(self, tmp_path, monkeypatch, capsys):
        from fmt_md_tables import main

        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        self._write(a, "| a |\n|---|\n| 1 |\n")
        self._write(b, "| b |\n|---|\n| 2 |\n")
        monkeypatch.setattr("sys.argv", ["fmt-md-tables", str(a), str(b)])
        assert main() == 0
        captured = capsys.readouterr().out
        assert captured.count("| ---") == 2

    def test_missing_file_returns_1_continues(self, tmp_path, monkeypatch, capsys):
        from fmt_md_tables import main

        good = tmp_path / "good.md"
        self._write(good, "| a |\n|---|\n| 1 |\n")
        missing = tmp_path / "nope.md"
        monkeypatch.setattr(
            "sys.argv", ["fmt-md-tables", str(missing), str(good)]
        )
        assert main() == 1
        out = capsys.readouterr()
        assert "| a   |" in out.out
        assert "nope.md" in out.err

    def test_stdin_with_in_place_errors(self, monkeypatch, capsys):
        from fmt_md_tables import main

        monkeypatch.setattr("sys.argv", ["fmt-md-tables", "-i", "-"])
        assert main() == 1
        assert "stdin" in capsys.readouterr().err
