"""changes.py: what the stacks change, measured against the same run.

    python demo/pools/truth/changes.py measure --run DIR... --grid MANIFEST... --to RESULT
    python demo/pools/truth/changes.py report  --result RESULT --to REPORT

Written after the first report (demo/pools/README.md, "What failed"), and
said so. truth.py's measures stand as frozen; these are the ones that
report said were missing:

- **The baseline is the same run's.** Each DIR is one run on one pile (a
  notebook): its `rows-alone.jsonl` (every step alone, that day, that
  machine), its `rows-empty.jsonl` (every step alone on an empty pile), and
  its stacks' rows. A step in a stack is held to its own run's alone row,
  so the day and the machine drop out.
- **Fired means more than printed.** A step fired on a pile when, by
  truth.py's rule, it fired, and what it printed differs from what it
  printed on an empty pile.
- **Bridges held.** In each bridge stack (giver, then taker), the taker
  changed or not, against the seeded no-bridge pairs (each first step, then
  second): the two rates and a one-sided Fisher exact p.
- **Kinds.** In each kind stack (a step that writes kinds of row, then a
  reader of the record), the reader changed or not; with the content groups
  of the rows the writer added (trace.py's row_groups), so a reader is tied
  to which rows moved it, not just their kind.
- **Pools.** Steps joined when one changed the other, in a held bridge or a
  kind stack: the connected groups.

A step unsteady alone (it differs between its alone row and its single
stack's) is never held to anything. Nor is a row from another UTC day than
its step's alone row: midnight can fall inside one run.

Exit codes, the kernel's: 0 done; 2 refused (a bad command line, a file that
isn't there).
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path


def fires(r: dict) -> bool:
    """truth.py's rule: exit 0 or 42, not timed out, nothing breached, and a
    report populated or, with no report state, a line printed."""
    return (r.get("exit") in (0, 42) and not r.get("timed_out") and not r.get("breaches")
            and (r.get("state") == "populated" or (r.get("state") is None and r.get("lines", 0) > 0)))  # fmt: skip


def _load(path: Path) -> list[dict]:
    return (
        [
            json.loads(x)
            for x in path.read_text(encoding="utf-8").splitlines()
            if x.strip()
        ]
        if path.is_file()
        else []
    )


def fisher_greater(a: int, b: int, c: int, d: int) -> float:
    """One-sided Fisher exact p that the first row's rate (a of a+b) is above
    the second's (c of c+d), by the hypergeometric tail."""
    n, k, m = a + b + c + d, a + c, a + b

    def h(x: int) -> float:
        return math.comb(m, x) * math.comb(n - m, k - x) / math.comb(n, k)

    return min(1.0, sum(h(x) for x in range(a, min(m, k) + 1)))


def measure(runs: list[Path], grids: list[dict]) -> dict:
    way, order = {}, {}
    for g in grids:
        for s in g["stacks"]:
            way[s["id"]], order[s["id"]] = s["way"], s["steps"]
    per_pile: dict = {}
    bridge_n = bridge_c = ctrl_n = ctrl_c = 0
    held, ctrl_changed, kind_effects, unsteady_all = [], [], [], set()
    edges: set = set()
    for run in runs:
        alone = {r["step"]: r for r in _load(run / "rows-alone.jsonl")}
        empty = {r["step"]: r for r in _load(run / "rows-empty.jsonl")}
        stacked = [r for f in sorted(run.glob("rows-*.jsonl")) if f.name not in ("rows-alone.jsonl", "rows-empty.jsonl")
                   for r in _load(f)]  # fmt: skip
        if not alone or not stacked:
            continue
        pile = stacked[0]["pile"]
        single = {r["step"]: r for r in stacked if way.get(r["stack"]) == "single"}
        said = (
            json.loads((run / "run.json").read_text())
            if (run / "run.json").is_file()
            else {}
        )
        unsteady = {
            s for s, r in single.items() if s in alone and r["out"] != alone[s]["out"]
        }
        unsteady |= set(
            said.get("never", [])
        )  # stage 0's two runs alone, as the run was given them
        unsteady_all |= unsteady
        fired = sorted(
            s
            for s, r in alone.items()
            if fires(r) and (s not in empty or r["out"] != empty[s]["out"])
        )
        printed = sorted(s for s, r in alone.items() if fires(r))
        by: dict = {}
        for r in stacked:
            by.setdefault(r["stack"], []).append(r)

        def changed(r: dict) -> bool | None:
            s = r["step"]
            if s in unsteady or s not in alone:
                return None
            if r.get("day") != alone[s].get("day"):
                return None  # another day than its baseline: a step may count days
            return r["out"] != alone[s]["out"]

        moved = 0
        for sid, rs in by.items():
            rs.sort(key=lambda r: r["at"])
            w = way.get(sid)
            if w in ("bridge", "no-bridge", "kind") and len(rs) == 2:
                c = changed(rs[1])
                if c is None:
                    continue
                first, second = rs[0]["step"], rs[1]["step"]
                if w == "bridge":
                    bridge_n += 1
                    bridge_c += c
                    if c:
                        held.append(
                            {"pile": pile, "from": first, "to": second, "stack": sid}
                        )
                        edges.add((first, second))
                elif w == "no-bridge":
                    ctrl_n += 1
                    ctrl_c += c
                    if c:
                        ctrl_changed.append(
                            {"pile": pile, "from": first, "to": second, "stack": sid}
                        )
                else:
                    kind_effects.append({"pile": pile, "writer": first, "reader": second, "changed": c,
                                         "kinds": sorted(rs[0].get("rows", {})),
                                         "groups": rs[0].get("row_groups", [])})  # fmt: skip
                    if c:
                        edges.add((first, second))
            for r in rs:
                if w != "single" and changed(r):
                    moved += 1
        per_pile[pile] = {"steps_alone": len(alone), "printed": len(printed), "fired": len(fired),
                          "fired_steps": fired, "unsteady": sorted(unsteady), "stack_runs_changed": moved}  # fmt: skip
    groups = _components(edges)
    return {
        "about": "changes.py, written after the first report: the same run's baseline, fired against an empty pile, bridges held, kinds, pools",
        "piles": per_pile,
        "unsteady": sorted(unsteady_all),
        "bridges": {"stacks": bridge_n, "changed": bridge_c, "held": held},
        "controls": {"stacks": ctrl_n, "changed": ctrl_c, "changed_rows": ctrl_changed},
        "bridges_beyond_controls_p": fisher_greater(bridge_c, bridge_n - bridge_c, ctrl_c, ctrl_n - ctrl_c) if bridge_n and ctrl_n else None,
        "kinds": kind_effects,
        "pools": groups,
    }  # fmt: skip


def _components(edges: set) -> list[list[str]]:
    near: dict = {}
    for a, b in edges:
        near.setdefault(a, set()).add(b)
        near.setdefault(b, set()).add(a)
    seen, out = set(), []
    for n in sorted(near):
        if n in seen:
            continue
        todo, group = [n], []
        while todo:
            x = todo.pop()
            if x not in seen:
                seen.add(x)
                group.append(x)
                todo += sorted(near[x] - seen)
        out.append(sorted(group))
    return sorted(out, key=lambda g: (-len(g), g))


def report(res: dict) -> str:
    out = ["# What the stacks change", "", res["about"] + ".", ""]
    b, c = res["bridges"], res["controls"]
    out += [
        "## Fired, against an empty pile",
        "",
        "| pile | printed | fired | differs from empty |",
        "|---|---|---|---|",
    ]
    for p, v in sorted(res["piles"].items()):
        out.append(
            f"| {p} | {v['printed']} | {v['fired']} | {v['printed'] - v['fired']} print the same on nothing |"
        )
    out += ["", "## Bridges held", ""]
    br = f"{b['changed']} of {b['stacks']}" if b["stacks"] else "none run"
    cr = f"{c['changed']} of {c['stacks']}" if c["stacks"] else "none run"
    out.append(f"- Bridges: the taker changed in {br}; no-bridge pairs: the second changed in {cr}; "
               f"one-sided Fisher p {res['bridges_beyond_controls_p']}.")  # fmt: skip
    for h in b["held"]:
        out.append(f"  - held on {h['pile']}: `{h['from']}` then `{h['to']}`")
    for h in c["changed_rows"]:
        out.append(
            f"  - a control changed on {h['pile']}: `{h['from']}` then `{h['to']}`"
        )
    out += ["", "## Kinds: which writer moves which reader", ""]
    moved = [k for k in res["kinds"] if k["changed"]]
    out.append(f"- {len(moved)} of {len(res['kinds'])} kind stacks moved their reader.")
    by: dict = {}
    for k in moved:
        by.setdefault((k["writer"], ", ".join(k["kinds"])), {}).setdefault(
            k["reader"], set()
        ).add(k["pile"])
    for (w, kinds), rs in sorted(by.items()):
        out.append(
            f"  - `{w}` ({kinds or 'no rows'}) moved: "
            + ", ".join(f"`{r}` ({len(p)} piles)" for r, p in sorted(rs.items()))
        )
    out += ["", "## Pools: steps joined by a change one made in the other", ""]
    for g in res["pools"]:
        out.append(f"- {len(g)}: " + ", ".join(f"`{s}`" for s in g))
    if not res["pools"]:
        out.append("- None.")
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    verb = argv[0] if argv else ""
    opts: dict = {"run": [], "grid": []}
    it = iter(argv[1:])
    for a in it:
        if a in ("--run", "--grid"):
            opts[a[2:]].append(next(it, ""))
        elif a in ("--to", "--result"):
            opts[a[2:]] = next(it, "")
        else:
            opts = {}
            break
    try:
        if (
            verb == "measure"
            and opts.get("run")
            and opts.get("grid")
            and opts.get("to")
        ):
            res = measure(
                [Path(r) for r in opts["run"]],
                [json.loads(Path(g).read_text()) for g in opts["grid"]],
            )
            Path(opts["to"]).write_text(
                json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf-8"
            )
            return 0
        if verb == "report" and opts.get("result") and opts.get("to"):
            Path(opts["to"]).write_text(
                report(json.loads(Path(opts["result"]).read_text())), encoding="utf-8"
            )
            return 0
    except (OSError, ValueError, KeyError) as why:
        print(f"refused: {why}", file=sys.stderr)
        return 2
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
