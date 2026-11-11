"""demo/homestead-health: the pile is six repositories each at one whole
commit, the recipe names no other, and what the first asks kept is what
the page says of them."""

from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def test_the_pile_is_six_repositories_each_at_one_whole_commit():
    sources = json.loads((HERE / "sources.json").read_text())["sources"]
    assert len(sources) == 6 and len({s["as"] for s in sources}) == 6
    for s in sources:
        assert s["address"] == f"https://github.com/homestead-affairs/{s['name']}"
        assert re.fullmatch(r"[0-9a-f]{40}", s["commit"])
        assert not s["as"].startswith("."), "a hidden folder is not walked as a pile"
    script = (HERE / "rebuild.sh").read_text()
    assert "sources.json" in script and "github.com" not in script
    assert "refused: SCRATCH is inside the repository" in script


def test_the_first_asks_kept_are_what_the_page_says_of_them():
    asked = [q for q in (HERE / "questions.txt").read_text().splitlines() if q]
    rows = [r.split("  |  ") for r in (HERE / "results" / "asks.txt").read_text().splitlines()]  # fmt: skip
    assert [r[0] for r in rows] == asked and len(asked) == 12
    assert [r[0] for r in rows if r[1] == "empty"] == [
        "break glass access in an emergency"
    ]
    assert sum(1 for r in rows if r[1] == "populated") == 11
    card = next(r for r in rows if r[0] == "what is on the emergency card")
    assert card[2].startswith("homestead/docs/PLAN-homestead-health.md:")
    kept = json.loads((HERE / "KEPT.json").read_text())["files"]
    assert kept == ["results/asks.txt"]
    page = (HERE / "README.md").read_text()
    assert "397 files" in page and "Eleven were served" in page
