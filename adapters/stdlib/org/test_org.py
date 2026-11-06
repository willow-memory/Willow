"""org: an Org-mode file as plain lines, line for line: headlines, timestamps,
drawers, keywords, blocks, links, emphasis, checkboxes and tables in words;
hidden files and folders skipped, an unreadable file skipped and counted, the
same bytes twice, originals unchanged, and MIRROR and FOLDER kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
from collections import Counter
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "org.py"
spec = importlib.util.spec_from_file_location("org", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

AGENDA = """#+TITLE: Agenda
#+AUTHOR: Ada Example
#+STARTUP: overview
#+TODO: TODO NEXT(n) WAITING(w@/!) | DONE(d!) CANCELLED(c@)

* Home
** TODO [#A] Ring the vet about Biscuit's booster              :pets:phone:
SCHEDULED: <2024-03-05 Tue 09:00>
:PROPERTIES:
:CREATED:  [2024-03-01 Fri 18:22]
:LAST_REPEAT: [2024-02-29 Thu 08:10]
:END:
** NEXT Renew the car insurance                                       :car:
DEADLINE: <2024-03-28 Thu -7d>
Policy number is in [[file:~/docs/insurance.pdf][the insurance pdf]]. Call /before/ the 20th.
** DONE Pay the council tax
CLOSED: [2024-03-02 Sat 10:12] SCHEDULED: <2024-03-01 Fri>
:LOGBOOK:
- State "DONE"       from "TODO"       [2024-03-02 Sat 10:12]
:END:
** TODO Put the bins out
SCHEDULED: <2024-03-06 Wed 19:00 +1w>
* Work
** TODO Quarterly report [1/3]                                     :work:
- [X] Pull the numbers from the ledger
- [ ] Draft the summary
:LOGBOOK:
CLOCK: [2024-03-04 Mon 10:00]--[2024-03-04 Mon 11:30] =>  1:30
:END:
** Conference in Lisbon
<2024-05-13 Mon>--<2024-05-15 Wed>
"""

GARDEN = """#+TITLE: Allotment
* Seed sowing
| Plant       | Sown       | Bed | Notes   |
|-------------+------------+-----+---------|
| Tomato      | 2024-02-10 |   2 | indoors |
| Runner bean | 2024-04-20 |   3 |         |
#+TBLFM: @4$3=vsum(@2..@3)
* Watering script
#+BEGIN_SRC sh
# run the pump for *ten* minutes
gpio write 7 1
#+END_SRC
#+BEGIN_QUOTE
Plots must be /cultivated/ by April.
#+END_QUOTE
#+BEGIN_COMMENT
Ask Joe about half plots.
#+END_COMMENT
# my own note
- Rent :: 45 pounds a year
"""


JOURNAL = """#+TITLE: Journal
* 2024
** 2024-03 March
*** 2024-03-02 Saturday
**** Planted the tomatoes out                                    :garden:
[2024-03-02 Sat 15:40]
Six plants in bed 2. The soil was still cold.
*** 2024-03-03 Sunday
**** Lunch with Mum
[2024-03-03 Sun 13:10]
She wants the recipe for the *lemon drizzle* cake.
**** Fixed the gate latch
[2024-03-03 Sun 17:02]
Needed a 6mm bolt.
"""


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def mirror_of(
    tmp_path: Path, files: dict[str, bytes]
) -> tuple[subprocess.CompletedProcess, Path]:
    src = tmp_path / "src"
    for rel, data in files.items():
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_bytes(data)
    out = tmp_path / "out"
    return run("mirror", "--from", str(src), "--to", str(out)), out


def org(text: str) -> list[str]:
    return mod.convert(text.encode()).split("\n")


def line_of(text: str, source_line: str) -> str:
    """The mirror's line for a line of the source: the same number."""
    return org(text)[text.split("\n").index(source_line)]


def test_each_mirror_line_is_the_sources_line_so_a_passage_is_cited_by_its_own_line():
    out, src = org(AGENDA), AGENDA.split("\n")
    assert len(out) == len(src) and out[-1] == ""
    assert out[src.index("** Conference in Lisbon")] == "Conference in Lisbon"


def test_a_headline_keeps_its_keyword_priority_cookie_and_tags_as_written():
    assert line_of(AGENDA, AGENDA.split("\n")[6]) == (
        "Home › TODO [#A] Ring the vet about Biscuit's booster :pets:phone:"
    ), "the heading above said once, on the first headline under it"
    assert line_of(AGENDA, AGENDA.split("\n")[12]) == (
        "NEXT Renew the car insurance :car:"
    )
    assert line_of(AGENDA, "** DONE Pay the council tax") == "DONE Pay the council tax"
    assert line_of(AGENDA, AGENDA.split("\n")[23]) == (
        "Work › TODO Quarterly report [1/3] :work:"
    )
    assert org("* /Read/ [[https://x.org][the post]] :a:b:\n")[0] == (
        "Read the post :a:b:"
    )


def test_a_heading_with_only_headings_under_it_is_said_once_so_passages_split():
    out = org(
        "* Garden\n** Tomatoes\n*** Water them\nEvery day.\n** Beans\n* Next :t:\n** Kid\n"
    )
    assert out[:8] == [
        "",
        "",
        "Garden › Tomatoes › Water them",
        "Every day.",
        "Beans",
        "",
        "Next :t: › Kid",
        "",
    ]
    out = org(JOURNAL)
    assert out[4] == (
        "2024 › 2024-03 March › 2024-03-02 Saturday › Planted the tomatoes out :garden:"
    )
    assert out[7] == "" and out[8] == "2024-03-03 Sunday › Lunch with Mum"


def test_timestamps_lose_their_brackets_and_day_and_keep_their_repeaters_as_written():
    assert line_of(AGENDA, "SCHEDULED: <2024-03-05 Tue 09:00>") == (
        "SCHEDULED: 2024-03-05 09:00"
    )
    assert line_of(AGENDA, "DEADLINE: <2024-03-28 Thu -7d>") == (
        "DEADLINE: 2024-03-28 -7d"
    )
    assert line_of(AGENDA, "SCHEDULED: <2024-03-06 Wed 19:00 +1w>") == (
        "SCHEDULED: 2024-03-06 19:00 +1w"
    )
    assert line_of(
        AGENDA, "CLOSED: [2024-03-02 Sat 10:12] SCHEDULED: <2024-03-01 Fri>"
    ) == ("CLOSED: 2024-03-02 10:12 SCHEDULED: 2024-03-01")
    assert line_of(AGENDA, "<2024-05-13 Mon>--<2024-05-15 Wed>") == (
        "2024-05-13 to 2024-05-15"
    )
    got = mod.inline(
        "<2024-03-03 dim. 10:00-11:30 +2w> <2024-03-03 Sun ++1m -1d> "
        "<2024-03-03 Sun .+1d/3d> <2024-03-03 Sun 10:00>--<2024-03-03 Sun 12:00 +1d>"
    )
    assert got == (
        "2024-03-03 10:00 to 11:30 +2w 2024-03-03 ++1m -1d "
        "2024-03-03 .+1d/3d 2024-03-03 10:00 to 12:00 +1d"
    )
    assert mod.inline("<%%(diary-anniversary 3 3 1990)>") == (
        "<%%(diary-anniversary 3 3 1990)>"
    ), "a diary expression is not a date, and is left as written"


def test_the_kernel_dates_each_task_by_its_own_timestamp_not_the_files_latest(
    tmp_path,
):
    for name, text in (("raw", AGENDA), ("mirror", mod.convert(AGENDA.encode()))):
        (tmp_path / name).mkdir()
        (tmp_path / name / "todo.org").write_text(text, encoding="utf-8")
    for name, want in (("raw", 20240328), ("mirror", 20240305)):
        pile = kernel.chunks(tmp_path / name)
        got = kernel.rank(pile, "when is the vet appointment")
        assert len(got) == 1
        dated = dict(zip((c["id"] for c in pile), kernel.dates(pile)))
        assert dated[got[0]["id"]] == want, name
    assert "SCHEDULED: 2024-03-05 09:00" in got[0]["text"]
    assert "insurance" not in got[0]["text"]


def pile_of(tmp_path: Path, mirrored: bool) -> list[dict]:
    folder = tmp_path / ("mirror" if mirrored else "raw")
    folder.mkdir()
    for name, text in (
        ("todo.org", AGENDA),
        ("garden.org", GARDEN),
        ("journal.org", JOURNAL),
    ):
        (folder / name).write_text(
            mod.convert(text.encode()) if mirrored else text, encoding="utf-8"
        )
    return kernel.chunks(folder)


def in_most(pile: list[dict]) -> set[str]:
    """Words, not dates' digits, in most passages of a file of the pile."""
    out: set[str] = set()
    for path in {c["path"] for c in pile}:
        mine = [
            set(kernel.words(c["text"])) - kernel.FUNCTION
            for c in pile
            if c["path"] == path
        ]
        counts = Counter(w for ws in mine for w in ws if not w.isdigit())
        out |= {w for w, n in counts.items() if n * 2 > len(mine)}
    return out


def test_no_word_in_most_passages_answers_a_question_about_something_absent(tmp_path):
    """A word written into passage after passage is half of a two-word
    question: "volcano" is in no file, and nothing may answer it."""
    raw = in_most(pile_of(tmp_path, False))
    markup = {"end", "todo"}  # a drawer's end, a keyword the raw file repeats
    assert markup <= raw, "the raw files repeat Org's markup"
    pile = pile_of(tmp_path, True)
    assert in_most(pile) == set()
    for word in ("end",):
        assert kernel.rank(pile, f"volcano {word}") == [], word
    for question, holds in (
        ("when is the vet appointment", "SCHEDULED: 2024-03-05 09:00"),
        ("when did I pay the council tax", "CLOSED: 2024-03-02 10:12"),
        (
            "how long did I spend on the quarterly report",
            "Work › TODO Quarterly report",
        ),
        ("what did mum want", "lemon drizzle cake"),
        (
            "which bed is the runner bean in",
            "Plant; Sown; Bed; Notes\nTomato; 2024-02-10; 2; indoors\nRunner bean; 2024-04-20; 3",
        ),
        ("when did I plant the tomatoes", "Planted the tomatoes"),
    ):
        got = kernel.rank(pile, question)
        assert any(holds in c["text"] for c in got), question


def test_the_mirror_adds_no_word_the_source_does_not_hold():
    for text in (AGENDA, GARDEN, JOURNAL):
        added = set(kernel.words(mod.convert(text.encode()))) - kernel.FUNCTION
        assert added <= set(kernel.words(text)), added - set(kernel.words(text))


def test_drawers_keep_their_lines_as_written_with_their_markers_blank():
    assert line_of(AGENDA, ":PROPERTIES:") == ""
    assert line_of(AGENDA, ":LOGBOOK:") == ""
    assert line_of(AGENDA, ":CREATED:  [2024-03-01 Fri 18:22]") == (
        "CREATED: 2024-03-01 18:22"
    )
    assert line_of(AGENDA, ":LAST_REPEAT: [2024-02-29 Thu 08:10]") == (
        "LAST_REPEAT: 2024-02-29 08:10"
    )
    assert line_of(
        AGENDA, "CLOCK: [2024-03-04 Mon 10:00]--[2024-03-04 Mon 11:30] =>  1:30"
    ) == ("CLOCK: 2024-03-04 10:00 to 11:30 => 1:30")
    assert line_of(
        AGENDA, '- State "DONE"       from "TODO"       [2024-03-02 Sat 10:12]'
    ) == ('- State "DONE" from "TODO" 2024-03-02 10:12')
    out = org(
        ":PROPERTIES:\n:ID:\n:Effort+: 1:00\n:id: 6b3c-41\n:CUSTOM_ID: lunch\n:END:\n"
        ":NOTES:\nKeep [[x][this]]\n:END:\n"
    )
    assert out[:9] == ["", "", "Effort: 1:00", "", "", "", "", "Keep this", ""], (
        "an ID or CUSTOM_ID is a link's target, not something said"
    )
    out = org(":PROPERTIES:\nset by hand\n:END:\n:NOTES:\n:not: a property\n:END:\n")
    assert out[:6] == ["", "set by hand", "", "", ":not: a property", ""], (
        "a stray line in a property drawer, and any line of another drawer, as written"
    )
    out = org(
        "text\n:END:\n* H\nCLOCK: [2024-03-03 Sun 10:00]--[2024-03-04 Mon 01:00] =>  15:00\n"
    )
    assert out[1] == ":END:" and out[3] == (
        "CLOCK: 2024-03-03 10:00 to 2024-03-04 01:00 => 15:00"
    )


def test_keywords_comments_and_blocks():
    out, src = org(GARDEN), GARDEN.split("\n")
    assert out[0] == "title: Allotment"
    for blank in ("#+TBLFM: @4$3=vsum(@2..@3)", "#+BEGIN_SRC sh", "#+END_SRC",
                  "#+BEGIN_QUOTE", "#+BEGIN_COMMENT", "Ask Joe about half plots.",
                  "# my own note"):  # fmt: skip
        assert out[src.index(blank)] == "", blank
    assert out[src.index("# run the pump for *ten* minutes")] == (
        "# run the pump for *ten* minutes"
    ), "source is kept as written"
    assert out[src.index("Plots must be /cultivated/ by April.")] == (
        "Plots must be cultivated by April."
    )
    assert out[src.index("- Rent :: 45 pounds a year")] == "- Rent: 45 pounds a year"
    out = org(
        "#+SUBTITLE: Notes\n#+DATE: 2024-03-03\n#+FILETAGS: :a:b:\n#+OPTIONS: toc:nil\n"
        "#+begin_example\n  *kept*\n#+end_example\n: fixed /width/\n#\n"
        "#+BEGIN: clocktable\n#+END:\n#+begin_export html\n<b>x</b>\n#+end_export\n"
        "#+begin_html\n<!-- y -->\n#+end_html\n#+BEGIN_LATEX\n\\newpage\n#+END_LATEX\n"
    )
    assert out == ["subtitle: Notes", "date: 2024-03-03", "filetags: :a:b:", "", "",
                   "  *kept*", "", "fixed /width/", ""], "the blank lines at the end trimmed"  # fmt: skip


def test_links_footnotes_and_targets_become_their_words():
    assert mod.inline(
        "[[https://example.org/a_b_][the site]] or [[file:notes.org]]"
    ) == ("the site or notes.org")
    assert mod.inline("[[*Garden]] [[#ref]] <https://ex.org/p/q/>") == (
        "Garden ref https://ex.org/p/q/"
    )
    assert mod.inline("note[fn:1] and [fn::inline note] <<here>> <<<radio>>>") == (
        "note[1] and (inline note) here radio"
    )
    assert mod.inline("A line break \\\\") == "A line break"
    assert org("[[file:ADDONS.md][See\n  every add-on.]] Then [[x]]\n") == [
        "See",
        "  every add-on. Then x",
        "",
    ], "a description over two lines, as pandoc wraps one"
    assert mod.inline("[[file:LICENSE][[[https://img.example/badge.svg]]]]") == (
        "https://img.example/badge.svg"
    ), "an image for a description, as pandoc writes a badge"
    assert mod.inline("  - spaced     out") == "  - spaced out", "indent kept"


def test_emphasis_is_taken_off_only_where_org_reads_it_as_markup():
    assert mod.inline(
        '*bold* /italic/ _under_ =ver*b*at= ~co_de~ +strike+, (*b*) "/q/"'
    ) == ('bold italic under ver*b*at co_de strike, (b) "q"')
    kept = (
        "see /usr/bin and /usr/local/bin/ and snake_case_name, 2+2+3 C++ and C++ "
        "x*y* end* https://ex.org/_a_/ [[https://ex.org/x/_y_/]]"
    )
    assert mod.inline(kept) == kept.replace("[[", "").replace("]]", "")


def test_checkboxes_are_kept_as_written():
    assert line_of(AGENDA, "- [X] Pull the numbers from the ledger") == (
        "- [X] Pull the numbers from the ledger"
    )
    assert line_of(AGENDA, "- [ ] Draft the summary") == "- [ ] Draft the summary"
    assert org("  + [-] Half\n1. [x] *One*\n")[:2] == ["  + [-] Half", "1. [x] One"]


def test_a_table_row_is_its_cells_and_the_header_begins_the_passage_of_its_rows():
    out, src = org(GARDEN), GARDEN.split("\n")
    assert out[src.index("| Plant       | Sown       | Bed | Notes   |")] == ""
    assert out[src.index("|-------------+------------+-----+---------|")] == (
        "Plant; Sown; Bed; Notes"
    ), "the header moved down onto the rule under it, not repeated on each row"
    assert out[src.index("| Tomato      | 2024-02-10 |   2 | indoors |")] == (
        "Tomato; 2024-02-10; 2; indoors"
    )
    assert out[src.index("| Runner bean | 2024-04-20 |   3 |         |")] == (
        "Runner bean; 2024-04-20; 3"
    ), "an empty cell is left out"
    assert out[src.index("#+TBLFM: @4$3=vsum(@2..@3)")] == ""
    out = org("| a | b |\n| 1 | 2 |\n\n| h | |\n|---|\n| x |  |\n|---|\n| | y | z |\n")
    assert out[:8] == ["a; b", "1; 2", "", "", "h", "x", "", "y; z"], (
        "no rule under the first row, no header; a later rule is blank"
    )


def test_a_long_table_says_its_header_once_so_it_answers_nothing_absent(tmp_path):
    rows = "".join(
        f"| Plant{i} | 2024-03-{i % 28 + 1:02d} | {i % 5} |\n" for i in range(60)
    )
    text = "* Sowing\n| Plant | Sown | Bed |\n|---+---+---|\n" + rows
    (tmp_path / "a.org.txt").write_text(mod.convert(text.encode()), encoding="utf-8")
    pile = kernel.chunks(tmp_path)
    assert len(pile) > 3
    for label in ("plant", "sown", "bed"):
        assert len(kernel.rank(pile, f"volcano {label}")) == 1, label
    got = kernel.rank(pile, "when was plant42 sown")
    assert got and "Plant42; 2024-03-15; 2" in got[0]["text"]


def test_a_file_with_nothing_to_say_is_not_a_result():
    assert (
        mod.convert(b"#+STARTUP: overview\n# a comment\n:PROPERTIES:\n:END:\n") is None
    )
    assert mod.convert(b"\xef\xbb\xbf* Notes\r\nA line\r\n") == "Notes\nA line\n"


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {"notes/todo.org": AGENDA.encode(), "old.org_archive": b"* Gone\n",
         "notes.md": b"# not org\n"},
    )  # fmt: skip
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip().endswith("; skipped 0")
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == [".places/notes/todo.org.txt.json", ".places/old.org_archive.txt.json",
          "notes/todo.org.txt", "old.org_archive.txt"]  # fmt: skip


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {"a.org": b"* A\n", ".hidden/b.org": b"* B\n", ".c.org": b"* C\n"},
    )
    assert "wrote 1 files" in got.stdout
    assert sorted(p.name for p in out.rglob("*") if p.is_file()) == [
        "a.org.txt",
        "a.org.txt.json",
    ]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"todo.org": AGENDA.encode()})
    before = (tmp_path / "src" / "todo.org").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "todo.org.txt").read_bytes() == (out / "todo.org.txt").read_bytes()
    assert (tmp_path / "src" / "todo.org").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {"good.org": AGENDA.encode(), "bad.org": b"\xff\xfe not utf8",
         "empty.org": b"# nothing\n"},
    )  # fmt: skip
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 2" in got.stdout
    assert (out / "good.org.txt").is_file() and not (out / "bad.org.txt").exists()


def test_a_folder_with_nothing_to_read_waits_on_you(tmp_path):
    got, _ = mirror_of(tmp_path, {"notes.md": b"nothing here\n"})
    assert got.returncode == 42 and "wrote 0 files" in got.stdout


def test_a_mirror_inside_the_folder_or_the_folder_inside_it_is_refused(tmp_path):
    (tmp_path / "src").mkdir()
    for to in (tmp_path / "src" / "m", tmp_path):
        got = run("mirror", "--from", str(tmp_path / "src"), "--to", str(to))
        assert got.returncode == 2 and got.stderr.startswith("refused")
    got = run(
        "mirror", "--from", str(tmp_path / "missing"), "--to", str(tmp_path / "m")
    )
    assert got.returncode == 2 and got.stderr.startswith("refused: not a folder")


def test_a_bad_command_line_says_how_to_run_it():
    for argv in (
        [],
        ["mirror"],
        ["mirror", "--from", "a"],
        ["nope", "--from", "a", "--to", "b"],
        ["mirror", "--from", "a", "--into", "b"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "org.py" in got.stderr
