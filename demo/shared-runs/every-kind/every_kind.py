"""every_kind.py: every job of the sweep, run alone on another machine, held
to what the study's baseline came to.

    python demo/shared-runs/every-kind/every_kind.py --plan PLAN --truth FOLDER --runs FOLDER
        [--also RUNS] [--box DIR --gate NAME] [--json]

The first study's R1 passed with only 3 of its 220 jobs run in full on
all three kinds of processor: one kind ran everything and the others
checked. This is the addition that closes it. A machine runs the whole
sweep alone, with the study's own runner.py, plan and starts:

    python demo/shared-runs/study/runner.py alone --plan PLAN --starts STARTS --repo DIR --to OUT

`--truth` is the folder the study's first baseline left. `--runs` holds
one folder for each machine that did the above. Two rules:

    E1  every added machine ran every job of the plan, and each came to
        the same outcome, the same step and the same bytes as the truth
    E2  measured: the jobs run in full on each kind of processor, and on
        how many kinds each job was, counting with `--also` what the
        study's own machines ran

With `--box`, each verdict is a row on that record. It reads and, with
`--box`, writes the record only. Exit codes, the kernel's: 0 no rule
failed; 42 one did; 2 refused.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent / "study"
sys.path.insert(0, str(STUDY))
import sweep  # noqa: E402

USAGE = __doc__.split("\n\n")[1]
REFUSED, ESCALATE = 2, 42
RULES = ("E1", "E2")
IN_FULL = ("alone", "shared", "afresh")


def acts_of(folder: Path) -> list[dict]:
    return [json.loads(x) for x in (folder / "acts.jsonl").read_text().splitlines()]


def kind_of(folder: Path) -> str:
    return json.loads((folder / "machine.json").read_text(encoding="utf-8"))["kind"]


def result(act: dict) -> tuple:
    return act["outcome"], act["ended"], act["sha256"]


def machines(folder: Path) -> list[Path]:
    return sorted(p for p in folder.iterdir() if (p / "acts.jsonl").is_file())


def judged(plan: dict, truth: Path, runs: Path, also: Path | None) -> tuple[dict, dict]:
    """(what each added machine came to, the verdicts)."""
    jobs = [j for j, _, _ in sweep.jobs(plan)]
    true = {a["job"]: result(a) for a in acts_of(truth) if a["mode"] == "alone"}
    if sorted(true) != sorted(jobs):
        raise ValueError("the truth is not a baseline of this plan")
    added = {}
    on: dict[str, set[str]] = {j: set() for j in jobs}
    for folder in machines(runs):
        mine = {a["job"]: result(a) for a in acts_of(folder) if a["mode"] == "alone"}
        kind = kind_of(folder)
        added[folder.name] = {
            "kind": kind,
            "ran": sum(1 for j in jobs if j in mine),
            "same": sum(1 for j in jobs if mine.get(j) == true[j]),
            "differ": sorted(j for j in jobs if j in mine and mine[j] != true[j]),
        }
        for j in mine:
            if j in on:
                on[j].add(kind)
    for folder in machines(also) if also else ():
        kind = kind_of(folder)
        for a in acts_of(folder):
            if a["mode"] in IN_FULL and a["job"] in on and not a.get("took"):
                on[a["job"]].add(kind)
    short = sorted(n for n, m in added.items() if m["ran"] < len(jobs))
    wrong = sorted(n for n, m in added.items() if m["differ"])
    if not added:
        e1 = {"state": "not tested", "said": "no machine's run is here"}
    elif wrong:
        e1 = {"state": "failed", "said": "came to other bytes: " + "; ".join(f"{n}, {len(added[n]['differ'])} of {added[n]['ran']} jobs" for n in wrong)}  # fmt: skip
    elif short:
        e1 = {
            "state": "not tested",
            "said": "did not run every job: " + ", ".join(short),
        }
    else:
        e1 = {"state": "passed", "said": "; ".join(f"{n} ({m['kind']}): {m['same']} of {len(jobs)} jobs the same bytes as the baseline" for n, m in added.items())}  # fmt: skip
    e1["figures"] = added
    kinds = sorted({k for ks in on.values() for k in ks})
    by_kind = {k: sum(1 for ks in on.values() if k in ks) for k in kinds}
    count = {
        n: sum(1 for ks in on.values() if len(ks) == n) for n in range(len(kinds) + 1)
    }
    three = sum(v for n, v in count.items() if n >= 3)
    e2 = {
        "state": "measured",
        "said": f"{three} of {len(jobs)} jobs run in full, from their start, on three kinds of processor or more; by kind: "
        + "; ".join(f"{k}: {n}" for k, n in by_kind.items()),
        "figures": {"jobs": len(jobs), "by_kind": by_kind, "jobs_by_number_of_kinds": count},
    }  # fmt: skip
    return added, {"E1": e1, "E2": e2}


def main(argv: list[str]) -> int:
    opts: dict = {"json": False}
    it = iter(argv)
    for a in it:
        if a in ("--plan", "--truth", "--runs", "--also", "--box", "--gate") and a[2:] not in opts:  # fmt: skip
            opts[a[2:]] = next(it, "")
        elif a == "--json":
            opts["json"] = True
        else:
            opts = {}
            break
    if not all(opts.get(k) for k in ("plan", "truth", "runs")) or bool(opts.get("box")) != bool(opts.get("gate")):  # fmt: skip
        print(USAGE, file=sys.stderr)
        return REFUSED
    try:
        plan = sweep.load(Path(opts["plan"]))
        also = Path(opts["also"]) if opts.get("also") else None
        added, v = judged(plan, Path(opts["truth"]), Path(opts["runs"]), also)
        if opts.get("box"):
            sys.path.insert(0, str(HERE.parents[2]))
            import kernel

            box = Path(opts["box"])
            if not (box / "kernel.json").exists():
                raise ValueError("not a kernel box; init first")
            files = [Path(opts["truth"]) / "acts.jsonl"] + [m / "acts.jsonl" for m in machines(Path(opts["runs"]))]  # fmt: skip
            whole = hashlib.sha256()
            for f in files:
                whole.update(hashlib.sha256(f.read_bytes()).hexdigest().encode())
            tools = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (HERE / "every_kind.py", STUDY / "runner.py", STUDY / "sweep.py")}  # fmt: skip
            for r in RULES:
                kernel.append(box, kernel.now(), "verdict", who="shared-runs",
                              gate=f"{opts['gate']}:{r}", verdict=v[r]["state"], said=v[r]["said"],
                              figures=v[r]["figures"], answers_sha256=whole.hexdigest(), tools=tools)  # fmt: skip
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as why:
        print(f"refused: {why}", file=sys.stderr)
        return REFUSED
    if opts["json"]:
        print(json.dumps({"verdicts": v}, indent=1, sort_keys=True))
    else:
        for r in RULES:
            print(f"{r}: {v[r]['state']}, {v[r]['said']}")
    return ESCALATE if any(x["state"] == "failed" for x in v.values()) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
