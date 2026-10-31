"""said: a quote is read by shape (a chat's stamp, a speech verb, or
quotation marks), a field label never passes for a speaker, and the timeline
is dated as the files say, oldest first."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("said", HERE / "said.py")
sd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sd)
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


def test_the_three_shapes_are_read():
    assert sd.spoken("[13/12/2024, 08:10:00] Dev Raman: I can do 600 tonight") == (
        "Dev Raman", "I can do 600 tonight")  # fmt: skip
    assert sd.spoken("17/04/2023, 12:27 pm - Mags: Terry says he owes $10") == (
        "Mags", "Terry says he owes $10")  # fmt: skip
    assert sd.spoken("Sam said: we'll cover the parts") == (
        "Sam", "we'll cover the parts")  # fmt: skip
    assert sd.spoken("Ana wrote that the fence can wait") == (
        "Ana", "that the fence can wait")  # fmt: skip
    assert sd.spoken('Mags: "no way"') == ("Mags", '"no way"')
    assert sd.spoken("Siobhán replied, fine, come Tuesday")[0] == "Siobhán"


def test_a_field_label_or_a_bare_colon_never_passes_for_a_speaker():
    for line in ("Subject: Roof estimate", "TODO: ring the bank",
                 "RE: the quote", "Ana: we'll move the fence",
                 "Date: Thu, 14 Oct 2026 09:15:00 +0100",
                 "12 Main St: turn left at the church",
                 "Total: £214.60"):  # fmt: skip
        assert sd.spoken(line) is None, line


def test_a_stamped_line_needs_no_quotation_marks_a_bare_one_always_does():
    assert sd.spoken("Ana: come at six") is None
    assert sd.spoken("[2026-01-02 09:00] Ana: come at six") is not None
    assert sd.spoken('Ana: "come at six"') is not None


def test_the_timeline_is_dated_as_the_files_say_oldest_first(tmp_path):
    b = box(tmp_path, {
        "chats/mags.txt": "17/04/2023, 12:27 pm - Mags: the footy was robbed\n",
        "minutes/2026-02-03.md": "Sam said: the parts are on us\n",
        "notes.md": 'Colleen: "bring the photos"\n',
    })  # fmt: skip
    got = run(str(HERE / "said.py"), "--box", str(b))
    lines = got.stdout.splitlines()
    assert got.returncode == 0
    assert lines[0].startswith("2023-04-17") and "Mags" in lines[0]
    assert lines[1].startswith("2026-02-03") and lines[1].endswith(
        "(date from file name)"
    )
    assert lines[2].startswith("undated") and "Colleen" in lines[2]
    assert lines[3] == "3 quotes by 3 speakers, 1 undated"


def test_who_narrows_by_the_speakers_own_words(tmp_path):
    rows = sd.quotes([{"path": "c.txt", "line": 1, "text": (
        "[2026-01-02 09:00] Mags Doyle: the kettle's on\n"
        "[2026-01-03 09:00] Mags Riley: mine too\n"
        "[2026-01-04 09:00] Dev: on my way\n")}])  # fmt: skip
    assert len(sd.by("mags", rows)) == 2
    assert [r["who"] for r in sd.by("mags doyle", rows)] == ["Mags Doyle"]
    assert sd.by("doyle mags", rows), "order doesn't matter, the words do"
    got_box_check = sd.by("gerry", rows)
    assert got_box_check == []


def test_a_quote_is_cut_at_90_characters_and_the_tally_counts_speakers():
    long = "[2026-01-02 09:00] Ana: " + "x" * 300
    rows = sd.quotes([{"path": "c.txt", "line": 1, "text": long}])
    shown = sd.show(rows)
    assert "x" * 90 in shown[0] and "x" * 91 not in shown[0]
    assert shown[-1] == "1 quotes by 1 speaker, 0 undated"


def test_nothing_quoted_and_nobody_by_that_name_both_escalate(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(str(HERE / "said.py"), "--box", str(b))
    assert got.returncode == 42 and "quotes anyone" in got.stdout
    b2 = box(tmp_path / "b2", {"c.txt": "[2026-01-02 09:00] Ana: here\n"})
    got = run(str(HERE / "said.py"), "--box", str(b2), "gerry")
    assert got.returncode == 42 and 'answers to "gerry"' in got.stdout
    one = run(str(HERE / "said.py"), "--box", str(b2)).stdout
    assert one == run(str(HERE / "said.py"), "--box", str(b2)).stdout


def test_a_bad_command_line_and_a_folder_that_is_no_box_are_refused(tmp_path):
    got = run(str(HERE / "said.py"))
    assert got.returncode == 2 and "said.py" in got.stderr
    got = run(str(HERE / "said.py"), "--box", str(tmp_path), "ana")
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    got = run(str(HERE / "said.py"), "--box", str(tmp_path), "ana", "gerry")
    assert got.returncode == 2 and "said.py" in got.stderr, "WHO is one argument"


def test_a_sentence_opening_with_a_common_word_names_no_speaker():
    for line in (
        "If I said it once, I said it twice.",
        "He said the plant was big.",
        "Someone said the plant was big.",
    ):
        assert sd.spoken(line) is None, line
