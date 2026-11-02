"""markdown: a Markdown file as the text it shows, line for line; front matter as
its values, a table's rows named by their columns, no word the source lacks;
hidden files and folders skipped, an unreadable file
skipped and counted, the same bytes twice, originals unchanged, and MIRROR and
FOLDER kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "markdown.py"
spec = importlib.util.spec_from_file_location("markdown_addon", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

SAMPLE = (
    b"---\ndate: 2024-03-03\ntags: [study, aat]\n---\n# AAT Level 4\n\n"
    b"| unit | status | date | mark |\n|------|--------|------|------|\n"
    b"| DAIF | passed | 2023-12-15 | 74% |\n| APMA | passed | 2024-02-09 | 71% |\n"
    b"| BSTX | started | 2024-09 | |\n\n"
    b"## Next\n- [ ] book **BSTX** exam, see [the portal](https://aat.example/book)\n"
    b"- [x] pay the fee\n"
)


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


def md(body: str) -> list[str]:
    """The mirror's lines for a Markdown text."""
    return mod.convert(body.encode()).rstrip("\n").split("\n")


def test_the_mirror_has_the_sources_lines_so_a_passage_is_cited_by_its_own_line():
    src = SAMPLE.decode().rstrip("\n").split("\n")
    lines = md(SAMPLE.decode())
    assert len(lines) == len(src)
    assert lines == [
        "",
        "2024-03-03",
        "study, aat",
        "",
        "AAT Level 4",
        "",
        "",
        "",
        "unit: DAIF; status: passed; date: 2023-12-15; mark: 74%",
        "unit: APMA; status: passed; date: 2024-02-09; mark: 71%",
        "unit: BSTX; status: started; date: 2024-09",
        "",
        "Next",
        "- [ ] book BSTX exam, see the portal (https://aat.example/book)",
        "- [x] pay the fee",
    ]


def test_a_question_about_a_tables_row_is_answered_by_that_row_with_its_column_named(
    tmp_path,
):
    (tmp_path / "m").mkdir()
    (tmp_path / "m" / "progress.md.txt").write_text(mod.convert(SAMPLE))
    got = kernel.rank(kernel.chunks(tmp_path / "m"), "what mark did I get on APMA")
    assert (
        got
        and "unit: APMA; status: passed; date: 2024-02-09; mark: 71%"
        in (got[0]["text"])
    )


def test_front_matter_keeps_its_values_not_its_keys_and_its_fences_are_blank():
    assert md(
        "---\ntitle: \"Tomatoes\"\nrating: 4\nnested:\n  sub: 'x'\n---\nbody\n"
    ) == ["", "Tomatoes", "4", "", "x", "", "body"]


def test_a_list_under_a_key_is_joined_onto_its_line_only_when_it_runs_to_the_end():
    # running to the closing fence: joined, the item lines blank beside it
    assert md("---\ntitle: Seeds\ntags:\n  - garden\n  - seed bank\n---\nx\n") == [
        "",
        "Seeds",
        "garden, seed bank",
        "",
        "",
        "",
        "x",
    ]
    # a key after it: each item on its own line
    assert md("---\ntags:\n- garden\n- bees\ntitle: Seeds\n---\nx\n") == [
        "",
        "",
        "garden",
        "bees",
        "Seeds",
        "",
        "x",
    ]


def test_toml_front_matter_and_a_fence_that_never_closes():
    assert md('+++\ntitle = "Hives"\ntags = ["bees", "honey"]\n[extra]\n+++\nx\n') == [
        "",
        "Hives",
        "bees, honey",
        "extra",
        "",
        "x",
    ]
    assert md("---\nnot: front matter\n") == ["", "not: front matter"]


def test_atx_and_setext_headings_with_their_underlines_blank():
    assert md(
        "# Garden ##\n\nSetext one\n==========\n\nTwo\n---\n\n####### seven\n"
    ) == [
        "Garden",
        "",
        "Setext one",
        "",
        "",
        "Two",
        "",
        "",
        "####### seven",
    ]


def test_a_heading_is_only_its_own_words_never_the_headings_above_it():
    assert md("# Garden\n\n## Tomatoes\nSown 3 March.\n### Pests\nAphids.\n") == [
        "Garden",
        "",
        "Tomatoes",
        "Sown 3 March.",
        "Pests",
        "Aphids.",
    ]


def test_no_word_is_added_so_a_question_about_something_absent_finds_nothing(
    tmp_path,
):
    """The owner's rule: a word the reader writes into passage after passage
    answers a question about anything paired with it. Daily notes with front
    matter, tasks, headings and a footnote: nothing in the mirror is a word
    the source lacks, and a question pairing a repeated word with one the
    folder doesn't hold is served nothing."""
    (tmp_path / "m").mkdir()
    sources = {}
    for day in ("2024-03-01", "2024-03-02", "2024-03-03"):
        sources[day] = (
            f"---\ndate: {day}\ntags: [daily]\n---\n# Garden\n\n## Beds\n"
            "- [x] water the beans[^1]\n- [ ] sow tomatoes\n\n"
            "[^1]: Rain due.\n"
        )
        (tmp_path / "m" / f"{day}.md.txt").write_text(
            mod.convert(sources[day].encode())
        )
    pile = kernel.chunks(tmp_path / "m")
    for c in pile:
        day = c["path"][:10]
        assert set(kernel.words(c["text"])) <= set(kernel.words(sources[day]))
    for word in ("tags", "date", "done", "note"):
        assert kernel.rank(pile, f"volcano {word}") == [], word
    assert kernel.rank(pile, "when did I sow tomatoes")


def test_table_headers_are_the_one_label_kept_and_they_answer_as_the_raw_file_does(
    tmp_path,
):
    """A table's headers are the source's own labels, written on each row so
    a row answers for its columns. Measured by the owner's test: a question
    pairing a header with an absent word is served the table, by the raw file
    and the mirror alike; without them "what mark did I get on APMA" holds
    one word of three and finds nothing."""
    (tmp_path / "raw").mkdir()
    (tmp_path / "m").mkdir()
    (tmp_path / "raw" / "progress.md").write_bytes(SAMPLE)
    (tmp_path / "m" / "progress.md.txt").write_text(mod.convert(SAMPLE))
    raw, mirror = kernel.chunks(tmp_path / "raw"), kernel.chunks(tmp_path / "m")
    for q in ("volcano mark", "volcano status"):
        assert bool(kernel.rank(raw, q)) == bool(kernel.rank(mirror, q))
    unlabelled = [dict(c, text=c["text"].replace("mark: ", "")) for c in mirror]
    assert kernel.rank(unlabelled, "what mark did I get on APMA") == []


def test_table_cells_empty_escaped_extra_and_where_the_table_ends():
    assert md(
        "a | b\n--|:-:\n1 | x \\| y\n| | 2 |\n|5|6|7|\nafter\n\n| only | header |\n|---|---|\n"
    ) == [
        "",
        "",
        "a: 1; b: x | y",
        "b: 2",
        "a: 5; b: 6; 7",
        "after",
        "",
        "only; header",
    ]


def test_emphasis_is_taken_off_but_never_inside_a_word_or_a_sum():
    assert md(
        "**bold** __strong__ *em* _em_ ~~gone~~ snake_case_name 2*3*4 a * b\n"
    ) == ["bold strong em em gone snake_case_name 2*3*4 a * b"]


def test_bold_that_opens_on_one_line_and_closes_on_the_next():
    assert md("say **only what you\nwrote** and stop\n") == [
        "say only what you",
        "wrote and stop",
    ]


def test_code_spans_are_kept_as_written_and_fenced_code_verbatim():
    assert md(
        "use `a*b*c` and ``x ` y``\n```python\n  x = **kw  # [not](a link)\n```\n"
        "~~~~\n```\nstill code\n~~~~\nafter *em*\n"
    ) == [
        "use a*b*c and x ` y",
        "",
        "  x = **kw  # [not](a link)",
        "",
        "",
        "```",
        "still code",
        "",
        "after em",
    ]
    assert md("```\nnever closed *x*\n") == ["", "never closed *x*"]


def test_links_keep_an_outside_address_but_not_a_path_within_the_folder():
    assert md(
        'See [the shop](https://shop.example "Shop"), [notes](notes/a.md), '
        "[https://a.b](https://a.b) and <https://c.d/e> or <me@x.org>.\n"
    ) == [
        "See the shop (https://shop.example), notes, https://a.b and https://c.d/e or me@x.org."
    ]


def test_images_and_badges_are_their_alt_text():
    assert md(
        "![a cat](cat.png) [![CI](https://x/b.svg)](https://x/ci) [![Py](p.svg)](ci.yml)\n"
    ) == ["a cat CI (https://x/ci) Py"]


def test_reference_links_are_their_text_and_their_definitions_blank():
    assert md(
        "Use [the guide][g], [g], [Guide][] and ![a map][g]; [unknown] stays.\n\n"
        '[g]: https://guide.example "Guide"\n[guide]: <https://guide.example>\nend\n'
    ) == ["Use the guide, g, Guide and a map; [unknown] stays.", "", "", "", "end"]


def test_wikilinks_and_embeds_are_the_text_they_show():
    assert md(
        "[[Seed bank]] [[Gerry|my husband]] ![[plot.png]] [[Health#Gerry]]\n"
    ) == ["Seed bank my husband plot.png Health › Gerry"]


def test_html_tags_entities_and_comments():
    assert md(
        "<b>bold</b><br>next &amp; &lt;b&gt; &eacute;\n<!-- one -->kept\n"
        "a <!-- starts\nhidden *x*\nends --> after\n<div>\n"
    ) == ["bold next & <b> é", "kept", "a", "", "after"]


def test_quotes_lists_tasks_and_rules():
    assert md(
        "> > nested **quote**\n* star\n+ plus\n3) third\n12. twelfth\n"
        "    - [x] Netflix\n- [ ] Lakeside\n- [X] Origin\n***\n- - -\nend\n"
    ) == [
        "nested quote",
        "- star",
        "- plus",
        "3. third",
        "12. twelfth",
        "- [x] Netflix",
        "- [ ] Lakeside",
        "- [X] Origin",
        "",
        "",
        "end",
    ]


def test_footnotes_escapes_and_a_hard_break():
    assert md(
        "Text[^1] here.\\\nmore \\*not em\\* and \\[x\\] and C:\\\\dir\\\n[^1]: The note.\n"
    ) == ["Text here.", "more *not em* and [x] and C:\\dir", "1: The note."]


def test_a_file_with_no_text_is_not_a_result():
    assert mod.convert(b"") is None
    assert mod.convert(b"---\n---\n\n<!-- just a comment -->\n***\n") is None
    assert mod.convert(b"\xef\xbb\xbf# kept\r\n") == "kept\n"


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(
        tmp_path, {"study/progress.md": SAMPLE, "old/notes.MARKDOWN": b"# Old\n"}
    )
    assert got.returncode == 0, got.stderr
    assert (out / "study/progress.md.txt").read_bytes() == mod.convert(SAMPLE).encode()
    assert (out / "old/notes.MARKDOWN.txt").read_text() == "Old\n"
    assert got.stdout.strip().endswith("wrote 2 files to " + str(out) + "; skipped 0")


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "a/n.md": SAMPLE,
            ".obsidian/n.md": SAMPLE,
            "a/.n.md": SAMPLE,
            "a/n.txt": b"x",
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["a/n.md.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"n.md": SAMPLE})
    before = (tmp_path / "src" / "n.md").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "n.md.txt").read_bytes() == (out / "n.md.txt").read_bytes()
    assert (tmp_path / "src" / "n.md").read_bytes() == before
    assert sorted(p.name for p in (tmp_path / "src").iterdir()) == ["n.md"]


def test_a_file_it_cannot_read_or_with_no_text_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {"good.md": SAMPLE, "bad.md": b"\xff\xfe not utf8", "empty.md": b"---\n---\n"},
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and got.stdout.strip().endswith("skipped 2")
    assert (out / "good.md.txt").is_file() and not (out / "bad.md.txt").exists()
    assert not (out / "empty.md.txt").exists()


def test_a_folder_with_nothing_to_read_waits_on_you(tmp_path):
    got, _ = mirror_of(tmp_path, {"notes.txt": b"nothing here\n"})
    assert got.returncode == 42 and "wrote 0 files" in got.stdout


def test_a_mirror_inside_the_folder_or_the_folder_inside_it_is_refused(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "n.md").write_bytes(SAMPLE)
    for to in (tmp_path / "src" / "m", tmp_path, tmp_path / "src"):
        got = run("mirror", "--from", str(tmp_path / "src"), "--to", str(to))
        assert got.returncode == 2 and got.stderr.startswith("refused")
    assert not (tmp_path / "src" / "m").exists()
    got = run(
        "mirror", "--from", str(tmp_path / "missing"), "--to", str(tmp_path / "m")
    )
    assert got.returncode == 2 and "not a folder" in got.stderr


def test_a_bad_command_line_says_how_to_run_it():
    for argv in (
        [],
        ["mirror"],
        ["mirror", "--from", "a"],
        ["nope", "--from", "a", "--to", "b"],
        ["mirror", "--from", "a", "--from", "b"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "markdown.py mirror" in got.stderr
