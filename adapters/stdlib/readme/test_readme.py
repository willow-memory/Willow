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
import re
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
            "writes": "nothing", "network": "none", "role": "tools", **more}  # fmt: skip
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
                "role": "makes", "tags": "later"}]  # fmt: skip
    (tmp_path / "adapters" / "planned.json").write_text(json.dumps(planned))
    (tmp_path / "ADDONS.md").write_text(PAGE)
    (tmp_path / "README.md").write_text(FRONT)
    monkeypatch.setattr(rd, "ROOT", tmp_path)
    monkeypatch.setattr(rd, "README", tmp_path / "README.md")
    monkeypatch.setattr(rd, "ADDONS_MD", tmp_path / "ADDONS.md")
    monkeypatch.setattr(rd, "ADAPTERS", tmp_path / "adapters")
    monkeypatch.setattr(rd, "PLANNED", tmp_path / "adapters" / "planned.json")
    monkeypatch.setattr(rd, "WEEK_FILE", tmp_path / "week.json")
    # a bare write draws for this week, as it should; these tests write
    # 2026-W45 and mean "still that week", so this week is that week here,
    # whatever the calendar says (they failed the day W46 began)
    monkeypatch.setattr(rd, "this_week", lambda: "2026-W45")
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
    # an entry is three lines: its anchor and name; its line; then, after a
    # hard break, what it needs and where it goes, and its source and tags
    assert '- <a id="alpha"></a>[**alpha**](adapters/stdlib/alpha/) \\\n  A thing. \\\n  *new* `no-install` `offline`' in text  # fmt: skip
    assert (
        '- <a id="beta"></a>[**beta**](adapters/deps/beta/) \\\n  A thing. \\\n  Needs somepkg; MIT. *new* `needs-install` `offline`'
        in text
    )
    assert (
        '- <a id="gamma"></a>**gamma** (idea) \\\n  Later. \\\n  Reaches this machine only. *box* `no-install` `this-machine` `later`'
        in text
    )
    assert "**2 of 3 built**" in text
    (repo / "adapters" / "stdlib" / "gamma").mkdir()  # built, and still planned
    (repo / "adapters" / "stdlib" / "gamma" / "README.md").write_text(card())
    with pytest.raises(rd.Refused, match="still in planned.json"):
        rd.rebuild(PAGE, None)
    (repo / "adapters" / "planned.json").write_text("[]")
    assert '- <a id="gamma"></a>[**gamma**](adapters/stdlib/gamma/)' in rd.rebuild(
        PAGE, None
    )


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
        ("stdlib/delta", card(programs="vim"), "only a deps add-on names programs"),
        (
            "deps/delta",
            card(needs="the gpg program; GPL", programs="gpg, tesseract"),
            "programs names tesseract, which needs doesn't",
        ),
        ("deps/delta", card(needs="the gpg program; GPL", programs="gpg"), None),
        ("stdlib/delta", card(writes="everything"), "writes is nothing, or any of"),
        ("stdlib/delta", card(writes="nothing, to"), "writes is nothing, or any of"),
        ("stdlib/delta", card(writes="README.md, record"), None),
        (
            "stdlib/delta",
            card(writes="no-such-file.md"),
            "writes is nothing, or any of",
        ),
        ("stdlib/delta", card().replace("network: none\n", ""), "needs network"),
        ("stdlib/delta", card().replace("role: tools\n", ""), "needs role"),
        ("stdlib/delta", card(role="everything"), "role is one of"),
        ("stdlib/delta", card(**{"runs-in": "repo"}), "role is repo exactly when"),
        ("stdlib/delta", card(role="repo"), "role is repo exactly when"),
        ("stdlib/delta", card(role="repo", **{"runs-in": "repo"}), None),
        ("stdlib/delta", card(role="reads"), "a reader says what it reads"),
        ("stdlib/delta", card(role="reads", reads=".pdf, zotero.sqlite"), None),
        ("stdlib/delta", card(role="reads", reads="none"), None),
        ("stdlib/delta", card(role="reads", reads="pdf files!"), "reads is .ext"),
        ("stdlib/delta", card(reads=".pdf"), "reads is for a card whose role is reads"),
        ("stdlib/delta", card(output="report"), None),
        ("stdlib/delta", card(role="reads", reads=".md", output="mirror"), None),
        (
            "stdlib/delta",
            card(output="mirror"),
            "output mirror is for a card whose role is reads",
        ),
        ("stdlib/delta", card(output="suggestions"), None),
        ("stdlib/delta", card(output="report, suggestions"), None),
        (
            "stdlib/delta",
            card(output="prose"),
            "output is one of mirror, report, suggestions",
        ),
        (
            "stdlib/delta",
            card(output="report, report"),
            "output is one of mirror, report, suggestions",
        ),
        (
            "stdlib/delta",
            card(form="shape, https://x.example/y, MIT"),
            "form is not a card's field",
        ),
        ("stdlib/delta", card(**{"from": "shape, https://github.com/a/b, MIT"}), None),
        ("stdlib/delta", card(**{"from": "shape, https://a.example/b, none"}), None),
        (
            "stdlib/delta",
            card(
                **{
                    "from": "shape, https://a.example/b, MIT; shape, https://c.example/d, BSD-3-Clause"
                }
            ),
            None,
        ),
        (
            "stdlib/delta",
            card(**{"from": "copied, https://a.example/b, MIT"}),
            "from is how",
        ),
        ("stdlib/delta", card(**{"from": "shape, https://a.example/b"}), "from is how"),
        (
            "stdlib/delta",
            card(**{"from": "shape, github.com/a/b, MIT"}),
            "an https:// link",
        ),
        (
            "stdlib/delta",
            card(**{"from": "shape, https://a.example/b, the MIT one"}),
            "from's licence",
        ),
        (
            "stdlib/delta",
            card(**{"from": "code, https://a.example/b, none"}),
            "only under a licence",
        ),
        (
            "stdlib/delta",
            card(**{"from": "code, https://a.example/b, GPL-3.0-only"}),
            "can't: take its shape",
        ),
        (
            "stdlib/delta",
            card(**{"from": "code, https://a.example/b, LGPL-3.0"}),
            "can't: take its shape",
        ),
        (
            "stdlib/delta",
            card(**{"from": "code, https://a.example/b, MIT"}),
            "keeps its notice",
        ),
        (
            "stdlib/delta",
            card(**{"from": "dep, https://a.example/b, MIT"}),
            "for a deps add-on",
        ),
        (
            "deps/delta",
            card(needs="b; MIT", **{"from": "dep, https://a.example/b, MIT"}),
            None,
        ),
        ("stdlib/Delta", card(), "lowercase words joined by -"),
        ("stdlib/delta", card(tags="a, b"), "tags is your one tag"),
        ("stdlib/delta", card(tags="Has Caps"), "tags is your one tag"),
        ("stdlib/delta", card(tags="offline"), "worked out from the card"),
        ("stdlib/delta", card(tags="money"), None),
        ("stdlib/delta", card(), None),  # a tag of your own is optional
        ("stdlib/delta", card(hands="none"), "leave it off when it hands nothing"),
        ("stdlib/delta", card(hands="the passages, to the client's model"), None),
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


@pytest.mark.parametrize(
    "code",
    [
        'print(json.dumps({"additionalContext": text}))',
        'req = {"method": "sampling/createMessage"}',
        'reply = {"jsonrpc": "2.0", "result": served}',
        "from mcp.server.fastmcp import FastMCP",
    ],
)
def test_code_that_hands_text_to_a_model_needs_a_hands_line(repo, code):
    """What leaves is said before it leaves (CONST-III-5): code that writes a
    hook's context, a JSON-RPC reply, a sampling request or an MCP server is
    refused until its card says what it hands and to whom; a test file
    holding the same text is not the add-on's code."""
    where = repo / "adapters" / "stdlib" / "delta"
    where.mkdir(parents=True)
    (where / "README.md").write_text(card())
    (where / "test_delta.py").write_text(code + "\n")
    (repo / "README.md").touch()
    rd.rebuild(PAGE, None)  # only a test holds it: holds together
    (where / "delta.py").write_text(code + "\n")
    with pytest.raises(rd.Refused, match="delta.py hands text to another program"):
        rd.rebuild(PAGE, None)
    (where / "README.md").write_text(card(hands="the passages, to the client's model"))
    rd.rebuild(PAGE, None)


def test_code_taken_keeps_the_notice_of_where_it_came_from(repo):
    """Code ported from another project is held to its licence's notice: the
    card that says so is refused until the notice is in the add-on's folder."""
    where = repo / "adapters" / "stdlib" / "delta"
    where.mkdir(parents=True)
    (where / "README.md").write_text(
        card(**{"from": "code, https://github.com/a/b, MIT"})
    )
    with pytest.raises(rd.Refused, match="keeps its notice"):
        rd.rebuild(PAGE, None)
    (where / "LICENSE-b").write_text("MIT License, Copyright (c) A\n")
    assert "From: code of [a/b](https://github.com/a/b), MIT." in flat(
        rd.rebuild(PAGE, None)
    )


def test_an_ideas_from_is_said_and_an_unknown_field_refused(repo):
    """An idea says where its shape comes from as a built card does, and a
    field no card has is refused, never read as one left out."""
    planned = json.loads((repo / "adapters" / "planned.json").read_text())
    planned[0]["from"] = (
        "shape, https://github.com/a/b, BSD-3-Clause; shape, https://c.example/d/, none"
    )
    (repo / "adapters" / "planned.json").write_text(json.dumps(planned))
    text = rd.rebuild(PAGE, None)
    assert (
        '- <a id="gamma"></a>**gamma** (idea) \\ Later. \\ Reaches this machine only. From: shape of '
        "[a/b](https://github.com/a/b), BSD-3-Clause; shape of [c.example/d](https://c.example/d/), none."
        " *box*" in flat(text)
    ), "its facts, wrapped to the width, read as one paragraph"
    planned[0]["added"] = "2026-10-01"  # a built card's field, not an idea's
    (repo / "adapters" / "planned.json").write_text(json.dumps(planned))
    with pytest.raises(rd.Refused, match="added is not a card's field"):
        rd.rebuild(PAGE, None)


def test_a_readme_missing_a_section_is_refused(repo):
    with pytest.raises(rd.Refused, match="needs one each"):
        rd.rebuild(
            PAGE.replace("<!-- willow:newest -->\n<!-- /willow:newest -->\n", ""), None
        )


def test_tags_are_worked_out_and_never_written_into_a_card(repo):
    """A card keeps only its author's own tag; the rest are a view of the card,
    so changing what the card says changes them, with no tag to edit."""
    cards = sorted((repo / "adapters").rglob("README.md"))
    before = {c: c.read_text() for c in cards}
    planned = (repo / "adapters" / "planned.json").read_text()
    assert rd.main(["write"]) == 0
    assert {c: c.read_text() for c in cards} == before
    assert (repo / "adapters" / "planned.json").read_text() == planned
    alpha = repo / "adapters" / "stdlib" / "alpha" / "README.md"
    alpha.write_text(alpha.read_text().replace("network: none", "network: loopback"))
    assert "*new* `no-install` `this-machine`" in rd.rebuild(PAGE, None)


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
                    "network": "none", "role": "words", "tags": "words"})  # fmt: skip
    (repo / "adapters" / "planned.json").write_text(json.dumps(planned))
    got = rd.section_languages(rd.addons())
    assert got.startswith("**2 built, 1 planned**")
    rows = [r for r in got.splitlines() if r.startswith("| `")]
    assert rows == [
        "| `cy` | [words-cy](adapters/stdlib/words-cy/) | Welsh common words. |",
        "| `tlh` | [words-tlh](adapters/stdlib/words-tlh/) | Klingon \\| words. |",
        "| `zh` | words-zh *(idea)* | Chinese. |",
    ]  # words-list isn't a language: only words- and a two- or three-letter code


def test_the_counts_stand_as_of_the_weeks_monday_and_its_own_line_is_now():
    """Every add-on pull request rewrote the counts, the newest and the
    week's draw, so any two conflicted: they stand as of the page's week now,
    and an add-on built since changes only its own line of the list."""
    every = [
        {"name": "old", "built": True, "added": "2026-11-02"},
        {"name": "new", "built": True, "added": "2026-11-04"},
        {"name": "idea", "built": False},
    ]
    got = {a["name"]: a["built"] for a in rd.as_of(every, "2026-W45")}
    assert got == {"old": True, "new": False, "idea": False}, (
        "Monday counts, Wednesday not yet"
    )
    assert {a["name"]: a["built"] for a in rd.as_of(every, "2026-W46")}["new"] is True
    assert every[1]["built"] is True, "as_of copies, never changes the list"
    page = "<!-- willow:pick week=2026-W45 -->x<!-- /willow:pick -->"
    assert (
        rd.week_of(page, None) == "2026-W45"
        and rd.week_of(page, "2026-W47") == "2026-W47"
    )
    assert rd.week_of("no week here", None) == rd.this_week()


# ── the week's tags and nearest entries ──────────────────────────────────────
def idea(name: str, line: str) -> dict:
    return {"name": name, "kind": "stdlib", "section": "Play", "line": line,
            "source": "new", "writes": "nothing", "network": "none", "role": "tools"}  # fmt: skip


def add_ideas(repo: Path, *more: dict) -> None:
    path = repo / "adapters" / "planned.json"
    path.write_text(json.dumps(json.loads(path.read_text()) + list(more)))


def line_of(repo: Path, name: str) -> str:
    """The entry in the list section (not the newest or the pick): its three
    lines, as one."""
    lines = (repo / "ADDONS.md").read_text().splitlines()
    at = next(i for i, x in enumerate(lines) if x.startswith(f'- <a id="{name}"></a>'))
    return "\n".join(lines[at : at + 3])


def test_the_weeks_first_write_keeps_each_entrys_topics_and_nearest(repo):
    assert rd.main(["write", "--week", "2026-W45"]) == 0
    kept = json.loads((repo / "week.json").read_text())
    assert kept["week"] == "2026-W45"
    assert set(kept["worked"]) == {"alpha", "beta", "gamma"}
    assert set(kept["worked"]["alpha"]) == {"topics", "near"}  # never its facts
    assert rd.main(["check"]) == 0


def test_another_entry_or_card_this_week_moves_no_other_line(repo):
    """What made every add-on pull request stale against every other: a new
    entry, or an edit to any card, moved other entries' tags and nearest
    entries, since they're worked out over the whole list."""
    assert rd.main(["write", "--week", "2026-W45"]) == 0
    before = {n: line_of(repo, n) for n in ("alpha", "beta", "gamma")}
    alpha = repo / "adapters" / "stdlib" / "alpha" / "README.md"
    alpha.write_text(alpha.read_text() + "\nbeta gamma later later somepkg words.\n")
    add_ideas(repo, idea("delta", "Gamma and beta, later, with somepkg."))
    assert rd.main(["write"]) == 0  # the page's week, still W45
    assert {n: line_of(repo, n) for n in ("beta", "gamma")} == {
        n: before[n] for n in ("beta", "gamma")
    }
    assert "**delta** (idea)" in line_of(repo, "delta")
    assert "delta" not in json.loads((repo / "week.json").read_text())["worked"]
    assert rd.main(["check"]) == 0


def test_a_new_entrys_line_is_its_own_whatever_else_is_new(repo):
    """Two pull requests each adding an entry: each one's line is worked out
    against the week's entries and itself, so merging both needs no write."""
    assert rd.main(["write", "--week", "2026-W45"]) == 0
    add_ideas(repo, idea("delta", "Later things, gamma-like."))
    assert rd.main(["write"]) == 0
    alone = line_of(repo, "delta")
    add_ideas(repo, idea("epsilon", "Later things, delta-like, gamma-like."))
    assert rd.main(["write"]) == 0
    assert line_of(repo, "delta") == alone


def test_the_counts_are_the_weeks_entries_and_a_new_one_counts_next_week(repo):
    assert rd.main(["write", "--week", "2026-W45"]) == 0
    pools = (repo / "ADDONS.md").read_text()
    add_ideas(repo, idea("delta", "Later."))
    assert rd.main(["write"]) == 0
    page = (repo / "ADDONS.md").read_text()
    assert "of 3 built" in pools and "of 3 built" in page, "delta counts from next week"
    assert rd.main(["write", "--week", "2026-W46"]) == 0
    assert "of 4 built" in (repo / "ADDONS.md").read_text()
    assert "delta" in json.loads((repo / "week.json").read_text())["worked"]


def test_a_cards_facts_and_own_tag_are_never_frozen(repo):
    """Install and online facts, and the author's own tag, are read from the
    card every time: a card going online is said the same day."""
    assert rd.main(["write", "--week", "2026-W45"]) == 0
    alpha = repo / "adapters" / "stdlib" / "alpha" / "README.md"
    alpha.write_text(alpha.read_text().replace("network: none", "network: loopback"))
    assert rd.main(["write"]) == 0
    assert "`this-machine`" in line_of(repo, "alpha")


def test_a_week_file_for_another_week_or_none_is_stale_to_check(repo, capsys):
    assert rd.main(["write", "--week", "2026-W45"]) == 0
    (repo / "week.json").unlink()
    assert rd.main(["check"]) == 2
    assert "week.json" in capsys.readouterr().out
    assert rd.main(["write"]) == 0 and rd.main(["check"]) == 0
    kept = json.loads((repo / "week.json").read_text())
    (repo / "week.json").write_text(json.dumps({**kept, "week": "2026-W44"}))
    assert rd.main(["check"]) == 2


def flat(text: str) -> str:
    """Text with its line breaks and wrapping indents as single spaces."""
    return " ".join(text.split())


def one(name, section, role, built=True):
    return {"name": name, "section": section, "line": f"{name} things.", "role": role,
            "built": built, "path": f"adapters/stdlib/{name}/", "kind": "stdlib",
            "network": "none", "source": "new"}  # fmt: skip


def test_a_section_is_cut_by_groups_py_built_first_and_each_entry_has_an_anchor():
    """Inside a section: a heading per role, in groups.py's order, or per
    group where the role has groups (readers by what they read); the built
    ones first, then the ideas under a heading of their own."""
    every = [
        one("zz-tool", "Reading more kinds of files", "tools"),
        one("mail", "Reading more kinds of files", "reads"),
        one("pdf", "Reading more kinds of files", "reads"),
        one("bank", "Reading more kinds of files", "reads"),
        one("aa-plan", "Reading more kinds of files", "reads", built=False),
    ]
    worked = {a["name"]: {"tags": [], "near": []} for a in every}
    text = rd.section_list(every, worked).split("## Reading more kinds of files", 1)[1]
    text = text.split("\n## ", 1)[0]
    heads = re.findall(r"^#{3,4} (.+)$", text, re.M)
    assert heads == ["Documents and office files", "Mail and chat",
                     "Exports from apps and services", "Other readers",
                     "Other readers: ideas, not built yet", "Tools you run yourself"]  # fmt: skip
    for n in ("pdf", "mail", "bank", "aa-plan", "zz-tool"):
        assert f'<a id="{n}"></a>' in text, n
    assert text.index('id="pdf"') < text.index('id="mail"') < text.index('id="bank"')


def test_the_real_list_is_every_add_on_once_under_a_heading():
    every = rd.addons()
    page = (rd.ROOT / "ADDONS.md").read_text(encoding="utf-8")
    listed = re.findall(r'^- <a id="([^"]+)"></a>', page.split("<!-- willow:list -->")[1], re.M)  # fmt: skip
    assert sorted(listed) == sorted(a["name"] for a in every)


def test_a_heading_with_more_than_a_screen_is_cut_a_to_z_and_says_where():
    """Three lines an entry: more than RUN under one heading would run past
    a screen, so it's cut into even runs, each heading saying its letters."""
    names = [f"{c}{i}" for c in "abcdefghij" for i in range(4)]  # 40, a to j
    every = [one(n, "Keeping track", "tools") for n in names]
    worked = {n: {"tags": [], "near": []} for n in names}
    text = rd.section_list(every, worked).split("## Keeping track", 1)[1].split("\n## ", 1)[0]  # fmt: skip
    heads = re.findall(r"^#{3,4} (.+)$", text, re.M)
    assert heads == ["Tools you run yourself, a to d", "Tools you run yourself, d to g",
                     "Tools you run yourself, g to j"]  # fmt: skip
    runs = re.split(r"^#{3,4} .+$", text, flags=re.M)[1:]
    assert [r.count('<a id="') for r in runs] == [13, 13, 14], "as even as they go"
    assert all(len(r.strip().splitlines()) <= rd.ROOM for r in runs)
    few = rd.section_list(every[: rd.RUN], worked)
    assert "### Tools you run yourself\n" in few and ", a to" not in few, (
        "not cut at RUN"
    )


def test_a_line_past_its_length_is_refused_and_one_at_it_kept(repo):
    """A card's or an idea's line is at most LINE, so the list reads in one look."""
    add_ideas(repo, idea("long", "x" * rd.LINE))
    assert "x" * rd.LINE in rd.rebuild(PAGE, None)
    add_ideas(repo, idea("longer", "y" * (rd.LINE + 1)))
    with pytest.raises(
        rd.Refused, match=f"141 characters, and a line is at most {rd.LINE}"
    ):
        rd.rebuild(PAGE, None)


def test_wrap_breaks_between_words_and_never_inside_a_link():
    link = "[a name with spaces](https://example.test/a/b)"
    assert rd.words_of(f"see {link}, then (and [x](y)) end") == [
        "see", f"{link},", "then", "(and", "[x](y))", "end"]  # fmt: skip
    text = " ".join(["word"] * 60) + f" {link}."
    lines = rd.wrap(text, "  ").splitlines()
    assert (
        all(len(x) <= rd.WIDTH and x.startswith("  ") for x in lines) and len(lines) > 1
    )
    assert lines[-1].endswith(f"{link}.") and flat(rd.wrap(text)) == text
    assert rd.wrap("short") == "short"


def test_the_real_add_on_list_reads_within_skims_bounds():
    """ADDONS.md held to how a person reads it: a heading every screen, no
    line past a look, every add-on an anchor (adapters/stdlib/skim)."""
    skim = rd.ROOT / "adapters" / "stdlib" / "skim" / "skim.py"
    got = subprocess.run([sys.executable, str(skim), "check", str(rd.ROOT / "ADDONS.md")],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 0, got.stdout + got.stderr
