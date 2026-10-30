"""The add-on list and the front page's one feature are built from the
add-ons, and can't drift from them.

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

<!-- willow:languages -->
<!-- /willow:languages -->

<!-- willow:newest -->
<!-- /willow:newest -->

Also by hand.

<!-- willow:pick week=2026-W43 -->
<!-- /willow:pick -->

<!-- willow:list -->
<!-- /willow:list -->

The end, by hand.
"""

FRONT = """# the front page

<!-- willow:summary -->
<!-- /willow:summary -->

<!-- willow:front show=pick week=2026-W43 -->
<!-- /willow:front -->
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
    (tmp_path / "ADDONS.md").write_text(PAGE)
    (tmp_path / "README.md").write_text(FRONT)
    monkeypatch.setattr(rd, "ROOT", tmp_path)
    monkeypatch.setattr(rd, "README", tmp_path / "README.md")
    monkeypatch.setattr(rd, "ADDONS_MD", tmp_path / "ADDONS.md")
    monkeypatch.setattr(rd, "ADAPTERS", tmp_path / "adapters")
    monkeypatch.setattr(rd, "PLANNED", tmp_path / "adapters" / "planned.json")
    return tmp_path


def test_the_real_readme_is_current():
    """The generated sections are a view, recomputed from the cards (CONST-VI-6)."""
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
    """A card that doesn't list what its add-on writes and where it goes
    online is refused: a reach is enumerated, never inferred (CONST-II-1)."""
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


def test_check_keeps_the_week_written_whatever_week_it_is(repo):
    """`write --week` sets the draw's week; `check` never moves it to today's."""
    assert rd.main(["write", "--week", "2027-W01"]) == 0
    assert "<!-- willow:pick week=2027-W01 -->" in (repo / "ADDONS.md").read_text()
    assert (
        "<!-- willow:front show=pick week=2027-W01 -->"
        in (repo / "README.md").read_text()
    )
    assert rd.main(["check"]) == 0


def rebuild_front(show: str) -> str:
    return rd.rebuild(
        FRONT.replace("show=pick", f"show={show}"),
        None,
        ("summary", "front"),
        "README.md",
    )


@pytest.mark.parametrize("show, title, has", [
    ("pick", "Add-on of the week", "*Drawn for 2026-W43"),
    ("newest", "Newest", "2026-10-05 · [**alpha**]"),
    ("pools", "How the list stands", "| Section | Built |"),
])  # fmt: skip
def test_the_front_page_shows_the_one_feature_its_marker_names(repo, show, title, has):
    text = rebuild_front(show)
    assert f"**{title}**" in text and has in text
    assert (
        "[Every add-on, 2 built of 3, and how to add one: ADDONS.md](ADDONS.md)" in text
    )
    marker = next(ln for ln in text.splitlines() if ln.startswith("<!-- willow:front"))
    assert ("week=" in marker) == (show == "pick")  # a week only for the draw
    assert rebuild_front(show) == rd.rebuild(
        text, None, ("summary", "front"), "README.md"
    )


@pytest.mark.parametrize("show", ["list", "Pick", "everything"])
def test_a_front_page_feature_that_isnt_one_is_refused(repo, show):
    with pytest.raises(rd.Refused, match="front shows one of pick, newest, pools"):
        rebuild_front(show)


def test_check_says_which_page_is_stale(repo, capsys):
    assert rd.main(["write"]) == 0
    (repo / "README.md").write_text((repo / "README.md").read_text().replace("Add-on of", "Add-in of"))  # fmt: skip
    assert rd.main(["check"]) == 2
    assert "README.md isn't current" in capsys.readouterr().out


def test_every_section_says_what_its_for():
    assert list(rd.WHAT) == rd.NAMES


def test_the_summary_gives_a_built_example_not_the_whole_list(repo, monkeypatch):
    monkeypatch.setitem(rd.EXAMPLES, "Play", ["alpha", "gamma", "beta"])
    play = next(
        ln for ln in rd.section_summary(rd.addons()).splitlines() if "**Play:**" in ln
    )
    assert play.endswith(
        "For example [alpha](adapters/stdlib/alpha/) and [beta](adapters/deps/beta/)."
    )
    assert "Built:" not in play and "gamma" not in play
    monkeypatch.setitem(rd.EXAMPLES, "Keeping track", ["alpha"])
    keeping = next(
        ln
        for ln in rd.section_summary(rd.addons()).splitlines()
        if "**Keeping track:**" in ln
    )
    assert "For example" not in keeping


def test_every_example_is_built_and_in_its_section():
    every = {a["name"]: a for a in rd.addons() if a["built"]}
    assert set(rd.EXAMPLES) <= set(rd.NAMES)
    for title, names in rd.EXAMPLES.items():
        for name in names:
            assert every[name]["section"] == title


def test_the_languages_are_the_words_packs_built_and_planned(repo):
    for name, line in (("words-cy", "Welsh common words."), ("words-tlh", "Klingon | words."),
                       ("words-list", "Not a language: four letters.")):  # fmt: skip
        (repo / "adapters" / "stdlib" / name).mkdir()
        (repo / "adapters" / "stdlib" / name / "README.md").write_text(
            card(section="Your own words", line=line)
        )
    planned = json.loads((repo / "adapters" / "planned.json").read_text())
    planned.append({"name": "words-zh", "kind": "stdlib", "section": "Your own words",
                    "line": "Chinese.", "source": "new", "writes": "record",
                    "network": "none", "tags": "words"})  # fmt: skip
    (repo / "adapters" / "planned.json").write_text(json.dumps(planned))
    got = rd.section_languages(rd.addons())
    assert got.startswith("**2 built, 1 planned**")
    rows = [r for r in got.splitlines() if r.startswith("| `")]
    assert rows == [
        "| `cy` | [words-cy](adapters/stdlib/words-cy/) | Welsh common words. |",
        "| `tlh` | [words-tlh](adapters/stdlib/words-tlh/) | Klingon \\| words. |",
        "| `zh` | words-zh *(idea)* | Chinese. |",
    ]  # words-list isn't a language: only words- and a two- or three-letter code
