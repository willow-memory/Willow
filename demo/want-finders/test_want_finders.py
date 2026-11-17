"""demo/want-finders: what was frozen stays frozen, every right card is a card
here, the hit rule says what its docstring says, and a dry run puts its
verdicts on a box and nowhere else. The scored runs are in results/; CI holds
what they stand on, not their numbers."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import score  # noqa: E402

FROZEN = json.loads((HERE / "FROZEN.json").read_text(encoding="utf-8"))


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "kernel.py"), *argv], capture_output=True, text=True
    )


def test_every_frozen_file_is_as_it_was_frozen():
    for rel, sha in FROZEN["files"].items():
        got = hashlib.sha256((HERE / rel).read_bytes()).hexdigest()
        assert got == sha, (
            f"{rel} changed after it was frozen; a change is a new freeze"
        )
    assert {"wants.json", "score.py"} <= set(FROZEN["files"])


def test_every_right_card_is_a_card_here():
    """A card renamed or gone under a frozen want is said here, so the score
    never counts a miss against a name nothing can offer."""
    for w in score.read_wants():
        for name in w["right"]:
            cards = [
                ROOT / "adapters" / kind / name / "README.md"
                for kind in ("stdlib", "deps")
            ]
            assert any(c.is_file() for c in cards), f"{w['id']}: no card named {name}"


def test_the_wants_hold_together():
    wants = score.read_wants()
    assert len({w["id"] for w in wants}) == len(wants)
    assert any(not w["right"] for w in wants), "one want no card here answers"


@pytest.mark.parametrize(
    "doc",
    [
        {"wants": []},
        {"wants": [{"id": "A", "want": " ", "right": []}]},
        {"wants": [{"id": "A", "want": "x", "right": "mail"}]},
        {
            "wants": [
                {"id": "A", "want": "x", "right": []},
                {"id": "A", "want": "y", "right": []},
            ]
        },
    ],
)
def test_wants_that_dont_hold_together_are_refused(tmp_path, doc):
    f = tmp_path / "wants.json"
    f.write_text(json.dumps(doc))
    with pytest.raises(ValueError):
        score.read_wants(f)


def test_the_hit_rule():
    assert score.hits(["a", "b"], ["b"], 2) and not score.hits(["a", "b"], ["b"], 1)
    assert score.hits(["b"], ["a", "b"], 1), "any right card is a hit"
    assert score.hits([], [], 5) and not score.hits(["a"], [], 5), (
        "none right, none offered"
    )
    assert not score.hits([], ["a"], 5)
    assert score.rank(["x", "a"], ["a"]) == 2 and score.rank(["x"], ["a"]) is None


def row(name: str) -> dict:
    """A report row as suggest writes one for a card."""
    return {
        "where": f"adapters/stdlib/{name}/README.md",
        "what": f"{name}: a line (writes nothing)",
    }


def test_a_suggest_report_is_read_as_its_offers():
    """What the dry run can't reach: nonsense is offered nothing, so the
    reading of a real report is held here, on suggest's own shape."""
    doc = {
        "addon": "forge",
        "state": "populated",
        "said": "1 fork waits on you",
        "groups": [
            {"name": "steps", "rows": [row("stack")]},
            {"name": "fork “email”", "rows": [row("apple-mail"), row("mail")]},
            {
                "name": "stale seals, asked again",
                "rows": [
                    {
                        "where": "forge/decisions/willow-due.json",
                        "what": "renewals no longer does “due” here (row 4)",
                    }
                ],
            },
            {"name": "ideas", "rows": [row("email-ask"), row("mail")]},
        ],
    }
    assert score.offers(doc) == ["stack", "apple-mail", "mail", "email-ask"]
    many = {"groups": [{"name": "steps", "rows": [row(f"a{i}") for i in range(9)]}]}
    assert len(score.offers(many)) == score.TOP


def test_a_dry_run_puts_its_verdicts_on_the_box(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.txt").write_text("nothing here\n")
    box = tmp_path / "box"
    assert (
        k(
            "init", "--box", str(box), "--pile", str(pile), "--key", str(tmp_path / "k")
        ).returncode
        == 0
    )
    got = subprocess.run(
        [
            sys.executable,
            str(HERE / "score.py"),
            "run",
            "--box",
            str(box),
            "--dry",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert got.returncode == 0, got.stderr
    out = json.loads(got.stdout)
    rows = [json.loads(ln) for ln in (box / "record.jsonl").read_text().splitlines()]
    verdicts = [r for r in rows if r["kind"] == "verdict"]
    assert [r["n"] for r in verdicts] == out["rows"]
    assert {r["rule"] for r in verdicts} == {
        f"want-finders:dry:{rule}:{name}"
        for rule in score.RULES
        for name in score.SOURCES
    }
    for r in verdicts:
        assert r["state"] in ("scored", "unreachable") and r["standing"] == "unattested"
        assert (
            r["wants_sha256"]
            == hashlib.sha256((HERE / "wants.json").read_bytes()).hexdigest()
        )
        if r["state"] == "unreachable":
            assert r["hits"] == 0, "unreachable never reads as a pass"
    assert k("verify", "--box", str(box)).returncode == 0


def test_a_folder_that_isnt_a_box_is_refused(tmp_path):
    got = subprocess.run(
        [sys.executable, str(HERE / "score.py"), "run", "--box", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert got.returncode == 2 and "not a box" in got.stderr
