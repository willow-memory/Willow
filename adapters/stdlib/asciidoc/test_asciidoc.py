"""asciidoc: an AsciiDoc document as the text it shows, line for line; PGP armor
in an .asc file passed over, hidden files and folders skipped, an unreadable
file skipped and counted, the same bytes twice, originals unchanged, and MIRROR
and FOLDER kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "asciidoc.py"
spec = importlib.util.spec_from_file_location("asciidoc", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
kernel = sys.modules["kernel"]

SAMPLE = b"""= Tides of the Estuary
Ada Example <ada@example.org>
v1.2, 2024-03-03: First survey
:revdate: 2024-03-03
:toc: left
:harbour: Leeds

// a comment line
== Method

We measure the tide at {harbour} with *six* gauges.footnote:[Calibrated in March.]
See link:https://tides.example.org/data[the data] and <<results,the results>>.

NOTE: The gauge at Hull was broken.

[source,python]
----
def tide(x):
    return *x*  # not bold
----

.Gauge readings
|===
| Harbour | Gauges | Read
| Leeds | 6 | 2024-03-03
|===
include::chapter1.adoc[]
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


def adoc(body: str) -> list[str]:
    return mod.convert(body.encode()).split("\n")


def test_the_mirror_has_the_sources_lines_so_a_passage_is_cited_by_its_own_line():
    src = SAMPLE.decode().split("\n")
    out = mod.convert(SAMPLE).split("\n")
    assert len(out) <= len(src), "never more lines than the source"
    want = {
        "= Tides of the Estuary": "Tides of the Estuary",
        "== Method": "Method",
        "NOTE: The gauge at Hull was broken.": "note: The gauge at Hull was broken.",
        "    return *x*  # not bold": "    return *x*  # not bold",
        ".Gauge readings": "Gauge readings",
        "| Leeds | 6 | 2024-03-03": "Leeds; 6; 2024-03-03",
        "include::chapter1.adoc[]": "",
        "// a comment line": "",
        "----": "",
    }
    out += [""] * (len(src) - len(out))  # the blank lines at the end are dropped
    for line, mirrored in want.items():
        assert out[src.index(line)] == mirrored, line
    at = next(i for i, x in enumerate(src) if x.startswith("We measure"))
    assert (
        out[at]
        == "We measure the tide at Leeds with six gauges. (Calibrated in March.)"
    )
    assert (
        out[at + 1] == "See the data (https://tides.example.org/data) and the results."
    )


def test_the_header_keeps_the_author_revision_and_the_documents_own_attributes():
    out = mod.convert(SAMPLE).split("\n")
    assert out[:6] == [
        "Tides of the Estuary",
        "Ada Example <ada@example.org>",
        "v1.2, 2024-03-03: First survey",
        "revdate: 2024-03-03",
        "",
        "",
    ]


def test_an_attribute_reference_is_its_value_when_set_and_as_written_when_not():
    out = adoc(
        "= Doc\nAda Example <ada@example.org>\nv2.0, 2025-01-02: Spring\n\n"
        ":boat: Heron\n:empty-one:\nOn {boat} by {author} ({email}), {revnumber} of {revdate}: {revremark}.\n"
        "{nobody} and {empty-one}x and a{nbsp}b.\n:boat!:\nNow {boat}.\n"
    )
    assert out[4:6] == ["", ""]
    assert (
        out[6]
        == "On Heron by Ada Example (ada@example.org), 2.0 of 2025-01-02: Spring."
    )
    assert out[7] == "{nobody} and x and a b."
    assert out[8:10] == ["", "Now {boat}."]
    assert adoc("= Doc\nAda\n2024-05-06\n\nOn {revdate}.\n")[4] == "On 2024-05-06."


def test_an_attribute_value_running_on_keeps_its_lines():
    out = adoc(":description: A survey of \\\nsix harbours.\n:other: a \\\nb\nText.\n")
    assert out == ["description: A survey of", "six harbours.", "", "", "Text.", ""]


def test_listing_literal_and_fenced_blocks_are_kept_as_written():
    out = adoc(
        "[source,python]\n----\nx = *a* + _b_\n----\n....\n  *lit*  {x}\n....\n"
        "```ruby\nputs `a`\n```\n[literal]\nkept *as* is\n\nback to *bold*\n"
    )
    assert out == [
        "", "", "x = *a* + _b_", "", "", "  *lit*  {x}", "", "", "puts `a`", "",
        "", "kept *as* is", "", "back to bold", "",
    ]  # fmt: skip


def test_an_indented_paragraph_is_literal_but_an_indented_list_item_is_not():
    out = adoc("Text\n\n  $ rbenv *install*\n  next\n\n  * item *one*\n")
    assert out == ["Text", "", "  $ rbenv *install*", "  next", "", "- item one", ""]


def test_comments_are_blank_with_their_lines_kept():
    assert adoc("a\n// gone\n////\nhidden\nalso\n////\nb\n") == [
        "a", "", "", "", "", "", "b", "",
    ]  # fmt: skip


def test_example_sidebar_quote_and_open_blocks_keep_their_text():
    out = adoc(
        "====\nan *example*\n====\n****\na sidebar\n****\n"
        '[quote, Abraham Lincoln, "Gettysburg, Address"]\n____\nFour score\n____\n--\nopen\n--\nend\n'
    )
    assert out == [
        "", "an example", "", "", "a sidebar", "",
        "— Abraham Lincoln, Gettysburg, Address", "", "Four score", "", "", "open", "", "end", "",
    ]  # fmt: skip


def test_admonitions_paragraph_and_block():
    out = adoc(
        "TIP: Bring rope.\n\n[WARNING]\nDo not swim.\n\n[CAUTION]\n====\n\nThe pier is closed.\n====\nend\n"
    )
    assert out == [
        "tip: Bring rope.", "", "", "warning: Do not swim.", "", "", "", "",
        "caution: The pier is closed.", "", "end", "",
    ]  # fmt: skip


def test_bold_italic_monospace_and_highlight_lose_their_marks_but_never_inside_a_word():
    out = adoc(
        "*bold* _it_ `mono` #mark# **un**constrained __it__alic ``co``de ##hi##gh\n"
        "snake_case_name and 2*3*4 and a_b_ stay; `a_b` and `*args` are code\n"
        "*_both_* and [.underline]#role# and ^sup^ and ~sub~ and ~/.rbenv stays\n"
    )
    assert out[0] == "bold it mono mark unconstrained italic code high"
    assert out[1] == "snake_case_name and 2*3*4 and a_b_ stay; a_b and *args are code"
    assert out[2] == "both and role and sup and sub and ~/.rbenv stays"


def test_escapes_passthroughs_quotes_and_replacements():
    out = adoc(
        "\\*not bold* and +++<b>raw *x*</b>+++ and pass:[*p*] and `+*lit*+` and +*plus*+\n"
        "\"`curly`\" and '`single`' (C) (R) (TM) a--b x -- y &amp; &#169; C++ and C++ go\n"
        "a hard break +\n"
    )
    assert out[0] == "*not bold* and <b>raw *x*</b> and *p* and *lit* and *plus*"
    assert out[1] == "“curly” and ‘single’ © ® ™ a—b x — y & © C++ and C++ go"
    assert out[2] == "a hard break"


def test_links_are_their_text_with_an_outside_address_after_it():
    out = adoc(
        "link:https://x.org/a_b_c[the site] and https://y.org/p_q[Y, window=_blank] and "
        "https://z.org[] and https://w.org/raw_path here\n"
        "link:notes/plan.adoc[the plan] and link:other.adoc[] and mailto:ada@example.org[Ada] "
        'and mailto:cy@example.org[] and link:https://v.org["a, b",role=x] and <https://u.org>\n'
    )
    assert out[0] == (
        "the site (https://x.org/a_b_c) and Y (https://y.org/p_q) and "
        "https://z.org and https://w.org/raw_path here"
    )
    assert out[1] == (
        "the plan and other.adoc and Ada (ada@example.org) and cy@example.org "
        "and a, b (https://v.org) and https://u.org"
    )


def test_cross_references_images_footnotes_keys_menus_anchors_and_index_terms():
    out = adoc(
        "<<setup,the setup>> and <<setup>> and xref:a.adoc#b[the B part] and xref:c.adoc[]\n"
        "image:boat.png[A heron, 40] then word.footnote:[A note.] and footnote:fn1[] end\n"
        "kbd:[Ctrl+C] btn:[Save] menu:File[Save > Quit] [[here]]anchor:x[] ((tides)) (((hidden, x))) "
        "indexterm:[gone] indexterm2:[shown] stem:[x_1^2]\n"
        "image::harbour.png[The harbour at dawn, 300]\ntoc::[]\nvideo::v.mp4[]\nend\n"
    )
    assert out[0] == "the setup and setup and the B part and c.adoc"
    assert out[1] == "A heron then word. (A note.) and end"
    assert out[2] == "Ctrl+C Save File > Save > Quit tides shown x_1^2"
    assert out[3:7] == ["The harbour at dawn", "", "", "end"]


def test_a_macro_or_a_bold_running_onto_the_next_line_is_read_line_by_line():
    out = adoc(
        "keeps the link:CODE.md[code of\nconduct]. And https://x.org/a_b[the long\nname] here.\n"
        "Word.footnote:[a note\nthat runs on] next.\n"
        "link:ci.yml[image:https://img/badge[Python\n3.9 to 3.14]] after\n"
        "*Ask your own\nfiles.* And _lean\nin_.\n"
    )
    assert out[:9] == [
        "keeps the code of",
        "conduct. And the long",
        "name (https://x.org/a_b) here.",
        "Word. (a note",
        "that runs on) next.",
        "Python",
        "3.9 to 3.14 after",
        "Ask your own",
        "files. And lean",
    ]
    assert out[9] == "in."


def test_an_unclosed_mark_with_nothing_to_close_it_stays():
    assert adoc("a *star\nand more\n\nnext* para\n")[:4] == [
        "a *star", "and more", "", "next* para",
    ]  # fmt: skip


def test_lists_checklists_and_descriptions():
    out = adoc(
        "* first\n** nested *item*\n- dash\n. ordered\n.. deeper\n3. numbered\n"
        "* [ ] buy rope\n* [x] fix the boat\n+\nGauge:: a tool\n*Pier* (old)::\nTerm;; semi\n"
        "std::vector stays\n"
    )
    assert out == [
        "- first", "- nested item", "- dash", "- ordered", "- deeper", "3. numbered",
        "- [ ] buy rope", "- [x] fix the boat", "", "Gauge: a tool", "Pier (old):",
        "Term: semi", "std::vector stays", "",
    ]  # fmt: skip


def test_titles_of_every_kind_keep_their_text():
    out = adoc(
        "== Section ==\n=== Sub _part_\n# Markdown style\n.Block *title*\n. an item\n"
    )
    assert out == [
        "Section",
        "Sub part",
        "Markdown style",
        "Block title",
        "- an item",
        "",
    ]


def test_a_tables_rows_are_their_cells_and_the_header_row_is_kept_once():
    out = adoc(
        '[cols="1,2",options="header"]\n|===\n|Name |Role\n\n|Ada\n|Surveyor\n\n'
        "|Cy\n|Driver who\nalso cooks\n\n2+|Both *spanned* | x \\| y\n|===\nafter\n"
    )
    assert out == [
        "", "", "Name; Role", "", "Ada", "Surveyor", "", "Cy", "Driver who",
        "also cooks", "", "Both spanned; x | y", "", "after", "",
    ]  # fmt: skip


def test_csv_and_dsv_tables():
    out = adoc(
        ',===\nHarbour,Gauges\nLeeds,"6, new"\n,===\n:===\nHull:2\\:3\n:===\n'
        "[format=csv,separator=;]\n|===\nYork;9\n|===\nend\n"
    )
    assert out == [
        "", "Harbour; Gauges", "Leeds; 6, new", "", "", "Hull; 2:3", "", "", "", "York; 9", "", "end", "",
    ]  # fmt: skip
    assert adoc("|===\n|a |b\n")[:2] == ["", "a; b"], "an unclosed table is still read"


def test_directives_and_breaks_are_blank():
    out = adoc(
        "ifdef::x[]\nkept\nendif::[]\n<<<\n'''\ninclude::secret.adoc[lines=1..3]\nend\n"
    )
    assert out == ["", "kept", "", "", "", "", "end", ""]


def test_a_file_with_no_text_is_not_a_result():
    assert mod.convert(b":toc:\n// only a comment\n") is None
    assert mod.convert(b"") is None


# ── a question lands on its passage, and nothing the folder lacks is answered ──

LOG = b"""= Boat log
Ada Example
:revdate: 2024-03-03

== Crew

|===
|Name |Role |Boat

|Ada
|Surveyor
|Heron

|Cy
|Driver
|Kestrel

|Dee
|Pilot
|Osprey
|===

NOTE: The *Kestrel* engine needs oil.

[WARNING]
The pier at Hull is closed.

Mooring:: Berth 14 at the north quay
Fuel:: Diesel from the harbour office

* [ ] buy rope
* [x] fix the bilge pump
"""


def passages(tmp_path: Path, data: bytes) -> list[dict]:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "log.txt").write_bytes(mod.convert(data).encode())
    return kernel.chunks(pile)


def served(pile: list[dict], question: str) -> list[str]:
    return [c["text"] for c in kernel.rank(pile, question)]


def test_no_word_the_reader_adds_is_in_most_passages_so_an_absent_question_finds_nothing(
    tmp_path,
):
    pile = passages(tmp_path, LOG)
    assert len(pile) >= 8
    counts: dict[str, int] = {}
    for c in pile:
        for w in set(kernel.words(c["text"])) - kernel.FUNCTION:
            counts[w] = counts.get(w, 0) + 1
    common = sorted(w for w, n in counts.items() if n > len(pile) / 2)
    assert common == [], common
    # a header written onto every row would be such a word: it is on its own row once
    for word in ("role", "boat", "name", "note", "warning", "done"):
        got = served(pile, f"volcano {word}")
        rows = ("Surveyor", "Driver", "Pilot")
        assert not [t for t in got if any(r in t for r in rows)], word
    assert served(pile, "volcano done") == [] and served(pile, "marathon todo") == []


def test_a_persons_questions_land_on_the_passage_that_answers_them(tmp_path):
    pile = passages(tmp_path, LOG)
    assert served(pile, "what boat is Cy on")[0] == "Cy\nDriver\nKestrel"
    assert served(pile, "who is the pilot")[0] == "Dee\nPilot\nOsprey"
    assert (
        served(pile, "Kestrel engine oil")[0] == "note: The Kestrel engine needs oil."
    )
    assert served(pile, "where is the mooring berth")[0].startswith("Mooring: Berth 14")
    assert (
        served(pile, "is the pier at Hull closed")[0]
        == "warning: The pier at Hull is closed."
    )
    assert "fix the bilge pump" in served(pile, "bilge pump")[0]


# ── the mirror on disk ──────────────────────────────────────────────────────


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {"docs/guide.adoc": SAMPLE, "docs/b.ASCIIDOC": SAMPLE, "c.asc": SAMPLE},
    )
    assert got.returncode == 0, got.stderr
    assert sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()) == [
        "c.asc.txt", "docs/b.ASCIIDOC.txt", "docs/guide.adoc.txt",
    ]  # fmt: skip
    assert got.stdout.strip().endswith("wrote 3 files to " + str(out) + "; skipped 0")
    assert (out / "docs/guide.adoc.txt").read_bytes() == mod.convert(SAMPLE).encode()


def test_an_asc_file_that_is_pgp_armor_is_passed_over_without_being_counted(tmp_path):
    key = b"-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nmQENBF...\n-----END PGP PUBLIC KEY BLOCK-----\n"
    sig = b"\xef\xbb\xbf\n  -----BEGIN PGP SIGNATURE-----\n\niQEz\n-----END PGP SIGNATURE-----\n"
    got, out = mirror_of(
        tmp_path,
        {
            "key.asc": key,
            "release.tar.gz.ASC": sig,
            "notes.asc": SAMPLE,
            "key.adoc": key,
        },
    )
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip().endswith("wrote 2 files to " + str(out) + "; skipped 0")
    assert sorted(p.name for p in out.rglob("*") if p.is_file()) == [
        "key.adoc.txt", "notes.asc.txt",
    ]  # fmt: skip
    only_keys, _ = mirror_of(tmp_path / "k", {"key.asc": key})
    assert only_keys.returncode == 42 and "skipped 0" in only_keys.stdout


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {"doc.adoc": SAMPLE, ".hid/doc.adoc": SAMPLE, ".doc.adoc": SAMPLE},
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["doc.adoc.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"doc.adoc": SAMPLE})
    before = (tmp_path / "src" / "doc.adoc").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "doc.adoc.txt").read_bytes() == (out / "doc.adoc.txt").read_bytes()
    assert (tmp_path / "src" / "doc.adoc").read_bytes() == before
    assert sorted(p.name for p in (tmp_path / "src").iterdir()) == ["doc.adoc"]


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "good.adoc": SAMPLE,
            "bad.adoc": b"\xff\xfe not utf8",
            "empty.adoc": b"// x\n",
        },
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 2" in got.stdout
    assert (out / "good.adoc.txt").is_file() and not (out / "bad.adoc.txt").exists()


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
        assert got.returncode == 2 and "asciidoc.py mirror" in got.stderr
