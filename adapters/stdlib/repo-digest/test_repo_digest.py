"""repo-digest: a ring is found once and named with what rests on it, a
uses that leads nowhere is said, each add-on's step is one above the
highest it uses, what nothing declares and what waits are counted, and
only what is wrong ends 42."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCRIPT = HERE / "repo_digest.py"
sys.path.insert(0, str(HERE))
import repo_digest  # noqa: E402


def card(uses: str = "") -> str:
    return (
        "<!-- willow-addon\nline: a thing\n"
        + (f"uses: {uses}\n" if uses else "")
        + "-->\n# x\n"
    )


def addons(**uses: str) -> dict[str, str]:
    """A tree of add-ons, each a card with this `uses` line and one script."""
    tree = {}
    for name, line in uses.items():
        tree[f"adapters/stdlib/{name}/README.md"] = card(line)
        tree[f"adapters/stdlib/{name}/{name}.py"] = ""
    return tree


def make(root: Path, tree: dict[str, str]) -> Path:
    for rel, text in tree.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(root), "init", "-q"], check=True, capture_output=True
    )
    return root


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, text=True)  # fmt: skip


def doc_of(root: Path) -> tuple[dict, int]:
    got = run("page", "--json", "--root", str(root))
    return json.loads(got.stdout), got.returncode


def rows(doc: dict, opens: str) -> dict[str, str]:
    for g in doc["groups"]:
        if g["name"].startswith(opens):
            return {r["where"]: r["what"] for r in g["rows"]}
    return {}


CHAIN = dict(a="", b="a", c="b, a", d="c", e="", f="e")


def test_each_add_ons_step_is_one_above_the_highest_it_uses():
    uses = {k: [u.strip() for u in v.split(",") if u.strip()] for k, v in CHAIN.items()}
    steps = repo_digest.steps_up(uses)
    assert steps == {"a": 0, "b": 1, "c": 2, "d": 3, "e": 0, "f": 1}
    assert repo_digest.way_down(uses, steps, "d") == ["d", "c", "b", "a"]
    assert repo_digest.way_down(uses, steps, "e") == ["e"]
    assert repo_digest.rings(uses) == []


def test_a_ring_is_found_once_and_what_rests_on_it_has_no_step():
    uses = {
        "a": ["b"],
        "b": ["c"],
        "c": ["a"],
        "d": ["a"],
        "e": [],
        "f": ["e", "d"],
        "g": ["g"],
    }
    assert repo_digest.rings(uses) == [("a", "b", "c"), ("g",)]
    steps = repo_digest.steps_up(uses)
    assert steps == {
        "a": None,
        "b": None,
        "c": None,
        "d": None,
        "e": 0,
        "f": None,
        "g": None,
    }
    two = {"m": ["n"], "n": ["m"], "x": ["y"], "y": ["x"], "z": []}
    assert repo_digest.rings(two) == [("m", "n"), ("x", "y")]
    assert (
        repo_digest.steps_up({"p": ["q"], "q": ["r"], "r": ["q"], "s": ["p"]})["s"]
        is None
    )


def test_the_page_gives_the_order_the_longest_way_down_and_the_most_built_on(tmp_path):
    doc, code = doc_of(make(tmp_path, addons(**CHAIN)))
    assert code == 0, "nothing wrong waits: every file is a card or code"
    assert doc["said"] == (
        "0 files nothing declares, 0 rings in what uses what, 0 ideas waiting; "
        "6 add-ons build 3 steps deep"
    )
    assert rows(doc, "the order") == {
        "on the kernel alone": "2 add-ons",
        "1 step up": "2 add-ons: b, f",
        "2 steps up": "1 add-on: c",
        "3 steps up": "1 add-on: d",
        "the longest way down": "d → c → b → a",
    }
    assert rows(doc, "most built on") == {
        "a": "2 add-ons use it", "b": "1 add-on uses it", "c": "1 add-on uses it",
        "e": "1 add-on uses it"}  # fmt: skip
    assert list(rows(doc, "most built on")) == ["a", "b", "c", "e"], (
        "most first, then A to Z"
    )
    assert [g["name"].split(":")[0] for g in doc["groups"]] == [
        "the order they build in",
        "most built on",
    ]


def test_a_ring_and_a_uses_that_leads_nowhere_are_said_and_end_42(tmp_path):
    tree = addons(a="b", b="a", c="a", d="", e="ghost, d")
    doc, code = doc_of(make(tmp_path, tree))
    assert code == 42
    assert rows(doc, "a ring") == {
        "a → b → a": "each needs the other beside it; 1 add-on rests on it: c"
    }
    assert rows(doc, "uses one that isn't here") == {
        "e": "uses ghost, and no add-on here is called that"
    }
    assert rows(doc, "the order") == {
        "on the kernel alone": "1 add-on",
        "1 step up": "1 add-on: e",
        "the longest way down": "e → d",
    }
    assert (
        "1 ring in what uses what" in doc["said"]
        and "5 add-ons build 1 step deep" in doc["said"]
    )
    only_ring = tmp_path / "ring"
    only_ring.mkdir()
    assert doc_of(make(only_ring, addons(a="b", b="a")))[1] == 42
    only_ghost = tmp_path / "ghost"
    only_ghost.mkdir()
    assert doc_of(make(only_ghost, addons(a="ghost")))[1] == 42


def test_what_nothing_declares_ends_42_and_what_only_waits_does_not(tmp_path):
    waits = {
        **addons(a=""),
        "towncrier.toml": '[tool.towncrier]\ndirectory = "changes"\nfilename = "CHANGELOG.md"\n',
        "CHANGELOG.md": "# changes\n",
        "changes/1.added.md": "a\n",
        "changes/2.fixed.md": "b\n",
        "adapters/planned.json": json.dumps(
            [
                {"name": "zed", "section": "Play"},
                {"name": "ant", "section": "Play"},
                {"name": "bee", "section": "Trust"},
                {"name": "cat"},
                {"section": "Play"},
                "junk",
            ]
        ),  # fmt: skip
    }
    doc, code = doc_of(
        make(tmp_path / "w" if (tmp_path / "w").mkdir() is None else tmp_path, waits)
    )
    assert rows(doc, "nothing declares") == {
        "(top level)": "1 file, such as towncrier.toml"
    }
    assert code == 42, "towncrier.toml has no kind"
    assert rows(doc, "ideas waiting") == {
        "Play": "2 ideas, such as ant", "(no section)": "1 idea, such as cat", "Trust": "1 idea, such as bee"}  # fmt: skip
    assert rows(doc, "entries waiting") == {
        "the changelog": "2 entries not yet in a release"
    }
    assert "4 ideas waiting" in doc["said"] and "1 file nothing declares" in doc["said"]
    calm = tmp_path / "calm"
    calm.mkdir()
    tree = {
        **addons(a=""),
        "adapters/planned.json": json.dumps([{"name": "x", "section": "Play"}]),
    }
    doc, code = doc_of(make(calm, tree))
    assert code == 0 and "1 idea waiting" in doc["said"], (
        "an idea waiting is not a fault"
    )
    assert rows(doc, "entries waiting") == {}


def test_only_uses_is_read_and_only_from_a_card(tmp_path):
    tree = addons(a="", b="a")
    tree["adapters/stdlib/b/README.md"] = card("a").replace(
        "-->", "looks-for: zzz\n-->"
    )
    tree["adapters/stdlib/c/README.md"] = "# no card header\nuses: a\n"
    tree["adapters/stdlib/d/README.md"] = card("") + "\nuses: ghost\n"
    files = repo_digest.kinds.tracked(make(tmp_path, tree))
    assert repo_digest.uses_of(tmp_path, files) == {"a": [], "b": ["a"], "d": []}


def test_a_long_row_names_eight_and_counts_the_rest():
    assert repo_digest.names(list("abc")) == "a, b, c"
    assert repo_digest.names([str(n) for n in range(8)]) == "0, 1, 2, 3, 4, 5, 6, 7"
    assert (
        repo_digest.names([str(n) for n in range(11)])
        == "0, 1, 2, 3, 4, 5, 6, 7, and 3 more"
    )
    assert repo_digest.count(1, "entry", "entries") == "1 entry"
    assert (
        repo_digest.count(2, "entry", "entries") == "2 entries"
        and repo_digest.count(0, "ring") == "0 rings"
    )


def test_the_text_is_the_report_its_json_holds(tmp_path):
    root = make(tmp_path, addons(**CHAIN))
    doc, _ = doc_of(root)
    text = run("page", "--root", str(root)).stdout
    assert text == repo_digest.report_text(doc) + "\n"
    assert text.splitlines()[0] == f"repo-digest: populated, {doc['said']}"


@pytest.mark.parametrize(
    "argv,said",
    [
        ([], "usage: repo_digest.py page"),
        (["--json"], "usage: repo_digest.py page"),
        (["count"], "usage: repo_digest.py page"),
        (["page", "kernel.py"], "usage: repo_digest.py page"),
        (["page", "--nope"], "usage: repo_digest.py page"),
        (["page", "--root"], "--root with no folder is not a folder"),
        (["page", "--root", "{root}/absent"], "is not a folder"),
    ],
)
def test_a_bad_command_line_is_refused_and_says_why(tmp_path, argv, said):
    got = run(*[a.replace("{root}", str(tmp_path)) for a in argv])
    assert got.returncode == 2 and said in got.stderr and got.stdout == ""


def test_a_folder_git_does_not_know_is_unreachable_and_an_empty_repo_is_empty(tmp_path):
    (tmp_path / "x.txt").write_text("")
    got = run("page", "--json", "--root", str(tmp_path))
    doc = json.loads(got.stdout)
    assert (
        got.returncode == 42 and doc["state"] == "unreachable" and doc["groups"] == []
    )
    empty = tmp_path / "empty"
    empty.mkdir()
    doc, code = doc_of(make(empty, {}))
    assert code == 0 and doc["state"] == "empty"


def test_on_this_repo_the_page_has_its_groups_and_every_add_on_is_placed_or_in_a_ring():
    got = run("page", "--json")
    doc = json.loads(got.stdout)
    assert doc["state"] == "populated"
    order = rows(doc, "the order")
    placed = sum(
        int(what.split()[0])
        for where, what in order.items()
        if where != "the longest way down"
    )
    resting = 0
    for where, what in rows(doc, "a ring").items():
        resting += len(where.split(" → ")) - 1
        resting += int(what.split("; ")[1].split()[0]) if "; " in what else 0
    files = repo_digest.kinds.tracked(ROOT)
    assert placed + resting == len(repo_digest.uses_of(ROOT, files))
    chain = order["the longest way down"].split(" → ")
    assert len(chain) == max(int(w.split()[0]) for w in order if w[0].isdigit()) + 1
    assert rows(doc, "uses one that isn't here") == {}, (
        "a uses line names an add-on that is not built"
    )


def test_it_writes_nothing(tmp_path):
    root = make(tmp_path, addons(**CHAIN))
    before = sorted(str(p) for p in root.rglob("*") if ".git" not in p.parts)
    run("page", "--root", str(root))
    assert sorted(str(p) for p in root.rglob("*") if ".git" not in p.parts) == before


def test_the_most_built_on_are_five_the_most_used_first(tmp_path):
    tree = addons(
        a="",
        b="",
        c="",
        d="",
        e="",
        z="",
        p="z",
        q="z",
        r="z, a",
        s="b",
        t="c",
        u="d",
        v="e",
    )
    doc, _ = doc_of(make(tmp_path, tree))
    most = rows(doc, "most built on")
    assert list(most) == ["z", "a", "b", "c", "d"], (
        "the most used first, then A to Z, and five"
    )
    assert most["z"] == "3 add-ons use it" and most["a"] == "1 add-on uses it"
