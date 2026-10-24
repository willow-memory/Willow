"""timeline: one matter's lines, by date, each cited; two dates both shown,
undated lines kept, nothing merged; written only where --to points."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]

TENANCY = {
    "tenancy/log.md": "# Flat 2\n\n2026-03-01 Reported the mould in the back bedroom.\n"
    "The landlord said someone would come.\n\n"
    "2026-03-20 Mould back on the ceiling, landlord not answering.\n",
    "letters/2026-03-10.md": "2026-03-09 Wrote to the landlord about the mould.\n",
    "tenancy/2026-04-02.md": "Still no visit from the landlord; mould spreading.\n",
    "tenancy/misc.md": "The landlord's number is in the blue book. Mould spray under the sink.\n",
    "garden.md": "Tomatoes want sun.\n",
}


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path, files: dict[str, str], *extra: str) -> Path:
    pile = tmp_path / "pile"
    for name, text in files.items():
        (pile / name).parent.mkdir(parents=True, exist_ok=True)
        (pile / name).write_text(text)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile), "--key",
        str(tmp_path / "k"), *NOW, *extra)  # fmt: skip
    return b


def timeline(b: Path, to: Path, words: str) -> subprocess.CompletedProcess:
    return run(str(HERE / "timeline.py"), "--box", str(b), "--to", str(to), words)


def snapshot(root: Path) -> dict[str, bytes]:
    return {str(p): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def test_the_whole_page_every_line_cited_and_dated_as_it_says(tmp_path):
    b = box(tmp_path, TENANCY)
    to = tmp_path / "out" / "mould.txt"
    to.parent.mkdir()
    before = snapshot(tmp_path / "pile")
    got = timeline(b, to, "mould landlord")
    assert got.returncode == 0, got.stderr
    assert got.stdout == f"wrote 6 lines to {to}; 1 undated\n"
    assert to.read_text() == (
        "Timeline: mould landlord\n"
        "\n"
        "6 lines, oldest first: 5 dated, 1 undated.\n"
        "Every line of each passage in the folder that holds these words, as\n"
        "written, with its file and line. A line's own date and the date its\n"
        "file is named for are both shown when they differ.\n"
        "\n"
        "2026-03-01  tenancy/log.md:3         2026-03-01 Reported the mould in the back bedroom.\n"
        "2026-03-01  tenancy/log.md:4         The landlord said someone would come.  (date from line 3)\n"
        "2026-03-09  letters/2026-03-10.md:1  2026-03-09 Wrote to the landlord about the mould.  (filed 2026-03-10)\n"
        "2026-03-20  tenancy/log.md:6         2026-03-20 Mould back on the ceiling, landlord not answering.\n"
        "2026-04-02  tenancy/2026-04-02.md:1  Still no visit from the landlord; mould spreading.  (date from file name)\n"
        "undated     tenancy/misc.md:1        The landlord's number is in the blue book. Mould spray under the sink.\n"
    )
    assert snapshot(tmp_path / "pile") == before, "originals are never changed"
    if os.name == "posix":
        assert to.stat().st_mode & 0o777 == 0o600


def test_the_same_folder_gives_the_same_bytes_wherever_it_lives(tmp_path):
    one, two = tmp_path / "one", tmp_path / "two" / "deeper"
    for t in (one, two):
        t.mkdir(parents=True)
        timeline(box(t, TENANCY), t / "t.txt", "mould landlord")
    assert (one / "t.txt").read_bytes() == (two / "t.txt").read_bytes()
    assert str(tmp_path) not in (one / "t.txt").read_text()


def test_a_heading_dates_the_lines_under_it_and_its_file_date_is_shown(tmp_path):
    b = box(tmp_path, {
        "2026-10-25.md": "Knee physio notes\n\n2026-10-24\nPhysio said rest the knee.\n"
                         "Knee still swollen at night.\n",
    })  # fmt: skip
    timeline(b, tmp_path / "t.txt", "knee")
    rows = (tmp_path / "t.txt").read_text().splitlines()[7:]
    assert rows == [
        "2026-10-24  2026-10-25.md:3  2026-10-24  (filed 2026-10-25)",
        "2026-10-24  2026-10-25.md:4  Physio said rest the knee.  (date from line 3; filed 2026-10-25)",
        "2026-10-24  2026-10-25.md:5  Knee still swollen at night.  (date from line 3; filed 2026-10-25)",
        "2026-10-25  2026-10-25.md:1  Knee physio notes  (date from file name)",
    ]


def test_a_line_is_placed_at_the_date_it_starts_with_and_dates_the_next(tmp_path):
    b = box(tmp_path, {
        "log.md": "2026-03-05 Hearing set for 2026-12-01, landlord told.\n"
                  "Landlord says the mould is fixed.\n"
                  "Landlord moved the hearing from 2026-12-01 to 2027-01-12.\n",
    })  # fmt: skip
    timeline(b, tmp_path / "t.txt", "landlord")
    rows = (tmp_path / "t.txt").read_text().splitlines()[7:]
    assert rows == [
        # written in March: neither it nor the line under it is December
        "2026-03-05  log.md:1  2026-03-05 Hearing set for 2026-12-01, landlord told."
        "  (names several dates; placed at the one it starts with)",
        "2026-03-05  log.md:2  Landlord says the mould is fixed.  (date from line 1)",
        "2027-01-12  log.md:3  Landlord moved the hearing from 2026-12-01 to 2027-01-12."
        "  (names several dates; placed at the latest)",
    ]


def test_the_nearest_date_above_not_the_latest(tmp_path):
    b = box(tmp_path, {
        "log.md": "2026-05-01\nKnee physio booked.\n\n2026-02-01\nKnee hurt on the stairs.\n",
    })  # fmt: skip
    timeline(b, tmp_path / "t.txt", "knee")
    rows = (tmp_path / "t.txt").read_text().splitlines()[7:]
    assert rows == [
        "2026-02-01  log.md:4  2026-02-01",
        "2026-02-01  log.md:5  Knee hurt on the stairs.  (date from line 4)",
        "2026-05-01  log.md:1  2026-05-01",
        "2026-05-01  log.md:2  Knee physio booked.  (date from line 1)",
    ]


def test_a_heading_in_one_file_never_dates_another(tmp_path):
    b = box(tmp_path, {
        "a.md": "2026-01-05 Rent paid.\n",
        "b.md": "Rent increase letter came.\n",
    })  # fmt: skip
    timeline(b, tmp_path / "t.txt", "rent")
    rows = (tmp_path / "t.txt").read_text().splitlines()[7:]
    assert rows == [
        "2026-01-05  a.md:1  2026-01-05 Rent paid.",
        "undated     b.md:1  Rent increase letter came.",
    ]


def test_a_date_that_could_be_either_way_round_is_never_read(tmp_path):
    b = box(tmp_path, {
        "x.md": "11/03/2026 Council called about the fence.\n",
        "y.md": "21/03/2026 Council wrote about the fence.\n",
    })  # fmt: skip
    timeline(b, tmp_path / "t.txt", "council fence")
    rows = (tmp_path / "t.txt").read_text().splitlines()[7:]
    assert rows == [
        "2026-03-21  y.md:1  21/03/2026 Council wrote about the fence.",
        "undated     x.md:1  11/03/2026 Council called about the fence.",
    ]


def test_nothing_is_merged_away_and_undated_come_last_by_file_and_line(tmp_path):
    memo = "Asked the clinic for the scan results.\n"
    b = box(tmp_path, {
        "z.md": "Clinic visit two.\n\n\n\n\n\n\n\n\nClinic visit eleven.\n",
        "a/2026-05-01.md": memo,
        "b/2026-02-01.md": memo,
        "m.md": memo,
    })  # fmt: skip
    timeline(b, tmp_path / "t.txt", "clinic")
    rows = (tmp_path / "t.txt").read_text().splitlines()[7:]
    assert [r.split()[:2] for r in rows] == [
        ["2026-02-01", "b/2026-02-01.md:1"],
        ["2026-05-01", "a/2026-05-01.md:1"],
        ["undated", "m.md:1"],
        ["undated", "z.md:1"],
        ["undated", "z.md:10"],
    ]


def test_a_passage_is_in_when_it_holds_half_the_words(tmp_path):
    b = box(tmp_path, {
        "a.md": "The boiler broke.\n",
        "b.md": "Boiler engineer came, the landlord paid.\n",
        "c.md": "Engineer for the car.\n",
        "boiler/d.md": "Part ordered.\n",
    })  # fmt: skip
    timeline(b, tmp_path / "t.txt", "boiler landlord engineer")
    text = (tmp_path / "t.txt").read_text()
    # two of three words held: in; one of three: out; a folder's name holds
    assert "b.md:1" in text and "a.md:1" not in text and "c.md:1" not in text
    timeline(b, tmp_path / "u.txt", "boiler landlord")
    text = (tmp_path / "u.txt").read_text()
    assert all(f"{p}:1" in text for p in ("a.md", "b.md", "boiler/d.md"))
    assert "c.md:1" not in text


def test_their_words_list_is_used(tmp_path):
    words = tmp_path / "words.txt"
    words.write_text("doctor = gp, clinic\n")
    words.chmod(0o600)
    b = box(tmp_path, {"a.md": "Saw the GP about my back.\n"}, "--words", str(words))
    got = timeline(b, tmp_path / "t.txt", "doctor")
    assert got.returncode == 0 and "a.md:1" in (tmp_path / "t.txt").read_text()
    words.chmod(0o644)
    got = timeline(b, tmp_path / "u.txt", "doctor")
    assert got.returncode == 2 and got.stderr.startswith("refused")
    assert not (tmp_path / "u.txt").exists()


def test_nothing_held_writes_nothing_and_says_so(tmp_path):
    b = box(tmp_path, TENANCY)
    got = timeline(b, tmp_path / "t.txt", "frost")
    assert got.returncode == 42
    assert got.stdout == 'Nothing in your folder holds "frost". Nothing written.\n'
    assert not (tmp_path / "t.txt").exists()
    got = timeline(b, tmp_path / "t.txt", "the and of")
    assert got.returncode == 42 and "say more" in got.stdout
    assert not (tmp_path / "t.txt").exists()


def test_a_file_inside_the_folder_or_the_box_is_refused(tmp_path):
    b = box(tmp_path, TENANCY)
    before = snapshot(tmp_path)
    for to in (tmp_path / "pile" / "t.txt", tmp_path / "pile" / "tenancy" / "t.txt",
               b / "t.txt"):  # fmt: skip
        got = timeline(b, to, "mould")
        assert got.returncode == 2 and got.stderr.startswith("refused"), got.stderr
        assert "never writes there" in got.stderr
    assert snapshot(tmp_path) == before, "a refusal writes nothing"


def test_it_never_overwrites(tmp_path):
    b = box(tmp_path, TENANCY)
    to = tmp_path / "t.txt"
    to.write_text("handed to the solicitor\n")
    got = timeline(b, to, "mould")
    assert got.returncode == 2 and "never overwrites" in got.stderr
    assert to.read_text() == "handed to the solicitor\n"
    got = timeline(b, tmp_path / "no" / "such" / "t.txt", "mould")
    assert got.returncode == 2 and got.stderr.startswith("refused: could not write")


def test_refused_without_a_box_or_a_file_or_words(tmp_path):
    b = box(tmp_path, TENANCY)
    script = str(HERE / "timeline.py")
    for argv in (
        ["--box", str(tmp_path), "--to", str(tmp_path / "t.txt"), "mould"],
        ["--box", str(b), "mould"],
        ["--to", str(tmp_path / "t.txt"), "mould"],
        ["--box", str(b), "--to", str(tmp_path / "t.txt")],
        ["--box", str(b), "--to", str(tmp_path / "t.txt"), "mould", "more"],
    ):
        got = run(script, *argv)
        assert got.returncode == 2 and got.stderr, argv
    assert not (tmp_path / "t.txt").exists()


def test_a_line_whose_one_date_is_mid_line_is_placed_at_it(tmp_path):
    b = box(
        tmp_path, {"log.md": "Wrote to the landlord on 2026-03-09 about the mould.\n"}
    )
    timeline(b, tmp_path / "t.txt", "landlord")
    rows = (tmp_path / "t.txt").read_text().splitlines()[7:]
    assert rows == [
        "2026-03-09  log.md:1  Wrote to the landlord on 2026-03-09 about the mould."
    ]
