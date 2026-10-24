"""clauses: one sentence a passage, from wrapped PDF text and web pages, and
what changed between two versions, sentence by sentence."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import clauses  # noqa: E402

SCRIPT = HERE / "clauses.py"

#: the pdf add-on's mirror: lines wrapped at the page's width, `== page N`
WRAPPED = """\
== page 1
PRIVACY POLICY
We collect information to provide better services to all our users, from
figuring out basic stuff like which language you speak, to more complex
things. We don't show you personalized ads based on your content from
Drive, Gmail, or Photos. Our services include
things like the U.S. Search app and e.g. maps. Mr. Example agrees.
Learn more about ads.
deliver our services
Examples of how we use your information to deliver our services, and a
sentence that runs right to the end of the page and keeps going without a

== page 2
Google noun that would look like a new start, so it goes on.
"""


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def test_wrapped_lines_become_one_sentence_a_paragraph():
    got = [s for _, s in clauses.clauses(WRAPPED, "policy.pdf.txt")]
    assert got == [
        "== page 1",
        "PRIVACY POLICY",  # a short line: a heading ends its block
        "We collect information to provide better services to all our users, from "
        "figuring out basic stuff like which language you speak, to more complex things.",
        "We don't show you personalized ads based on your content from Drive, Gmail, or Photos.",
        # a short line going on in lower case is the same sentence; U.S., e.g.
        # and Mr. are not its end
        "Our services include things like the U.S. Search app and e.g. maps.",
        "Mr. Example agrees.",
        "Learn more about ads.",  # a short line that ends a sentence ends it
        "deliver our services",
        "Examples of how we use your information to deliver our services, and a "
        "sentence that runs right to the end of the page and keeps going without a "
        "Google noun that would look like a new start, so it goes on.",
        "== page 2",  # kept after the sentence it broke
    ]


def test_each_sentence_says_the_line_its_block_starts_on():
    got = dict((s[:12], n) for n, s in clauses.clauses(WRAPPED, "p.txt"))
    assert (
        got["PRIVACY POLI"] == 2 and got["We collect i"] == 3 and got["== page 2"] == 13
    )
    assert got["We don't sho"] == 3  # the same block as the sentence before it


def test_plain_paragraphs_are_not_cut_at_short_lines():
    text = "A short\nline goes on.\n\nNext one? Yes! (Quoted.) “Opening” too.\n"
    assert [s for _, s in clauses.clauses(text, "notes.md")] == [
        "A short line goes on.", "Next one?", "Yes!", "(Quoted.)", "“Opening” too."]  # fmt: skip


def test_a_web_page_is_read_as_its_blocks_with_lines_kept():
    page = ("<html><head><title>Terms</title><script>var x = 1;\n</script></head>\n"
            "<body><h1>Ads</h1><p>We don&rsquo;t show ads. Ever,\nmostly.</p>"
            "<ul><li>One <b>bold</b> item</li></ul>\n<p>Last.</p></body></html>\n")  # fmt: skip
    got = clauses.clauses(page, "t.html")
    assert got == [(1, "Terms"), (3, "Ads"), (3, "We don’t show ads."),
                   (3, "Ever, mostly."), (4, "One bold item"), (5, "Last.")]  # fmt: skip


def test_compare_pairs_rewordings_and_counts_spacing_as_same():
    old = [(1, "Effective October 1, 2026"), (3, "We don't show ads from Gmail."),
           (5, "Gone  for good."), (7, "Unrelated words here entirely.")]  # fmt: skip
    new = [(1, "Effective October 16, 2026"), (2, "Gone for good!"),
           (4, "We don't show ads from Gmail, unless you choose."),
           (9, "A new promise.")]  # fmt: skip
    got = clauses.compare(old, new)
    assert got["same"] == 1 and got["spacing"] == 1
    assert [(o[0], a[0]) for o, a, _, _ in got["reworded"]] == [(1, 1), (3, 4)]
    assert got["reworded"][1][2:] == (
        7,
        10,
    )  # "don't" is two words, as the kernel splits
    assert got["added"] == [(9, "A new promise.")]
    assert got["removed"] == [(7, "Unrelated words here entirely.")]


def test_compare_takes_the_closest_pair_first():
    old = [(1, "alpha beta gamma delta")]
    new = [(2, "alpha beta gamma zeta"), (3, "alpha beta gamma delta epsilon")]
    got = clauses.compare(old, new)
    assert [a[0] for _, a, _, _ in got["reworded"]] == [3]  # 4 of 5 over 3 of 5
    assert got["added"] == [(2, "alpha beta gamma zeta")]


def test_compare_needs_half_the_words_to_pair():
    got = clauses.compare([(1, "one two three four")], [(1, "one two five six")])
    assert got["reworded"] == [] and len(got["added"]) == len(got["removed"]) == 1
    got = clauses.compare([(1, "one two three")], [(1, "one two three four")])
    assert len(got["reworded"]) == 1  # 3 of 4: over half


def test_diff_prints_what_changed_and_writes_only_the_new_side(tmp_path):
    (tmp_path / "v").mkdir()
    old, new = tmp_path / "v" / "old.txt", tmp_path / "v" / "new.txt"
    old.write_text("Keep this.\n\nWe don't show ads from Gmail.\n\nDrop me now.\n")
    new.write_text(
        "Keep this!\n\nWe don't show ads from Gmail, unless you opt in.\n\nBrand new.\n"
    )
    got = run(
        "diff", "--old", str(old), "--new", str(new), "--to", str(tmp_path / "ch")
    )
    assert got.returncode == 42, got.stderr
    lines = got.stdout.splitlines()
    assert lines[0].startswith(
        "reworded  old.txt:3 -> new.txt:3   (7 of 11 words kept)"
    )
    assert lines[1] == "  - We don't show ads from Gmail."
    assert lines[3] == "added     new.txt:5   Brand new."
    assert lines[4] == "removed   old.txt:5   Drop me now."
    assert lines[5] == "same      1 sentences (1 differ only in spacing or punctuation)"
    assert (tmp_path / "ch" / "new.txt").read_text() == (
        "We don't show ads from Gmail, unless you opt in.\n\nBrand new.\n"
    )
    assert run("diff", "--old", str(old), "--new", str(old)).returncode == 0
    assert (
        "same      3 sentences"
        in run("diff", "--old", str(old), "--new", str(old)).stdout
    )


def test_diff_refuses_what_it_cant_read_or_a_folder_beside_the_versions(tmp_path):
    a = tmp_path / "a.txt"
    a.write_text("One.\n")
    (tmp_path / "bin").write_bytes(b"\0\1")
    assert run("diff", "--old", str(a), "--new", str(tmp_path / "bin")).returncode == 2
    assert run("diff", "--old", str(a), "--new", str(tmp_path / "no")).returncode == 2
    got = run("diff", "--old", str(a), "--new", str(a), "--to", str(tmp_path / "x"))
    assert got.returncode == 2 and not (tmp_path / "x").exists()
    assert run("diff", "--old", str(a), "--new", str(a), "--from", "x").returncode == 2


def test_mirror_skips_what_it_doesnt_read_and_counts_what_isnt_text(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("One. Two.\n")
    (src / "b.pdf").write_bytes(b"%PDF")  # not read: the pdf add-on's job
    (src / "c.md").write_bytes(b"\xff\xfe bad")
    got = run("mirror", "--from", str(src), "--to", str(tmp_path / "m"))
    assert got.returncode == 0 and got.stdout.endswith("; skipped 1\n")
    assert sorted(p.name for p in (tmp_path / "m").iterdir()) == ["a.txt.txt"]
    assert (tmp_path / "m" / "a.txt.txt").read_text() == "One.\n\nTwo.\n"


def test_splitting_its_own_output_changes_nothing():
    once = clauses.as_text(clauses.clauses(WRAPPED, "p.txt"))
    assert clauses.as_text(clauses.clauses(once, "p.txt")) == once
    assert clauses.as_text([]) == ""
