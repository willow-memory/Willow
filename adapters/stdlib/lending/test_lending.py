"""lending: what was lent and what came back, every line kept, parts
counted, absence said as absence, two dates both shown."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def lending(tmp_path: Path, files: dict[str, str]) -> subprocess.CompletedProcess:
    pile = tmp_path / "pile"
    for name, text in files.items():
        (pile / name).parent.mkdir(parents=True, exist_ok=True)
        (pile / name).write_text(text)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile), "--key",
        str(tmp_path / "k"), *NOW)  # fmt: skip
    return run(str(HERE / "lending.py"), "--box", str(b))


def blocks(out: str) -> list[list[str]]:
    got: list[list[str]] = []
    for line in out.splitlines():
        if line.startswith(" "):
            got[-1].append(line.strip())
        else:
            got.append([line])
    return got


def test_a_set_in_parts_is_out_until_every_part_is_back(tmp_path):
    got = lending(tmp_path, {
        "notes/2026-10-01.md": "Mara borrowed the Foxfire set (3 volumes).\n",
        "notes/2026-10-25.md": "2026-10-24 Mara gave back volumes 1 and 3.\n",
    })  # fmt: skip
    assert got.returncode == 0
    [b] = blocks(got.stdout)
    assert b[0].startswith("PART BACK  Foxfire set  to Mara  since 2026-10-01")
    assert b[0].endswith("parts out: 2 of 3")
    assert b[1].startswith("2026-10-01  notes/2026-10-01.md:1")
    # the line's own date and the file's are two facts: both shown
    assert b[2].startswith("2026-10-24  notes/2026-10-25.md:1")
    assert b[2].endswith("(filed 2026-10-25)")


def test_the_last_part_back_closes_it_and_every_line_stays(tmp_path):
    got = lending(tmp_path, {
        "a/2026-10-01.md": "Mara borrowed the Foxfire set (3 volumes).\n",
        "a/2026-10-24.md": "Mara gave back volumes 1 and 3.\n",
        "a/2026-11-03.md": "Mara returned volume 2 of the Foxfire set.\n",
    })  # fmt: skip
    [b] = blocks(got.stdout)
    assert b[0] == "BACK       Foxfire set  to Mara  2026-10-01 to 2026-11-03"
    assert len(b) == 4  # the loan and both returns, none merged away


def test_no_return_written_is_said_and_out_comes_first(tmp_path):
    got = lending(tmp_path, {
        "2026-08-02.md": "Lent the ladder to Dev.\n",
        "2026-08-30.md": "Got the ladder back from Dev.\n",
        "2026-09-01.md": "Lent Teo my good drill.\n",
    })  # fmt: skip
    b = blocks(got.stdout)
    assert (
        b[0][0] == "OUT        good drill  to Teo  since 2026-09-01  no return written"
    )
    assert b[1][0] == "BACK       ladder  to Dev  2026-08-02 to 2026-08-30"


def test_a_return_with_no_loan_is_listed_not_dropped(tmp_path):
    got = lending(tmp_path, {
        "2026-08-30.md": "Priya returned the cake pan.\n",
        "2026-09-01.md": "Lent the tent to Sol.\n",
    })  # fmt: skip
    b = blocks(got.stdout)
    assert b[0][0].startswith("OUT        tent  to Sol")
    assert b[1][0] == "BACK?      cake pan  from Priya  back, no loan written"


def test_a_return_answers_the_right_person_and_thing(tmp_path):
    got = lending(tmp_path, {
        "2026-01-01.md": "Lent the drill to Dev.\nLent the saw to Dev.\nLent the drill to Ana.\n",
        "2026-02-01.md": "Got the drill back from Dev.\n",
    })  # fmt: skip
    heads = [b[0] for b in blocks(got.stdout)]
    assert heads == [
        "OUT        saw  to Dev  since 2026-01-01  no return written",
        "OUT        drill  to Ana  since 2026-01-01  no return written",
        "BACK       drill  to Dev  2026-01-01 to 2026-02-01",
    ]


def test_a_second_loan_of_the_same_thing_is_its_own(tmp_path):
    got = lending(tmp_path, {
        "2026-01-01.md": "Lent the tent to Sol.\n",
        "2026-02-01.md": "Sol returned the tent.\n",
        "2026-03-01.md": "Lent the tent to Sol.\n",
    })  # fmt: skip
    heads = [b[0] for b in blocks(got.stdout)]
    assert heads == [
        "OUT        tent  to Sol  since 2026-03-01  no return written",
        "BACK       tent  to Sol  2026-01-01 to 2026-02-01",
    ]


def test_undated_lines_come_after_dated_ones(tmp_path):
    got = lending(tmp_path, {
        "misc.md": "Lent the kayak to Jo.\n",
        "2026-05-05.md": "Lent the canoe to Jo.\n",
    })  # fmt: skip
    heads = [b[0] for b in blocks(got.stdout)]
    assert heads[0].startswith("OUT        canoe  to Jo  since 2026-05-05")
    assert heads[1].startswith("OUT        kayak  to Jo  since undated")


def test_lowercase_is_not_a_person(tmp_path):
    got = lending(tmp_path, {"a.md": "The bank lent money to people in need.\n"})
    assert got.returncode == 42
    assert "Nothing in your folder" in got.stdout


def test_refused_without_a_box(tmp_path):
    assert run(str(HERE / "lending.py"), "--box", str(tmp_path)).returncode == 2
