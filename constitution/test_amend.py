"""amend.py: the law is always a draft (CONST-VIII-4), and Article 0 is beyond
the reach of any amendment (CONST-VIII-3).

Each test attempts a way the law and its amendments could drift apart, on a
copy, and checks that it is refused: Article 0 or the Preamble touched, the
record before the first amendment edited, an amendment's text not in the law,
a draft number skipped, an amendment that names an Article 0 clause. One
amendment superseding another keeps both.
"""

from __future__ import annotations

import importlib.util
import shutil
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("willow_amend", HERE / "amend.py")
am = importlib.util.module_from_spec(spec)
spec.loader.exec_module(am)

LAW = am.LAW.read_text(encoding="utf-8")
EVERY = am.amendments()
LATEST = EVERY[-1]["draft"]


@pytest.fixture
def folder(tmp_path) -> Path:
    """A copy of the amendments, made with tempfile so the guard knows it as
    this test's scratch."""
    where = Path(tempfile.mkdtemp(dir=tmp_path)) / "amendments"
    shutil.copytree(am.AMENDMENTS, where)
    return where


def test_the_real_law_holds():
    assert am.problems() == []
    assert am.main(["check"]) == 0


def test_write_changes_nothing_on_a_law_that_holds():
    assert am.build(LAW, am.amendments()) == LAW


@pytest.mark.parametrize(
    "old, new, says",
    [
        # CONST-VIII-3: Article 0 and the Preamble are fixed
        ("outside the amendment mechanism entirely", "outside the amendment mechanism",
         "Article 0 has changed"),
        ("To these six we bind ourselves", "To these six we bind",
         "the Preamble has changed"),
        # the record before the first amendment here is kept, never edited
        ("Draft 0.3 — three AI reviews", "Draft 0.3 — four AI reviews",
         "rows before the first amendment"),
        ("0.2 (body framed, DeepSeek)", "0.2 (body framed)", "lineage up to 0.9"),
        # CONST-VIII-4: each amendment makes the next draft, and says so; and
        # CONST-VIII-1: it takes effect only upon recording, its row and text
        (f"> Draft {LATEST}. ", "> Draft 0.9. ", "aren't what the amendments make"),
        ("*draft — by merge of #4* |", "*ratified* |", "aren't what the amendments make"),
        ("This constitution is never closed.", "This constitution is closed.",
         "isn't in CONSTITUTION.md word for word"),
    ],
)  # fmt: skip
def test_each_way_the_law_can_drift_from_its_amendments_is_refused(old, new, says, folder):  # fmt: skip
    assert old in LAW, f"the plant's anchor {old!r} is gone from CONSTITUTION.md"
    got = am.problems(LAW.replace(old, new, 1), folder)
    assert got and any(says in p for p in got), got


@pytest.mark.parametrize(
    "old, new, says",
    [
        ("draft: 0.10", "draft: 0.11", "the next draft is 0.10"),
        # CONST-VIII-3: no amendment may name an Article 0 clause
        ("clauses: CONST-VIII-4", "clauses: CONST-0-4", "Article 0 is beyond reach"),
        ("clauses: CONST-VIII-4", "clauses: CONST-VIII-2", "its text holds"),
        ("pr: 4\n", "", "missing pr"),
        ("date: 2026-10-24", "date: today", "date is YYYY-MM-DD"),
        ("pr: 4\n", "pr: 4\nsupersedes: 0001\n", "supersedes only amendments before it"),
        ("summary: VIII.4", "summary: | VIII.4", "has no | or →"),
        ("<!-- willow-amendment", "<!-- amendment", "willow-amendment header"),
    ],
)  # fmt: skip
def test_an_amendment_that_doesnt_hold_together_is_refused(old, new, says, folder):
    first = folder / "0001.md"
    text = first.read_text(encoding="utf-8")
    assert old in text, f"the plant's anchor {old!r} is gone from 0001.md"
    first.write_text(text.replace(old, new, 1), encoding="utf-8")
    got = am.problems(LAW, folder)
    assert got and any(says in p for p in got), got


def test_amendments_are_numbered_in_turn(folder):
    (folder / "0001.md").unlink()
    assert any("should be 0001.md" in p for p in am.problems(LAW, folder))


def test_a_later_amendment_supersedes_an_earlier_and_both_stay(folder):
    """CONST-VIII-4: nothing leaves the record. The second amendment rewrites
    VIII.4; the first one's text leaves the law, its file and its row stay."""
    first = (folder / "0001.md").read_text(encoding="utf-8")
    old = first.split("-->\n", 1)[1].strip()
    new = old.replace("This constitution is never closed.",
                      "This constitution is never closed, and says so.")  # fmt: skip
    n, draft = len(EVERY) + 1, am.next_draft(LATEST)
    (folder / f"{n:04d}.md").write_text(
        first.replace("draft: 0.10", f"draft: {draft}")
        .replace("pr: 4\n", "pr: 99\nsupersedes: 0001\n")
        .replace("summary: VIII.4,", "summary: VIII.4 restated,")
        .replace(old, new),
        encoding="utf-8",
    )
    law = am.build(LAW.replace(old, new), am.amendments(folder))
    assert am.problems(law, folder) == []
    assert f"> Draft {draft}. " in law and old not in law
    rows = [r for r in am.history(law) if "by merge of #" in r]
    assert len(rows) == n and rows[0].split(" | ")[2].startswith("Draft 0.10 — VIII.4,")
    assert rows[-1].endswith("*draft — by merge of #99* |")
    assert " → 0.10 (VIII.4, always" in law and f" → {draft} (VIII.4 restated," in law
    (folder / f"{n:04d}.md").unlink()  # with it gone, the law it made no longer holds
    assert am.problems(law, folder)


def test_with_no_amendments_the_law_is_the_draft_that_came_from_grove(folder):
    for f in folder.glob("*.md"):
        f.unlink()
    law = am.build(LAW, am.amendments(folder))
    assert "> Draft 0.9. " in law and "by merge of #" not in law
    assert am.problems(law, folder) == []


@pytest.mark.parametrize("argv", [[], ["checks"], ["check", "x"]])
def test_a_bad_command_line_is_refused(argv):
    assert am.main(argv) == 2


# ── emergency amendments (CONST-VIII-2) ──────────────────────────────────────
VIII4 = next(a for a in EVERY if a["clauses"] == ["CONST-VIII-4"])["body"]


def add(folder: Path, expires: str = "", supersedes: str = "", date: str = "2026-10-24") -> int:  # fmt: skip
    """The next amendment: VIII.4 restated as it stands, so the law's text
    holds it, optionally an emergency one."""
    every = am.amendments(folder)
    n, draft = len(every) + 1, am.next_draft(every[-1]["draft"])
    head = [f"draft: {draft}", f"date: {date}", "pr: 99", "articles: VIII",
            "clauses: CONST-VIII-4", f"summary: amendment {n}"]  # fmt: skip
    head += [f"expires: {expires}"] * bool(expires) + [f"supersedes: {supersedes}"] * bool(supersedes)  # fmt: skip
    body = "<!-- willow-amendment\n" + "\n".join(head) + "\n-->\n" + VIII4 + "\n"
    (folder / f"{n:04d}.md").write_text(body, encoding="utf-8")
    return n


def test_an_emergency_amendment_stands_until_its_date_then_stops_the_checks(folder):
    """CONST-VIII-2: the emergency door closes on a timer, and nothing restores
    the law on its own, so after its date the checks refuse until a person acts."""
    add(folder, expires="2026-11-01")
    law = am.build(LAW, am.amendments(folder))
    assert "*(emergency, expires 2026-11-01)*" in law
    assert am.problems(law, folder, today="2026-11-01") == []
    got = am.problems(law, folder, today="2026-11-02")
    assert any("expired 2026-11-01" in p for p in got), got


def test_a_full_amendment_that_names_it_keeps_or_undoes_it(folder):
    n = add(folder, expires="2026-11-01")
    add(folder, supersedes=f"{n:04d}")
    law = am.build(LAW, am.amendments(folder))
    assert am.problems(law, folder, today="2027-06-01") == []


def test_an_emergency_amendment_cant_renew_itself(folder):
    """CONST-VIII-2: it may never renew itself; only a full amendment keeps it."""
    n = add(folder, expires="2026-11-01")
    add(folder, expires="2026-12-01", supersedes=f"{n:04d}")
    assert any("can't renew another" in p for p in am.problems(LAW, folder))


@pytest.mark.parametrize(
    "expires, says",
    [
        ("2026-10-24", "expires after its date and within 90 days"),
        ("2027-01-23", "expires after its date and within 90 days"),
        ("soon", "expires is YYYY-MM-DD"),
    ],
)
def test_an_emergency_amendment_states_a_date_within_the_bound(folder, expires, says):
    add(folder, expires=expires)
    assert any(says in p for p in am.problems(LAW, folder)), am.problems(LAW, folder)


def test_ninety_days_on_is_within_the_bound(folder):
    add(folder, expires="2027-01-22")
    law = am.build(LAW, am.amendments(folder))
    assert am.problems(law, folder, today="2026-10-25") == []
