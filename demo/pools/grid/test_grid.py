"""grid.py: every stack written from the cards and tables, the same bytes each
time, each one a stack stack.py reads, its draws the plan's and not a
session's."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
GRID = HERE / "grid.py"
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "adapters" / "stdlib" / "stack"))
import grid  # noqa: E402
import stack  # noqa: E402


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(GRID), *map(str, argv)], capture_output=True,
                          text=True, stdin=subprocess.DEVNULL)  # fmt: skip


@pytest.fixture(scope="module")
def made(tmp_path_factory):
    to = tmp_path_factory.mktemp("grid") / "out"
    got = run("write", "--to", to)
    assert got.returncode == 0, got.stderr
    return to, json.loads((to / "manifest.json").read_text())


def test_the_same_sources_write_the_same_bytes(made, tmp_path):
    to, _ = made
    again = tmp_path / "again"
    assert run("write", "--to", again).returncode == 0

    def files(d: Path) -> dict[str, bytes]:
        return {
            p.relative_to(d).as_posix(): p.read_bytes()
            for p in d.rglob("*")
            if p.is_file()
        }

    assert files(to) == files(again)


def test_every_stack_is_one_stack_reads_and_its_hash_is_the_manifests(made):
    to, m = made
    names = set()
    for row in m["stacks"]:
        text = (to / "stacks" / f"{row['id']}.md").read_text()
        assert hashlib.sha256(text.encode()).hexdigest() == row["sha256"]
        pools, why = stack.parse_stack(text)
        assert why is None, (row["id"], why)
        assert [n for n, _ in pools[0][1]] == row["steps"], (
            "the listed order is the running order"
        )
        names |= set(row["steps"])
    assert all(stack.resolve(n) is not None for n in names), (
        "each step's add-on is there"
    )


def test_each_way_has_the_rows_the_plan_and_the_tables_give(made):
    _, m = made
    plan, n = m["plan"], len(m["steps"])
    ways = m["ways"]
    assert ways["single"] == ways["all-but-one"] == ways["near"] == n
    assert ways["all"] == 1 + plan["all_shuffles"]
    assert ways["random"] == len(plan["random_sizes"]) * plan["random_draws"]
    assert ways["bridge"] == len(m["bridges"])
    by_id = {r["id"]: r for r in m["stacks"]}
    for size in plan["random_sizes"]:
        assert len(by_id[f"random/{size}-0"]["steps"]) == size
    every = by_id["all/in-name-order"]["steps"]
    assert every == sorted(m["steps"])
    for k in range(plan["all_shuffles"]):
        shuffled = by_id[f"all/shuffle-{k}"]["steps"]
        assert sorted(shuffled) == every and shuffled != every
    assert all(
        len(by_id[f"all-but-one/{s}"]["steps"]) == n - 1 for s in ("stack", "kart")
    )


def test_the_draws_are_the_plans_seed_and_nothing_else(made):
    _, m = made
    plan = dict(m["plan"], seed=m["plan"]["seed"] + 1)
    card, mod = grid.cards(), grid.contract()
    step = grid.steps(mod)
    other = grid.grid(plan, card, step, {}, [])
    mine = {r["id"]: r["steps"] for r in m["stacks"] if r["way"] == "random"}
    theirs = {r["id"]: r["steps"] for r in other if r["way"] == "random"}
    assert mine.keys() == theirs.keys() and mine != theirs, "another seed, other draws"


def test_bridges_come_from_the_record_and_the_cards_and_the_giver_runs_first(made):
    _, m = made
    kinds = {why.split(":")[0] for b in m["bridges"] for why in b["by"]}
    assert kinds == {"record", "card"}
    assert {
        "from": "advisories",
        "to": "outdated",
        "by": ["card: outdated's uses"],
    } in m["bridges"]
    by_id = {r["id"]: r for r in m["stacks"]}
    both = {(b["from"], b["to"]): b["by"] for b in m["bridges"]}
    assert both[("dice", "game-master")] == [
        "card: game-master's uses",
        "record: roll rows",
    ]
    assert len(both) == len(m["bridges"]), "one bridge a pair, its reasons listed"
    for b in m["bridges"]:
        assert by_id[f"bridge/{b['from']}--{b['to']}"]["steps"] == [
            b["from"],
            b["to"],
        ]


def test_the_cards_with_no_step_are_the_ones_no_table_runs_over_a_pile(made):
    _, m = made
    mod = grid.contract()
    assert set(m["no_step"]) == set(mod.DEPS_TAKES) | {
        "ci",
        "github",
        "mutants",
        "readme",
        "similar",
    }


def test_fill_puts_in_one_pile_and_a_folder_for_each_step(made, tmp_path):
    to, _ = made
    pile, tmp = tmp_path / "pile", tmp_path / "tmp"
    pile.mkdir()
    tmp.mkdir()
    out = tmp_path / "filled.md"
    assert run("fill", "--stack", to / "stacks" / "single" / "backup.md", "--pile", pile,
               "--tmp", tmp, "--to", out).returncode == 0  # fmt: skip
    text = out.read_text()
    assert "{tmp}" not in text and "{pile}" not in text and "{box}" in text
    assert f"{tmp.resolve()}/backup/backups" in text and (tmp / "backup").is_dir()
    got = run("fill", "--stack", to / "stacks" / "single" / "backup.md", "--pile", pile,
              "--tmp", tmp, "--to", out)  # fmt: skip
    assert got.returncode == 2 and "is there already" in got.stderr


def test_a_bad_command_line_or_a_full_folder_is_refused(tmp_path):
    for argv in (
        [],
        ["write"],
        ["write", "--to"],
        ["fill", "--stack", "x"],
        ["go", "--to", tmp_path],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "grid.py write" in got.stderr
    (tmp_path / "full").mkdir()
    (tmp_path / "full" / "x").write_text("x")
    got = run("write", "--to", tmp_path / "full")
    assert got.returncode == 2 and "isn't an empty folder" in got.stderr


def test_record_bridges_reach_each_reader_from_any_step_that_adds_rows(made):
    _, m = made
    rec, static = m["record_bridges"], json.loads(grid.STATIC.read_text())
    assert rec["by"].startswith("record:")
    assert rec["readers"] == sorted(
        n for n in m["steps"] if static.get(n, {}).get("reads_record")
    )
    for n in rec["givers"]:
        s = static.get(n, {})
        assert (
            "bite" in m["steps"][n]["args"]
            or s.get("writes")
            or s.get("writes_unread")
            or s.get("bites")
        ), n
    # the ten the trace saw change in the stack of all 351 read the record
    for n in "again cloudevents forecasts game-master nightstand predict prov sent-log three-two-one".split():
        assert n in rec["readers"], n
    # too wide for stacks of their own: the bridge rows are the bridges'
    assert sum(r["way"] == "bridge" for r in m["stacks"]) == len(m["bridges"])


def test_the_kind_stacks_are_a_stage_0_writer_then_each_reader_of_the_record(made):
    _, m = made
    kinds = [r for r in m["stacks"] if r["way"] == "kind"]
    writers, readers = m["kind_writers"], set(m["record_bridges"]["readers"])
    assert kinds and len(kinds) == sum(len(readers - {w}) for w in writers)
    for r in kinds:
        w, reader = r["steps"]
        assert w in writers and reader in readers and reader != w
    assert "stage0" in m["sources"], (
        "the writers are read from stage 0's committed rows"
    )
    assert writers == grid.kind_writers(grid.STAGE0)
