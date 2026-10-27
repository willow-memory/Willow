"""amounts: a sum is a number written with its currency, dated by its line,
the nearest date above it, or its file's name, each saying so; a number that
could read two ways names no sum."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("amounts", HERE / "amounts.py")
am = importlib.util.module_from_spec(spec)
spec.loader.exec_module(am)
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path, files: dict) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir(parents=True)
    for name, text in files.items():
        p = pile / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
        "--key", str(tmp_path / "k"), *NOW)  # fmt: skip
    return b


def test_every_way_a_sum_is_written_and_every_way_one_is_not():
    assert am.sums("MOT test £54.85, parts £1,840.00") == ["£54.85", "£1,840.00"]
    assert am.sums("sent US$ 9.50 and € 45 and ¥1000") == ["US$ 9.50", "€ 45", "¥1000"]
    assert am.sums("EUR 100 wired; got 45.50 USD and 200 lei back") == [
        "EUR 100",
        "45.50 USD",
        "200 lei",
    ]
    assert am.sums("version 2.5, 3 May, PTO 100, 200 was plenty") == []
    assert am.sums("echo $HOME and $PATH5") == []
    assert am.sums("€1.995 and 100,00 read two ways: not guessed") == []
    assert am.sums("a bare 450 is never money") == []


def test_dated_by_the_line_the_date_above_or_the_file_name_each_saying_so(tmp_path):
    b = box(tmp_path, {
        "log.md": "2026-03-01 paid £450 rent\nthe plumber wants £80\n",
        "bank/2026-04-02.txt": "balance $1,200.50\n",
        "misc.md": "owe Ana $20\n",
    })  # fmt: skip
    got = run(str(HERE / "amounts.py"), "--box", str(b))
    lines = got.stdout.splitlines()
    assert got.returncode == 0 and lines[-1] == "4 sums: 3 dated, 1 undated"
    assert lines[0].startswith("2026-03-01") and "£450" in lines[0]
    assert "£80" in lines[1] and lines[1].endswith("(date from line 1)")
    assert lines[2].startswith("2026-04-02") and "$1,200.50" in lines[2]
    assert lines[2].endswith("(date from file name)")
    assert lines[3].startswith("undated") and "misc.md:1" in lines[3]


def test_dated_rows_come_oldest_first_across_files(tmp_path):
    b = box(tmp_path, {
        "b.md": "2026-01-02 coat $30\n",
        "a.md": "2026-05-01 boots $90\n",
    })  # fmt: skip
    out = run(str(HERE / "amounts.py"), "--box", str(b)).stdout
    assert out.index("$30") < out.index("$90"), "by date, not by file name"


def test_two_sums_on_one_line_are_two_rows_in_the_lines_order():
    pile = [{"path": "a.md", "line": 1, "text": "2026-01-01 sent £10, kept £2"}]
    rows = am.found(pile)
    assert [r["amount"] for r in rows] == ["£10", "£2"]
    assert [r["line"] for r in rows] == [1, 1]


def test_a_date_reaches_down_its_own_file_and_never_another(tmp_path):
    b = box(tmp_path, {
        "a.md": "2026-02-03 lunch\n\nalso £6 coffee\n",
        "z.md": "stamps £3\n",
    })  # fmt: skip
    lines = run(str(HERE / "amounts.py"), "--box", str(b)).stdout.splitlines()
    assert "£6" in lines[0] and lines[0].endswith("(date from line 1)")
    assert lines[1].startswith("undated") and "z.md:1" in lines[1]


def test_a_passage_cut_keeps_each_lines_number():
    long = "\n".join(f"note {i}" for i in range(1, 600)) + "\n2026-01-01 fee £5"
    pile_rows = am.file_lines([
        {"path": "a.md", "line": 1, "text": "\n".join(long.splitlines()[:500])},
        {"path": "a.md", "line": 501, "text": "\n".join(long.splitlines()[500:])},
    ])  # fmt: skip
    assert pile_rows["a.md"][-1] == (600, "2026-01-01 fee £5")


def test_a_long_line_is_cut_at_120_characters():
    text = "2026-01-01 fee £5 then " + "x" * 300
    rows = am.found([{"path": "a.md", "line": 1, "text": text}])
    assert am.show(rows)[0].endswith(text[:120])
    assert text[:121] not in am.show(rows)[0]


def test_no_sums_is_42_and_the_same_folder_gives_the_same_bytes(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(str(HERE / "amounts.py"), "--box", str(b))
    assert got.returncode == 42 and "No sums of money" in got.stdout
    b2 = box(tmp_path / "again", {"log.md": "2026-03-01 paid £450 rent\nowes $20\n"})
    one = run(str(HERE / "amounts.py"), "--box", str(b2)).stdout
    two = run(str(HERE / "amounts.py"), "--box", str(b2)).stdout
    assert one == two


def test_a_bad_command_line_and_a_folder_that_is_no_box_are_refused(tmp_path):
    got = run(str(HERE / "amounts.py"))
    assert got.returncode == 2 and "amounts.py" in got.stderr
    got = run(str(HERE / "amounts.py"), "--box", str(tmp_path))
    assert got.returncode == 2 and "not a kernel box" in got.stderr
