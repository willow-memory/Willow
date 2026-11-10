"""handover.py: where one project stands, to hand on. Python 3.9+.

    python adapters/stdlib/handover/handover.py --project FOLDER [--json]

    handover: populated, dashboards: 19 suggestions wait on you, 1 step flagged, 4 stacks run, 2 stacks never run
    ## waits on you
      box-full         10 suggestions waiting, of 24 rows
    ## flagged
      work.md step 03  sort: populated, 435 files: 271 sorted into 8 categories (mine/run-work-2/03-sort.txt)
    ## last runs
      mend.md          mine/run-mend-4: 4 steps, nothing flagged
      mend.md step 04  glance: populated, 18 questions: 9 held whole, 9 in part, 0 found nothing
    ## never run
      full.md          19 steps
    ## changed since its last run
      start.md         a file it was given is not as it was

What you would write by hand at the end of a day's work, made from what was
kept: the suggestions waiting in each record, and for each stack its last
run, step by step, each step by the one line it said. A hand-on that can be
checked: every line names the file it came from, and nothing here is
anyone's account of the work, only what the runs kept.

Flagged steps come first, since they are what the next person meets. A
stack whose files have changed since its last run is said, so an old
answer isn't handed on as a current one. When nothing waits and nothing is
flagged, it says so: an empty hand-on gives its reason.

It reads the project's records (never your key), its stacks and its run
folders, by the projects add-on. Nothing is written.

It prints a report (ci/README.md, "The report contract"); --json gives the
same as one object. Exit codes, the kernel's: 0 nothing waits and nothing
is flagged; 42 something does, or the folder is no project; 2 refused.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: handover.py --project FOLDER [--json]"
NAME = "handover"
STDLIB = Path(__file__).resolve().parents[1]
#: a stack with more clean steps than this is said by what ran, not a row a step
MANY = 8
#: how much of a step's line is shown
SHOWN = 110


def sibling(folder: str, module: str):
    """Another add-on's module, from its source beside this one."""
    path = STDLIB / folder / f"{module}.py"
    mod = types.ModuleType(f"handover_{module}")
    mod.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), mod.__dict__)
    return mod


def said(run: Path, n: int, name: str, width: int) -> str:
    """The one line a step said: its kept report's, or its output's first."""
    stem = f"{n:0{width}d}-{name}"
    try:
        doc = json.loads((run / "reports" / f"{stem}.json").read_text(encoding="utf-8"))
        line = f"{doc['state']}, {doc['said']}"
    except (OSError, ValueError, KeyError):
        try:
            text = (run / f"{stem}.txt").read_text(encoding="utf-8", errors="replace")
        except OSError:
            return "its output is gone"
        line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "said nothing")
        if line.startswith("{"):  # a program's line, not a person's
            line = f"{len(text.splitlines())} lines for a program"
        line = line.removeprefix(f"{name}: ")
    return line if len(line) <= SHOWN else line[:SHOWN].rsplit(" ", 1)[0] + "…"


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    if len(argv) != 2 or argv[0] != "--project" or not argv[1]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    folder = Path(argv[1]).expanduser().resolve()
    if not folder.is_dir():
        print(f"refused: {folder} isn't a folder", file=sys.stderr)
        return kernel.REFUSED
    pr, st = sibling("projects", "projects"), sibling("stack", "stack")
    found = [p for p in pr.find(folder.parent, st) if p["folder"].resolve() == folder]
    if not found:
        doc = {"addon": NAME, "state": "empty", "groups": [],
               "said": f"{folder} holds no record, so it is no project"}  # fmt: skip
        print(json.dumps(doc, ensure_ascii=False) if as_json else f"{NAME}: empty, {doc['said']}")
        return kernel.ESCALATE
    p = found[0]
    waits, flagged, last, never, changed = [], [], [], [], []
    waiting = 0
    for b in p["boxes"]:
        t = pr.tally(b)
        if "broken" in t:
            waits.append((b.name, f"its chain is broken: {t['broken']}"))
            waiting += 1
        elif t["waiting"]:
            waiting += t["waiting"]
            waits.append((b.name, f"{pr.count(t['waiting'], 'suggestion')} waiting, of {pr.count(t['rows'], 'row')}"))  # fmt: skip
    mine: dict[str, list] = {s["file"].name: [] for s in p["stacks"]}
    for r in p["runs"]:
        s, same = pr.owner(r, p["stacks"])
        if s is not None:
            mine[s["file"].name].append((r, same))
    for s in p["stacks"]:
        name, runs = s["file"].name, mine[s["file"].name]
        if not runs:
            never.append((name, pr.count(len(s["marks"]), "step")))
            continue
        r, same = runs[0]
        rel = r["folder"].relative_to(p["folder"])
        if not same:
            changed.append((name, f"its steps are not what {rel} ran"))
        elif pr.stale(r, s, p["boxes"], st):
            changed.append((name, "a file it was given is not as it was"))
        logs = sorted(r["folder"].glob("0*-stack.txt"))
        width = len(logs[0].name.split("-")[0])
        done = st.ended(logs[0].read_text(encoding="utf-8", errors="replace"))
        last.append((name, f"{rel}: {pr.count(len(r['marks']), 'step')}, {pr.said_of(r)}"))
        clean = [n for n in sorted(done) if not done[n]["flagged"]]
        for n in sorted(done):
            step = done[n]
            line = f"{step['name']}: {said(r['folder'], n, step['name'], width)}"
            where = f"{name} step {n:0{width}d}"
            if step["flagged"]:
                flagged.append((where, f"{line} ({rel}/{n:0{width}d}-{step['name']}.txt)"))
            elif len(clean) <= MANY:
                last.append((where, line))
        if len(clean) > MANY:  # a long stack by what ran, not a row a step
            names: dict[str, int] = {}
            for n in clean:
                names[done[n]["name"]] = names.get(done[n]["name"], 0) + 1
            each = ", ".join(f"{k} ×{v}" if v > 1 else k for k, v in names.items())
            last.append((f"{name} steps", f"{each}: each in {rel}"))
    parts = []
    if waiting:
        parts.append(f"{pr.count(waiting, 'suggestion')} wait{'s' * (waiting == 1)} on you")
    if flagged:
        parts.append(f"{pr.count(len(flagged), 'step')} flagged")
    runs_n = sum(1 for w, _ in last if " step" not in w)
    if runs_n:
        parts.append(f"{pr.count(runs_n, 'stack')} run")
    if never:
        parts.append(f"{pr.count(len(never), 'stack')} never run")
    if not waiting and not flagged:
        parts.insert(0, "nothing waits on you and no step is flagged")
    groups = [("waits on you", waits), ("flagged", flagged), ("last runs", last),
              ("never run", never), ("changed since its last run", changed)]  # fmt: skip
    doc = {
        "addon": NAME,
        "state": "populated",
        "said": f"{p['name']}: {', '.join(parts)}",
        "groups": [
            {"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
            for g, rows in groups
            if rows
        ],
    }
    if as_json:
        print(json.dumps(doc, ensure_ascii=False))
    else:
        rows = [r for g in doc["groups"] for r in g["rows"]]
        w = min(max((len(r["where"]) for r in rows), default=0), 60)
        print(f"{NAME}: {doc['state']}, {doc['said']}")
        for g in doc["groups"]:
            print(f"## {g['name']}")
            for r in g["rows"]:
                print(f"  {r['where']:<{w}}  {r['what']}".rstrip())
    return kernel.ESCALATE if waiting or flagged else kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
