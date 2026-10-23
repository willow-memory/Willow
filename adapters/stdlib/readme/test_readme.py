"""The README generator: the front page is built from the add-ons, and can't
drift from them.

Each test holds one promise in adapters/stdlib/readme/README.md, and each can
fail: the real README is current, building an add-on is what turns an idea into a built one,
the draw is the same for the same week and anyone can redo it, only the
marked sections are written, and an add-on that doesn't hold together is
refused.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("readme", HERE / "readme.py")
rd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rd)

PAGE = """# a page

Written by hand.

<!-- willow:pools -->
<!-- /willow:pools -->

<!-- willow:newest -->
<!-- /willow:newest -->

Also by hand.

<!-- willow:pick week=2026-W43 -->
<!-- /willow:pick -->

<!-- willow:list -->
<!-- /willow:list -->

The end, by hand.
"""


def card(section="Play", line="A thing.", source="new", added="2026-10-23", **more):
    head = {"section": section, "line": line, "source": source, "added": added,
            "writes": "nothing", "network": "none", "tags": "play, thing", **more}  # fmt: skip
    body = "".join(f"{k}: {v}\n" for k, v in head.items())
    return f"<!-- willow-addon\n{body}-->\n# card\n"


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A small repo: one built add-on in each folder, one planned. Made with
    tempfile, so the guard knows it as this test's scratch, not the repo
    readme.py's card names."""
    tmp_path = Path(tempfile.mkdtemp(dir=tmp_path))
    for kind, name, extra in (
        ("stdlib", "alpha", {}),
        ("deps", "beta", {"needs": "somepkg; MIT"}),
    ):
        (tmp_path / "adapters" / kind / name).mkdir(parents=True)
        (tmp_path / "adapters" / kind / name / "README.md").write_text(
            card(added="2026-10-0" + str(len(name)), **extra)
        )
    planned = [{"name": "gamma", "kind": "stdlib", "section": "Play", "line": "Later.",
                "source": "box", "writes": "to", "network": "loopback",
                "tags": "later"}]  # fmt: skip
    (tmp_path / "adapters" / "planned.json").write_text(json.dumps(planned))
    (tmp_path / "README.md").write_text(PAGE)
    monkeypatch.setattr(rd, "ROOT", tmp_path)
    monkeypatch.setattr(rd, "README", tmp_path / "README.md")
    monkeypatch.setattr(rd, "ADAPTERS", tmp_path / "adapters")
    monkeypatch.setattr(rd, "PLANNED", tmp_path / "adapters" / "planned.json")
    return tmp_path


def test_the_real_readme_is_current():
    got = subprocess.run(
        [sys.executable, str(HERE / "readme.py"), "check"],
        capture_output=True,
        text=True,
    )
    assert got.returncode == 0, got.stdout + got.stderr


def test_building_an_add_on_is_what_turns_planned_into_built(repo):
    text = rd.rebuild(PAGE, None)
    assert (
        "- [**alpha**](adapters/stdlib/alpha/) — A thing. *new* `play` `thing`" in text
    )
    assert (
        "- [**beta**](adapters/deps/beta/) — A thing. Needs somepkg; MIT. *new* `play` `thing`"
        in text
    )
    assert (
        "- **gamma** (idea) — Later. Reaches this machine only. *box* `later`" in text
    )
    assert "**2 of 3 built**" in text
    (repo / "adapters" / "stdlib" / "gamma").mkdir()  # built, and still planned
    (repo / "adapters" / "stdlib" / "gamma" / "README.md").write_text(card())
    with pytest.raises(rd.Refused, match="still in planned.json"):
        rd.rebuild(PAGE, None)
    (repo / "adapters" / "planned.json").write_text("[]")
    assert "- [**gamma**](adapters/stdlib/gamma/)" in rd.rebuild(PAGE, None)


def test_only_the_marked_sections_are_written(repo):
    text = rd.rebuild(PAGE, None)
    for hand in (
        "# a page\n\nWritten by hand.\n",
        "Also by hand.",
        "The end, by hand.\n",
    ):
        assert hand in text
    assert rd.rebuild(text, None) == text  # rebuilding what's built changes nothing
    assert "newest" in text and "2026-10-05 · [**alpha**]" in text


def test_the_draw_is_the_weeks_and_anyone_can_redo_it(repo):
    every = rd.addons()
    built = sorted(a["name"] for a in every if a["built"])
    for week in ("2026-W43", "2026-W44", "2027-W01"):
        by_hand = int(rd.kernel.h256(f"willow add-on of the week {week}"), 16) % len(
            built
        )
        assert f"**[{built[by_hand]}]" in rd.section_pick(every, week)
        assert rd.section_pick(every, week) == rd.section_pick(every, week)
    text = rd.rebuild(PAGE, None)  # check keeps the week already written
    assert "<!-- willow:pick week=2026-W43 -->" in text
    assert "<!-- willow:pick week=2027-W01 -->" in rd.rebuild(PAGE, "2027-W01")


@pytest.mark.parametrize(
    "folder, text, why",
    [
        ("stdlib/delta", "# no header\n", "doesn't open with a willow-addon header"),
        ("stdlib/delta", card(section="Nowhere"), "no section 'Nowhere'"),
        ("stdlib/delta", card(source="elsewhere"), "source is bot, box or new"),
        ("stdlib/delta", card(added="soon"), "added is the date"),
        ("stdlib/delta", card(needs="x; MIT"), "a stdlib add-on needs nothing"),
        ("deps/delta", card(), "a deps add-on says what it needs"),
        ("stdlib/delta", card(writes="everything"), "writes is nothing, or any of"),
        ("stdlib/delta", card(writes="nothing, to"), "writes is nothing, or any of"),
        ("stdlib/delta", card(writes="README.md, record"), None),
        (
            "stdlib/delta",
            card(writes="no-such-file.md"),
            "writes is nothing, or any of",
        ),
        ("stdlib/delta", card().replace("network: none\n", ""), "needs network"),
        ("stdlib/Delta", card(), "lowercase words joined by -"),
        ("stdlib/delta", card(tags="a, b, c, d, e, f"), "tags are up to 5"),
        ("stdlib/delta", card(tags="Has Caps"), "tags are up to 5"),
        ("stdlib/delta", card(tags="a, a"), "tags are up to 5"),
        (
            "stdlib/delta",
            card().replace("tags: play, thing\n", ""),
            "run readme.py tags",
        ),
        ("stdlib/alpha2", "", "has no README.md card"),
    ],
)
def test_an_add_on_that_doesnt_hold_together_is_refused(repo, folder, text, why):
    where = repo / "adapters" / folder
    where.mkdir(parents=True)
    if text:
        (where / "README.md").write_text(text)
    if why is None:  # a file of the repo, beside record: holds together
        (repo / "README.md").touch()
        rd.rebuild(PAGE, None)
        return
    with pytest.raises(rd.Refused, match=why):
        rd.rebuild(PAGE, None)


def test_a_readme_missing_a_section_is_refused(repo):
    with pytest.raises(rd.Refused, match="needs one each"):
        rd.rebuild(
            PAGE.replace("<!-- willow:newest -->\n<!-- /willow:newest -->\n", ""), None
        )


def test_tags_fills_only_what_is_missing_and_keeps_what_a_person_wrote(repo):
    """Auto-populated, never overwritten: the card's tags are its author's."""
    card_file = repo / "adapters" / "stdlib" / "alpha" / "README.md"
    card_file.write_text(card_file.read_text().replace("tags: play, thing\n", ""))
    beta = repo / "adapters" / "deps" / "beta" / "README.md"
    planned = repo / "adapters" / "planned.json"
    planned.write_text(planned.read_text().replace(', "tags": "later"', ""))
    before = beta.read_text()
    assert rd.main(["tags"]) == 0
    assert "tags: no-install, offline, read-only, play\n-->" in card_file.read_text()
    assert beta.read_text() == before  # a person's tags, untouched
    assert json.loads(planned.read_text())[0]["tags"] == (
        "no-install, this-machine, writes-output, play"
    )
    assert rd.main(["tags"]) == 0 and beta.read_text() == before  # twice: no change
