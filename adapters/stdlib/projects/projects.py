"""projects.py: every project under one folder, and what there is to go back to. Python 3.9+.

    python adapters/stdlib/projects/projects.py --home FOLDER [--json]

    projects: populated, 2 projects under /home/you/willow-stacks: 3 records, 4 stacks, 6 runs; 9 suggestions wait on you
    ## dashboards
      box             30 rows: 12 asked, 0 approved, 9 waiting
      mend.md         4 steps; last run mine/run-mend-3, nothing flagged; 2 runs before it
      full.md         24 steps; never run
      mine/run-0412   a run of no stack that is here now: 10 steps, 1 flagged
    ## cv
      box             61 rows: 4 asked, 38 approved, 0 waiting

A project is a folder that holds a record (a box). Beside it are its stacks
(the markdown files the stack add-on can run) and its runs (the folders a
stack was run into with --to). This lists them, so a page, a terminal or
an assistant can show what there is to switch to without looking for it.

A run doesn't say which stack made it; it is told by its steps. Each step
a run began is written to its log with a mark, eight characters of the
step's name and options. A run whose marks are a stack's own, in order, is
that stack's run. One that shares most of them is a run of the stack as it
was before it changed, and is said so. One that matches none is listed on
its own, so nothing is hidden.

A project is found by what it holds, never by a name it was given. Records
are counted from their rows; your key is never read. Nothing is written.

It prints a report (ci/README.md, "The report contract"); --json gives the
same as one object. Exit codes, the kernel's: 0 listed; 42 a suggestion
waits on you somewhere, a record's chain is broken, or the folder holds no
project; 2 refused.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: projects.py --home FOLDER [--json]"
NAME = "projects"
STDLIB = Path(__file__).resolve().parents[1]


def stack_addon():
    """The stack add-on's module, from its source beside this one."""
    path = STDLIB / "stack" / "stack.py"
    mod = types.ModuleType("projects_stack")
    mod.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), mod.__dict__)
    return mod


def count(n: int, word: str) -> str:
    return f"{n} {word}{'s' * (n != 1)}"


def tally(box: Path) -> dict:
    """A record in four counts, or why it can't be counted."""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return {"broken": "; ".join(breaks)}
    done = {**kernel.sealed(box, rows), **kernel.declined(box, rows)}
    return {
        "rows": len(rows),
        "asked": sum(1 for r in rows if r["kind"] == "bite"),
        "approved": len(kernel.sealed(box, rows)),
        "waiting": sum(
            1
            for r in rows
            if r["kind"] == "proposal"
            and r.get("verdict") == "pass"
            and r["subject"] not in done
        ),
    }


def run_of(folder: Path, st) -> dict | None:
    """A run read from its log: each step's mark in order, how many steps
    ended flagged, and whether it finished; None if the folder isn't a run."""
    logs = sorted(folder.glob("0*-stack.txt"))
    if not logs:
        return None
    try:
        log = logs[0].read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    marks: dict[int, str] = {}
    for line in log.splitlines():
        if m := st.STARTED.fullmatch(line):
            marks[int(m.group(1))] = m.group(3)
    done = st.ended(log)
    return {
        "folder": folder,
        "marks": [marks[n] for n in sorted(marks)],
        "flagged": sum(1 for s in done.values() if s["flagged"]),
        "finished": any(ln.startswith("done: ") for ln in log.splitlines()),
        "when": logs[0].stat().st_mtime,
    }


def find(home: Path, st) -> list[dict]:
    """Each folder under `home` that holds a record: its records, its stacks
    (each with its steps' marks) and its runs, newest first."""
    out = []
    for d in sorted(p for p in home.iterdir() if p.is_dir() and not p.name.startswith(".")):  # fmt: skip
        try:
            inside = sorted(d.iterdir())
        except OSError:
            continue
        boxes = [b for b in inside if (b / "kernel.json").is_file()]
        if not boxes:
            continue
        stacks = []
        for f in inside:
            if f.suffix != ".md" or not f.is_file():
                continue
            try:
                pools, err = st.parse_stack(f.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            steps = [s for _, ss in pools for s in ss] if not err else []
            if steps:
                stacks.append({"file": f, "marks": [st.mark(n, a) for n, a in steps]})
        # a run is a folder with a stack's log in it: here, or one folder down
        places = [d, *(c for c in inside if c.is_dir() and c not in boxes)]
        runs = []
        for place in places:
            try:
                kids = sorted(place.iterdir())
            except OSError:
                continue
            runs += [r for k in kids if k.is_dir() and k not in boxes and (r := run_of(k, st))]  # fmt: skip
        runs.sort(key=lambda r: (-r["when"], r["folder"].name))
        out.append({"name": d.name, "folder": d, "boxes": boxes, "stacks": stacks, "runs": runs})  # fmt: skip
    return out


def owner(run: dict, stacks: list[dict]) -> tuple[dict | None, bool]:
    """(the stack a run is of, whether it is the stack as it is now). A run
    is a stack's when its marks are the stack's own in order, as far as the
    run got; it is of the stack as it was when it shares most of them."""
    best, share = None, 0.0
    for s in stacks:
        if run["marks"] and run["marks"] == s["marks"][: len(run["marks"])]:
            return s, True
        both = len(set(run["marks"]) & set(s["marks"]))
        part = both / max(len(run["marks"]), len(s["marks"]), 1)
        if part > share:
            best, share = s, part
    return (best, False) if share > 0.5 else (None, False)


def said_of(run: dict) -> str:
    out = "nothing flagged" if not run["flagged"] else f"{run['flagged']} flagged"
    return out if run["finished"] else out + ", not finished"


def rows_of(p: dict) -> tuple[list[tuple[str, str]], int, bool]:
    """(a project's rows, the suggestions waiting in it, a record is broken)."""
    rows, waiting, broken = [], 0, False
    for b in p["boxes"]:
        t = tally(b)
        if "broken" in t:
            rows.append((b.name, f"its chain is broken: {t['broken']}"))
            broken = True
            continue
        waiting += t["waiting"]
        rows.append(
            (b.name, f"{count(t['rows'], 'row')}: {t['asked']} asked, "
                     f"{t['approved']} approved, {t['waiting']} waiting")  # fmt: skip
        )
    mine: dict[str, list] = {s["file"].name: [] for s in p["stacks"]}
    loose = []
    for r in p["runs"]:  # newest first
        s, same = owner(r, p["stacks"])
        if s is None:
            loose.append(r)
        else:
            mine[s["file"].name].append((r, same))
    for s in p["stacks"]:
        what = count(len(s["marks"]), "step")
        runs = mine[s["file"].name]
        if not runs:
            what += "; never run"
        else:
            r, same = runs[0]
            what += f"; last run {r['folder'].relative_to(p['folder'])}, {said_of(r)}"
            if not same:
                what += ", of the stack before it changed"
            if len(runs) > 1:
                what += f"; {count(len(runs) - 1, 'run')} before it"
        rows.append((s["file"].name, what))
    for r in loose:
        rows.append(
            (str(r["folder"].relative_to(p["folder"])),
             f"a run of no stack that is here now: {count(len(r['marks']), 'step')}, {said_of(r)}")  # fmt: skip
        )
    return rows, waiting, broken


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    if len(argv) != 2 or argv[0] != "--home" or not argv[1]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    home = Path(argv[1]).expanduser()
    if not home.is_dir():
        print(f"refused: {home} isn't a folder", file=sys.stderr)
        return kernel.REFUSED
    found = find(home, stack_addon())
    groups, waiting, broken = [], 0, False
    for p in found:
        rows, w, b = rows_of(p)
        groups.append((p["name"], rows))
        waiting, broken = waiting + w, broken or b
    said = (
        f"{count(len(found), 'project')} under {home}: "
        f"{count(sum(len(p['boxes']) for p in found), 'record')}, "
        f"{count(sum(len(p['stacks']) for p in found), 'stack')}, "
        f"{count(sum(len(p['runs']) for p in found), 'run')}"
    )
    if waiting:
        said += f"; {count(waiting, 'suggestion')} wait{'s' * (waiting == 1)} on you"
    if not found:
        said = f"no folder under {home} holds a record"
    doc = {
        "addon": NAME,
        "state": "populated" if found else "empty",
        "said": said,
        "groups": [
            {"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
            for g, rows in groups
        ],
    }
    if as_json:
        print(json.dumps(doc, ensure_ascii=False))
    else:
        rows = [r for g in doc["groups"] for r in g["rows"]]
        w = min(max((len(r["where"]) for r in rows), default=0), 60)
        print(f"{NAME}: {doc['state']}, {said}")
        for g in doc["groups"]:
            print(f"## {g['name']}")
            for r in g["rows"]:
                print(f"  {r['where']:<{w}}  {r['what']}".rstrip())
    return kernel.ESCALATE if waiting or broken or not found else kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
