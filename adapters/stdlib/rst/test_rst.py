"""rst: a reStructuredText file as the text it shows, line for line; nothing
repeated from passage to passage that would answer a question the folder
can't; hidden files and folders skipped, an unreadable file skipped and
counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "rst.py"
spec = importlib.util.spec_from_file_location("rst", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
kernel = mod.kernel

SAMPLE = b"""\
:Author: Ada Example
:Date: 2026-10-01

=====================
Tides of the Estuary
=====================

.. contents::
   :depth: 2

Method
======

We measure the tide at six harbours [1]_, as `the survey <https://tides.example/survey>`_ says.

.. note::

   Bring a coat on the pier.

.. warning:: The gauge at Whitby drifts.

Results
-------

The mean rise is ``4.2 m`` at |port|.

.. |port| replace:: Whitby harbour

.. code-block:: python
   :linenos:

   rise = mean(gauge)

Run it with::

   python tides.py

.. [1] Smith, 2020.

.. _survey: https://tides.example/survey

.. image:: chart.png
   :alt: Chart of the spring tides

.. This is a comment
   spanning two lines.
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


def rst(body: str) -> str:
    return mod.convert(body.encode())


def line_of(src: bytes, needle: str) -> int:
    return src.decode().split("\n").index(needle)


def test_the_mirror_has_the_sources_lines_so_a_passage_is_cited_by_its_own_line():
    out = mod.convert(SAMPLE).split("\n")
    assert len(out) <= len(SAMPLE.decode().split("\n"))
    expect = {
        ":Author: Ada Example": "author: Ada Example",
        "Tides of the Estuary": "Tides of the Estuary",
        "Method": "Method",
        "We measure the tide at six harbours [1]_, as `the survey <https://tides.example/survey>`_ says.":
            "We measure the tide at six harbours, as the survey (https://tides.example/survey) says.",
        "   Bring a coat on the pier.": "note: Bring a coat on the pier.",
        ".. warning:: The gauge at Whitby drifts.": "warning: The gauge at Whitby drifts.",
        "The mean rise is ``4.2 m`` at |port|.": "The mean rise is 4.2 m at Whitby harbour.",
        "   rise = mean(gauge)": "rise = mean(gauge)",
        "Run it with::": "Run it with:",
        "   python tides.py": "python tides.py",
        ".. [1] Smith, 2020.": "[1] Smith, 2020.",
        "   :alt: Chart of the spring tides": "",
        ".. image:: chart.png": "Chart of the spring tides",
    }  # fmt: skip
    for src, want in expect.items():
        assert out[line_of(SAMPLE, src)] == want, src


def test_adornments_directives_options_targets_and_comments_are_blank():
    out = mod.convert(SAMPLE).split("\n")
    out += [""] * (len(SAMPLE.split(b"\n")) - len(out))  # trailing blanks trimmed
    for src in (
        "=====================",
        "======",
        "-------",
        ".. contents::",
        "   :depth: 2",
        ".. note::",
        ".. |port| replace:: Whitby harbour",
        ".. code-block:: python",
        "   :linenos:",
        ".. _survey: https://tides.example/survey",
        ".. This is a comment",
        "   spanning two lines.",
    ):
        assert out[line_of(SAMPLE, src)] == "", src


def test_a_title_is_its_own_text_never_the_titles_above_it():
    out = rst("Garden\n======\n\nTomatoes\n--------\n\nSix hours of sun.\n")
    assert out == "Garden\n\n\nTomatoes\n\n\nSix hours of sun.\n"
    # an underline shorter than a long title is not one; a short title's is
    assert rst("A long line of prose\n--\n") == "A long line of prose\n--\n"
    assert rst("Hi\n--\n") == "Hi\n"


def test_a_transition_is_blank_and_an_overlined_title_may_be_indented():
    assert rst("one\n\n----------\n\ntwo\n") == "one\n\n\n\ntwo\n"
    assert rst("=========\n Support\n=========\n\ntext\n") == "\nSupport\n\n\ntext\n"


def test_admonitions_and_version_notes_say_what_they_are_once():
    out = rst(
        ".. tip:: Water early.\n\n.. versionadded:: 3.2\n\n.. versionchanged:: 3.4 Now faster.\n\n"
        ".. seealso:: The almanac.\n\n.. admonition:: Frost dates\n\n   Mid May.\n"
    )
    assert out == (
        "tip: Water early.\n\nversionadded 3.2\n\nversionchanged 3.4: Now faster.\n\n"
        "seealso: The almanac.\n\nFrost dates\n\nMid May.\n"
    )


def test_a_note_whose_body_opens_with_code_keeps_its_label_on_its_own_line():
    out = rst(".. note::\n\n   .. code-block:: sh\n\n      make all\n")
    assert out == "note:\n\n\n\nmake all\n"


def test_code_literal_blocks_and_doctests_are_kept_as_written():
    out = rst(
        "Example ::\n\n    def f(*args, **kw):\n        return `x`_\n\nAfter.\n\n::\n\n  a_b_\n\n"
        ">>> f(1)\n*2*\n\n.. doctest::\n\n   >>> g()\n"
    )
    assert out == (
        "Example\n\ndef f(*args, **kw):\n    return `x`_\n\nAfter.\n\n\n\na_b_\n\n"
        ">>> f(1)\n*2*\n\n\n\n>>> g()\n"
    )


def test_blank_directives_drop_their_options_and_body():
    out = rst(
        "a\n\n.. toctree::\n   :maxdepth: 2\n\n   intro\n   usage\n\n.. raw:: html\n\n   <hr>\n\n"
        ".. include:: other.rst\n\n.. index:: tides\n\nb\n"
    )
    assert out.split() == ["a", "b"]


def test_containers_keep_their_body_and_signatures_keep_their_arguments():
    out = rst(
        ".. only:: html\n\n   Shown on the web.\n\n.. function:: encrypt(message, *keys)\n\n   Encrypts it.\n"
    )
    assert out == "\n\nShown on the web.\n\nencrypt(message, *keys)\n\nEncrypts it.\n"


def test_a_figure_keeps_its_alt_and_its_caption_an_image_without_alt_is_blank():
    out = rst(
        ".. figure:: tide.png\n   :alt: Tide chart\n   :width: 50%\n\n   The spring tide, *March*.\n\n"
        ".. image:: badge.svg\n   :target: https://x.example\n\nText.\n"
    )
    assert out == "Tide chart\n\n\n\nThe spring tide, March.\n\n\n\n\nText.\n"


def test_links_roles_and_emphasis_read_as_their_text():
    out = rst(
        "See `the shop <https://shop.example/>`__, `the guide <guide.html>`_, `Home`_, "
        "PyPI_ and MAX_ here.\n"
        ":ref:`the tides <tide-table>` and :func:`~rsa.newkeys`, :py:mod:`email`, "
        "`x`:sub: and :rfc:`5322` and :math:`x^2` gone.\n"
        "**Bold** and *italic*, `default`, _`a target`, a\\ b and \\*not\\* emphasis.\n"
        "\n.. _Home: https://home.example\n.. _pypi: https://pypi.org\n"
    )
    assert out.split("\n")[:3] == [
        "See the shop (https://shop.example/), the guide, Home, PyPI and MAX_ here.",
        "the tides and newkeys, email, x and RFC 5322 and gone.",
        "Bold and italic, default, a target, ab and *not* emphasis.",
    ]


def test_a_link_that_wraps_onto_the_next_line_reads_on_both():
    out = rst("Ask the `Mailing list\n <http://lists.example/tides>`_ first.\n")
    assert out == "Ask the Mailing list\n(http://lists.example/tides) first.\n"


def test_substitutions_read_as_their_replacement_and_unknown_ones_are_left():
    out = rst(
        "|name| of |Copy| |badge| and |unknown|.\n\n.. |name| replace:: Tide *Table*\n"
        "   Project\n.. |copy| unicode:: 0xA9\n.. |badge| image:: b.svg\n   :alt: Build ok\n"
    )
    assert out.split("\n")[0] == "Tide Table Project of © Build ok and |unknown|."


def test_footnotes_lose_their_references_and_keep_their_text():
    out = rst(
        "Six [#f1]_ harbours [CIT2002]_.\n\n.. [#f1] Counted in 2020.\n   Twice.\n\n.. [#] Auto.\n"
    )
    assert out == "Six harbours.\n\n[f1] Counted in 2020.\nTwice.\n\nAuto.\n"


def test_fields_bullets_and_line_blocks():
    out = rst(
        ":Build status: green\n:Version:\n\n* first\n+ second with ``code``\n"
        "- .. versionadded:: 3.6\n\n| Roses are red,\n|  violets blue.\n"
    )
    assert out == (
        "build status: green\nversion:\n\n- first\n- second with code\n"
        "- versionadded 3.6\n\nRoses are red,\nviolets blue.\n"
    )


def test_a_literal_block_under_a_bullet_is_kept():
    out = rst("- Install it::\n\n      pip install tides\n\n- Done.\n")
    assert out == "- Install it:\n\npip install tides\n\n- Done.\n"


SIMPLE = """\
==========  ==========
Harbour     Rise
==========  ==========
Whitby      4.2 m
Leeds       3.9 m
            (estimated)
Hull spans the gap here
==========  ==========
"""

GRID = """\
+----------+------------------+
| Command  | Usage            |
+==========+==================+
| keygen   | Makes a new      |
|          | keypair.         |
+----------+------------------+
| sign     | Signs a file.    |
+----------+------------------+
| both spanning one cell      |
+----------+------------------+
"""


def test_a_simple_table_is_its_cells_with_the_header_written_once():
    assert rst(SIMPLE) == (
        "\nHarbour; Rise\n\nWhitby; 4.2 m\nLeeds; 3.9 m\n(estimated)\nHull spans the gap here\n"
    )


def test_a_grid_table_row_is_its_cells_on_its_first_line_a_cell_joined():
    assert rst(GRID) == (
        "\nCommand; Usage\n\nkeygen; Makes a new keypair.\n\n\nsign; Signs a file.\n\n"
        "both spanning one cell\n"
    )


def test_an_ordinary_line_of_equals_signs_with_spaces_is_not_a_table():
    assert rst("a\n\n===  ===\n\nb\n") == "a\n\n=== ===\n\nb\n"


def test_tabs_crlf_and_a_byte_order_mark():
    out = mod.convert(
        b"\xef\xbb\xbfTitle\r\n=====\r\n\r\n.. note::\r\n\r\n\tTabbed.\r\n"
    )
    assert out == "Title\n\n\n\n\nnote: Tabbed.\n"


def test_a_file_with_no_text_is_not_a_result():
    assert mod.convert(b".. toctree::\n   intro\n\n.. a comment\n") is None
    assert mod.convert(b"") is None


# Owner's ruling: a word the reader adds on passage after passage answers any
# two-word question that names it. Every word on most passages of a mirror,
# paired with a word the folder doesn't hold, must be answered by nothing.
NOTES = b"""\
Garden notes
============

Tomatoes
--------

Tomatoes want six hours of sun.

.. note:: Water them at dawn.

Beans
-----

Beans climb the north fence.

.. versionadded:: 2024

Plots
-----

+--------+----------+
| Plot   | Crop     |
+========+==========+
| 14     | leeks    |
+--------+----------+
| 15     | carrots  |
+--------+----------+

======  =======
Shed    Key
======  =======
north   brass
south   iron
======  =======

.. [1] Plot 14 floods in March.

.. [2] Plot 15 has the shed.
"""


def test_no_word_the_reader_adds_answers_a_question_about_something_absent(tmp_path):
    got, out = mirror_of(tmp_path, {"garden.rst": NOTES, "more/again.rst": NOTES})
    assert got.returncode == 0, got.stderr
    pile = kernel.chunks(out)
    assert len(pile) >= 8
    seen = Counter(
        w for c in pile for w in set(kernel.words(c["text"])) - kernel.FUNCTION
    )
    common = [w for w, n in seen.items() if n * 2 >= len(pile)]
    for word in common + ["version", "new", "title", "header", "value"]:
        assert kernel.rank(pile, f"volcano {word}") == [], word
    for question, holds in (
        ("how many hours of sun for tomatoes", "six hours"),
        ("which fence do beans climb", "north fence"),
        ("which plot has carrots", "15; carrots"),
        ("when does plot 14 flood", "March"),
        ("is the brass one north", "north; brass"),
    ):
        top = kernel.rank(pile, question)
        assert top and holds in top[0]["text"], question
    # the accepted cost: a question naming a column finds the header row,
    # since a header is no longer beside each value
    assert kernel.rank(pile, "what crop is in plot 15")[0]["text"] == "Plot; Crop"


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"docs/index.rst": SAMPLE, "b.rest": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (out / "docs/index.rst.txt").is_file() and (out / "b.rest.txt").is_file()
    assert "wrote 2 files to" in got.stdout and got.stdout.strip().endswith("skipped 0")


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {"docs/a.rst": SAMPLE, ".hid/docs/a.rst": SAMPLE, ".a.rst": SAMPLE},
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == [".places/docs/a.rst.txt.json", "docs/a.rst.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"docs/a.rst": SAMPLE})
    before = (tmp_path / "src" / "docs/a.rst").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "docs/a.rst.txt").read_bytes() == (
        out / "docs/a.rst.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "docs/a.rst").read_bytes() == before
    assert sorted(p.name for p in (tmp_path / "src").rglob("*")) == ["a.rst", "docs"]


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {"good.rst": SAMPLE, "bad.rst": b"\xff\xfe not utf8", "empty.rst": b".. x\n"},
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 2" in got.stdout
    assert (out / "good.rst.txt").is_file() and not (out / "bad.rst.txt").exists()


def test_a_folder_with_nothing_to_read_waits_on_you(tmp_path):
    got, _ = mirror_of(tmp_path, {"notes.md": b"nothing here\n"})
    assert got.returncode == 42 and "wrote 0 files" in got.stdout


def test_a_mirror_inside_the_folder_or_the_folder_inside_it_is_refused(tmp_path):
    (tmp_path / "src").mkdir()
    for to in (tmp_path / "src" / "m", tmp_path):
        got = run("mirror", "--from", str(tmp_path / "src"), "--to", str(to))
        assert got.returncode == 2 and got.stderr.startswith("refused")
    missing = run(
        "mirror", "--from", str(tmp_path / "missing"), "--to", str(tmp_path / "m")
    )
    assert missing.returncode == 2 and not (tmp_path / "m").exists()


def test_a_bad_command_line_says_how_to_run_it():
    for argv in (
        [],
        ["mirror"],
        ["mirror", "--from", "a"],
        ["nope", "--from", "a", "--to", "b"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "rst.py" in got.stderr


def test_an_overlined_title_at_the_very_end_of_a_file_is_still_a_title():
    # its text would read as a list item if it weren't taken as a title
    assert rst("=============\n* Appendix *\n=============") == "\n* Appendix *\n"
