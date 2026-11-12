"""pools, the reading: static.py reads a made-up add-on as it should, and the
kept reading holds the figures and the fourteen the page names. The kept
reading is of main at one commit; it is not held to the code as it moves."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import static  # noqa: E402

PREDICTED = "asciidoc chats code-comments csv-rows dotfiles equations jupyter latex mail markdown notation org rst subtitles"  # fmt: skip
KEPT = json.loads((HERE / "static.json").read_text(encoding="utf-8"))

CODE = """
import kernel
MADE, OTHER = "made", "other"
def go(box, rows):
    kernel.append(box, "ts", MADE, who="x")
    kernel.append(box, "ts", "plain")
    got, _ = kernel.read(box / "record.jsonl")
    out = box / ".places" / "a.pdf"
    return [r for r in got if r["kind"] == OTHER or r.get("kind") in ("bite", MADE)], "%.1f"
"""


def test_it_reads_rows_written_rows_told_apart_and_suffixes(tmp_path):
    (tmp_path / "x.py").write_text(CODE)
    (tmp_path / "test_x.py").write_text(
        'import kernel\nkernel.append(1, 2, "from-a-test")\n'
    )
    got = static.read(tmp_path)
    assert got["writes"] == ["made", "plain"] and got["writes_unread"] == 0
    assert got["takes"] == ["bite", "made", "other"] and got["reads_record"] is True
    assert got["files"] == [".places"], "a.pdf and %.1f are not whole suffixes"
    assert static.card_of(tmp_path) == {}
    (tmp_path / "README.md").write_text(
        "<!-- willow-addon\nsection: Here\nrole: tools\nempty:\n-->\n# x\n"
    )
    assert static.card_of(tmp_path) == {"section": "Here", "role": "tools"}


def test_the_kept_reading_holds_the_figures_the_page_gives():
    said = static.say(KEPT).splitlines()
    for line in (
        "341 add-ons with a card under adapters/stdlib",
        "write a row to the record: 32",
        "tell rows apart by kind: 48",
        "read the record at all: 78",
        "name a file suffix: 157",
        "none of those: 129",
        "kinds of row seen: 54",
        "made and taken only by their maker: 33",
        "made by one add-on and taken by another: 3",
        "links from a maker to another add-on that takes: 26, over 19 add-ons",
    ):
        assert line in said, line


def test_the_fourteen_are_the_ones_that_name_the_map_less_two():
    name_it = {a for a, got in KEPT.items() if ".places" in got["files"]}
    assert name_it - {"ci", "deep-links"} == set(PREDICTED.split())
    page = (HERE.parent / "README.md").read_text(encoding="utf-8")
    assert all(a in page for a in PREDICTED.split())


def test_a_bad_command_line_is_refused():
    assert static.main([]) == 2 and static.main(["say", "nonsense"]) == 2
