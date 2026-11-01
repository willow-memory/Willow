"""folder-card: a card written to FILE from the pile and your notes: each
file's size, dates and fiction label, files not read, the gaps the `gaps` rule
finds, marked told or untold by your notes, and the gaps you named marked seen
or contradicted; written once, private, the same bytes twice; box untouched."""

from __future__ import annotations

import datetime as dt
import hashlib
import os
import stat
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "folder_card.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def make(tmp_path: Path) -> tuple[Path, Path]:
    pile = tmp_path / "pile"
    (pile / "notes").mkdir(parents=True)
    for d in (
        "01",
        "02",
        "03",
        "04",
        "12",
        "13",
        "14",
    ):  # a gap from the 4th to the 12th
        (pile / "notes" / f"2026-03-{d}.md").write_text(f"day {d}\n")
    (pile / "notes" / "index.md").write_text("an index with no date\n")
    (pile / "diary.md").write_text(
        "FICTIONAL: a made-up diary.\n\n## 2026-01-05\nx\n\n## 2026-01-12\nx\n\n"
        "## 2026-01-19\nx\n\n## 2026-01-26\nx\n"
    )
    (pile / "short.txt").write_text("2026-02-01 one\n")
    (pile / "photo.bin").write_bytes(b"\0\1\2")
    (pile / ".hidden").mkdir()
    (pile / ".hidden" / "x.md").write_text("2020-01-01 secret\n")
    box = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(box), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), *NOW], capture_output=True, check=True)  # fmt: skip
    return box, pile


def card(tmp_path: Path, *extra: str, name: str = "card.md") -> str:
    box, _ = (
        make(tmp_path) if not (tmp_path / "box").exists() else (tmp_path / "box", None)
    )
    got = run("--box", str(box), "--to", str(tmp_path / name), *extra)
    assert got.returncode == 0, got.stderr
    return (tmp_path / name).read_text()


def test_each_file_has_its_size_dates_and_fiction_label(tmp_path):
    text = card(tmp_path)
    assert (
        "## Files (11: 10 read, 1 not)" in text
    )  # the hidden folder's file is not counted
    assert (
        "`diary.md`: " in text
        and "4 dated days, 2026-01-05 to 2026-01-26; labels itself fiction" in text
    )
    assert (
        "- `notes/`: 7 files named by a date, 2026-03-01 to 2026-03-14, 49 bytes"
        in text
    )
    assert "`notes/2026-03-04.md`" not in text  # a folder of them is one line
    assert "`short.txt`: 15 bytes, one dated line, 2026-02-01" in text
    assert "`notes/index.md`: 22 bytes, no dated line" in text
    assert "`photo.bin`: 3 bytes, not read" in text
    assert "secret" not in text and ".hidden" not in text


def test_gaps_come_from_the_gaps_rule_and_say_what_they_are(tmp_path):
    text = card(tmp_path)
    assert "GAP 2026-03-04 to 2026-03-12, 7 days with no entry; untold" in text
    assert (
        "`notes/`, files named by a date, 7 entries, 2026-03-01 to 2026-03-14" in text
    )
    assert "UNDATED `notes/index.md`" in text
    assert (
        "`diary.md`, lines that start with a date, 4 entries, 2026-01-05 to 2026-01-26"
        in text
    )
    assert "no gap" in text
    assert (
        "`short.txt`, lines that start with a date, 1 entry: too few for a rhythm"
        in text
    )
    assert "never days when nothing happened" in text


def test_your_notes_mark_a_gap_told_and_are_kept_word_for_word(tmp_path):
    n = tmp_path / "me.txt"
    n.write_text(
        "gap 2026-03-06 to 2026-03-10 flu, no writing\nTyped up from paper.\n\n  Odd   spacing  kept\n"
    )
    text = card(tmp_path, "--notes", str(n))
    assert (
        "GAP 2026-03-04 to 2026-03-12, 7 days with no entry; told: flu, no writing"
        in text
    )
    assert "- 2026-03-06 to 2026-03-10: flu, no writing (the files show it too)" in text
    assert "## Your notes\n\nTyped up from paper.\n  Odd   spacing  kept\n" in text


def test_a_gap_you_named_that_the_files_contradict_or_do_not_show_is_said(tmp_path):
    n = tmp_path / "me.txt"
    n.write_text("gap 2026-03-01 - 2026-03-02 away\nGAP 2026-05-01 2026-05-09\n")
    text = card(tmp_path, "--notes", str(n))
    assert (
        "2026-03-01 to 2026-03-02: away (the files hold 2 dated entries inside it)"
        in text
    )
    assert (
        "2026-05-01 to 2026-05-09: no reason given (the files show no gap there)"
        in text
    )
    assert "GAP 2026-03-04 to 2026-03-12, 7 days with no entry; untold" in text


def test_a_gap_line_that_does_not_read_is_listed_not_dropped(tmp_path):
    n = tmp_path / "me.txt"
    n.write_text(
        "gap 2026-02-31 to 2026-03-02 bad day\ngap 2026-03-09 to 2026-03-02 backwards\ngap sometime\n"
    )
    text = card(tmp_path, "--notes", str(n))
    assert text.count("could not be read as one") == 1
    for ln in ("gap 2026-02-31 to 2026-03-02 bad day", "gap sometime", "backwards"):
        assert ln in text
    assert "## Gaps you know of\n\nNone named." in text


def test_without_notes_there_is_no_notes_section_and_with_now_the_open_gap_shows(
    tmp_path,
):
    text = card(tmp_path)
    assert "Gaps you know of" not in text and "Your notes" not in text
    text = card(tmp_path, *NOW, name="later.md")
    assert "SINCE 2026-03-14 to 2026-10-24" in text


def test_the_same_pile_gives_the_same_bytes_and_the_card_is_written_once_private(
    tmp_path,
):
    a = card(tmp_path, name="a.md")
    b = card(tmp_path, name="b.md")
    assert a == b
    assert stat.S_IMODE(os.stat(tmp_path / "a.md").st_mode) == 0o600
    before = (tmp_path / "a.md").read_bytes()
    got = run("--box", str(tmp_path / "box"), "--to", str(tmp_path / "a.md"))
    assert got.returncode == 2 and (tmp_path / "a.md").read_bytes() == before


def test_the_box_and_pile_are_not_changed(tmp_path):
    box, pile = make(tmp_path)

    def snap() -> dict:
        return {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                for d in (box, pile) for p in sorted(d.rglob("*")) if p.is_file()}  # fmt: skip

    before = snap()
    card(tmp_path)
    assert snap() == before


def test_an_empty_pile_still_gives_a_card_that_says_nothing_is_dated(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    box = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(box), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), *NOW], capture_output=True, check=True)  # fmt: skip
    text = card(tmp_path)
    assert "## Files (0: 0 read, 0 not)" in text and "Nothing dated" in text


def test_refusals(tmp_path):
    box, _ = make(tmp_path)
    to = str(tmp_path / "c.md")
    for argv in ([], ["--box", str(box)], ["--to", to], ["--box", str(box), "--to", to, "extra"],
                 ["--box", str(box), "--to", to, "--now", "soon"],
                 ["--box", str(box), "--to", to, "--notes"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "folder_card.py" in got.stderr, argv
    assert run("--box", str(tmp_path), "--to", to).returncode == 2  # not a box
    got = run("--box", str(box), "--to", to, "--notes", str(tmp_path / "none.txt"))
    assert got.returncode == 2 and "notes" in got.stderr and not Path(to).exists()
    assert (
        run(
            "--box", str(box), "--to", str(tmp_path / "no" / "such" / "c.md")
        ).returncode
        == 2
    )
    assert not (tmp_path / "no").exists()  # a missing folder is refused, not made


def test_a_few_date_named_files_are_listed_one_by_one(tmp_path):
    box, pile = make(tmp_path)
    (pile / "notes").rename(pile / "few")
    for f in sorted((pile / "few").glob("2026-03-1*")) + [
        pile / "few" / "2026-03-04.md"
    ]:
        f.unlink()
    text = card(tmp_path)
    assert (
        "`few/2026-03-01.md`: 7 bytes, named for 2026-03-01" in text
        and "`few/`:" not in text
    )


def test_a_log_lists_its_longest_gaps_and_every_gap_you_named(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    base = dt.date(2025, 1, 5)
    ds = [dt.date(2025, 1, i) for i in (1, 2, 3, 4, 5)]
    cur = base
    for n in range(13):
        cur += dt.timedelta(days=5 + n)
        ds.append(cur)
        for _ in range(3):  # a run of daily entries so the typical spacing stays 1
            cur += dt.timedelta(days=1)
            ds.append(cur)
    (pile / "log.md").write_text("\n\n".join(f"{d} x" for d in ds) + "\n")
    box = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(box), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), *NOW], capture_output=True, check=True)  # fmt: skip
    plain = card(tmp_path)
    assert plain.count("  - GAP ") == 10 and "3 shorter gaps not listed" in plain
    first = base + dt.timedelta(days=1)  # inside the shortest gap, which is the first
    n = tmp_path / "n.txt"
    n.write_text(f"gap {first} to {first} short one\n")
    told = card(tmp_path, "--notes", str(n), name="t.md")
    assert told.count("  - GAP ") == 10 and "told: short one" in told
