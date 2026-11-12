"""held.py: what came back from Kaggle held to the first study's kept runs, rule by rule.

    python demo/shared-runs/door/kaggle/held.py --runs DIR --ring FILE [--against DIR]
        [--plan PLAN] [--json]

DIR holds a folder for each notebook that came back, under its name
(`round-1-machine-0-a`, `round-1-machine-0`, ..., `check`), wherever
below DIR Kaggle's download put it. FILE is the ring door_notebooks.py wrote
beside the notebooks. `--against` is the first study's kept runs
(study/runs), which this run should come to, byte for byte.

    K1  every folder that came back ended is whole by its seal, its log
        holds, its seal's signature holds, and its signer is in the ring
        (a part stopped by its budget has no seal yet, and is not held
        to one)
    K2  each machine's part, in each round, is the first study's own: the
        same jobs, from the same step, the same steps stepped, ending the
        same, the same SHA-256; and the same states kept
    K3  every first-round part was carried on from a notebook before it,
        and at least one was cut inside its work; none passes K2 by
        having begun over without saying so
    K4  the shared runs step, in all, what the first study's stepped
    K5  the check stepped every kept state and found every one the same,
        and every halt the memory names a halt
    K6  each later round took in its own place's earlier rounds and
        nothing else, each as enrolled

Measured, with no threshold: the kinds of processor drawn; the parts
begun over because they came back on another kind; seconds; the size
of what came back.

It reads and writes nothing. Exit codes, the kernel's: 0 every rule
passed; 42 a rule failed or was not tested; 2 refused.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(1, str(HERE.parents[1] / "study"))
import machine  # noqa: E402
import sweep  # noqa: E402

USAGE = __doc__.split("\n\n")[1]
RULES = ("K1", "K2", "K3", "K4", "K5", "K6")
SAME = ("job", "from", "stepped", "ended", "outcome", "sha256")


def rows(path: Path) -> list[dict]:
    return [
        json.loads(x)
        for x in path.read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]


def folders(runs: Path) -> dict[str, Path]:
    return {p.parent.name: p.parent for p in sorted(runs.rglob("run.json"))}


def figures(plan: dict, runs: Path, ring: dict[str, str], against: Path | None) -> dict:
    got = folders(runs)
    places, rounds = range(plan["machines"]), range(1, plan["rounds"] + 1)
    parts = [f"round-{r}-machine-{k}" for r in rounds for k in places]
    firsts = [f"round-1-machine-{k}-a" for k in places]
    f: dict = {"wanted": [*firsts, *parts, "check"], "came": sorted(got)}
    f["missing"] = [n for n in f["wanted"] if n not in got]
    sealed = [
        n
        for n, d in got.items()
        if not n.endswith("-a") or (d / "manifest.json").is_file()
    ]
    f["not_whole"] = [n for n in sealed if machine.verify(got[n], ring)[0] != 0]
    f["differ"], f["stepped"], f["first_study"] = [], 0, None
    for name in parts:
        if name not in got:
            continue
        acts = rows(got[name] / "acts.jsonl")
        f["stepped"] += sum(a["stepped"] for a in acts)
        if against is None:
            continue
        theirs = rows(against / name / "acts.jsonl")
        same = [[a[k] for k in SAME] for a in acts] == [
            [a[k] for k in SAME] for a in theirs
        ]
        kept = sorted(map(machine.canon, rows(got[name] / "memory.jsonl")))
        same = same and kept == sorted(
            map(machine.canon, rows(against / name / "memory.jsonl"))
        )
        if not same:
            f["differ"].append(name)
    if against is not None:
        f["first_study"] = sum(
            a["stepped"] for n in parts for a in rows(against / n / "acts.jsonl")
        )
    f["carried"], f["cut_inside"], f["cut"], f["begun_over"] = [], [], [], []
    for k in places:
        name = f"round-1-machine-{k}"
        if name not in got:
            continue
        said = rows(got[name] / "log.jsonl")
        whats = [r["what"] for r in said]
        if "carried on from" in whats:
            f["carried"].append(name)
        stops = [r for r in said if r["what"] == "stopped at the budget"]
        if stops:
            f["cut"].append(name)
        if any("inside" in r for r in stops):
            f["cut_inside"].append(name)
        if (got[name] / "restarted.json").exists():
            f["begun_over"].append(name)
    f["check"] = None
    if "check" in got and (got["check"] / "manifest.json").is_file():
        found = json.loads((got["check"] / "manifest.json").read_text())["checked"]
        f["check"] = {
            "folders": sorted(found), "states": sum(v["states"] for v in found.values()),
            "of": sum(v["of"] for v in found.values()), "same": sum(v["same"] for v in found.values()),
            "halts": sum(v["halts"] for v in found.values()),
            "halts_that_halt": sum(v["halts_that_halt"] for v in found.values()),
            "stepped": sum(a["stepped"] for a in rows(got["check"] / "acts.jsonl")),
        }  # fmt: skip
    f["door_wrong"] = []
    for r in rounds:
        for k in places:
            name = f"round-{r}-machine-{k}"
            if name not in got or not (got[name] / "manifest.json").is_file():
                continue
            took = json.loads((got[name] / "manifest.json").read_text())["took_in"]
            want = {f"round-{q}-machine-{k}" for q in range(1, r)}
            if set(took) != want or any(v["how"] != "taken" or "enrolled" not in v["why"] for v in took.values()):  # fmt: skip
                f["door_wrong"].append(name)
    f["kinds"] = {
        n: json.loads((d / "machine.json").read_text())["kind"] for n, d in got.items()
    }
    f["seconds"] = {n: round(sum(a.get("seconds", 0) for a in rows(d / "acts.jsonl")), 1)
                    for n, d in got.items()}  # fmt: skip
    f["bytes"] = {
        n: sum(p.stat().st_size for p in d.iterdir() if p.is_file())
        for n, d in got.items()
    }
    return f


def verdicts(f: dict) -> dict[str, tuple[str, str]]:
    """{rule: (passed | failed | not tested, why)}."""
    out = {}
    whole = not f["missing"]
    lacking = f"did not come back: {', '.join(f['missing'])}"
    if f["not_whole"]:
        out["K1"] = (
            "failed",
            f"not whole, or not signed by the ring: {', '.join(f['not_whole'])}",
        )
    else:
        out["K1"] = ("passed", f"{len(f['came'])} folders whole and signed by the ring") if whole else ("not tested", lacking)  # fmt: skip
    if f["first_study"] is None:
        out["K2"] = out["K4"] = ("not tested", "no kept runs were given to hold it to")
    elif f["differ"]:
        out["K2"] = ("failed", f"not the first study's: {', '.join(f['differ'])}")
    else:
        out["K2"] = ("passed", "every part is the first study's, byte for byte") if whole else ("not tested", lacking)  # fmt: skip
    if f["first_study"] is not None:
        same = f["stepped"] == f["first_study"]
        out["K4"] = (("passed" if same else "failed") if whole else "not tested",
                     f"{f['stepped']} steps, the first study's {f['first_study']}")  # fmt: skip
    firsts = [
        n for n in f["wanted"] if n.startswith("round-1-") and not n.endswith("-a")
    ]
    silent = [n for n in firsts if n not in f["carried"] and n not in f["begun_over"]]
    if not whole:
        out["K3"] = ("not tested", lacking)
    elif silent:
        out["K3"] = (
            "failed",
            f"neither carried on nor said to have begun over: {', '.join(silent)}",
        )
    elif not f["cut_inside"]:
        out["K3"] = (
            "not tested",
            "no part was cut inside its work, so going on was not tried",
        )
    else:
        out["K3"] = ("passed", f"{len(f['carried'])} carried on, {len(f['cut_inside'])} cut inside a job, "
                               f"{len(f['begun_over'])} begun over and said so")  # fmt: skip
    c = f["check"]
    if c is None:
        out["K5"] = ("not tested", "the check did not come back sealed")
    else:
        ok = (
            c["states"] == c["of"] == c["same"]
            and c["halts"] == c["halts_that_halt"]
            and c["of"] > 0
        )
        every = len(c["folders"]) == len(f["wanted"]) - len(firsts) - 1
        out["K5"] = ("passed" if ok and every else "failed",
                     f"{c['same']} of {c['of']} states the same, {c['halts_that_halt']} of {c['halts']} halts halt, "
                     f"over {len(c['folders'])} folders")  # fmt: skip
    if f["door_wrong"]:
        out["K6"] = (
            "failed",
            f"took in something else, or not as enrolled: {', '.join(f['door_wrong'])}",
        )
    else:
        out["K6"] = ("passed", "each later round took in its own place's earlier rounds, as enrolled") if whole else ("not tested", lacking)  # fmt: skip
    return {r: out[r] for r in RULES}


def say(f: dict, v: dict) -> str:
    out = [f"{r}  {how}: {why}" for r, (how, why) in v.items()]
    kinds: dict[str, int] = {}
    for kind in f["kinds"].values():
        kinds[kind] = kinds.get(kind, 0) + 1
    out.append("measured:")
    out.append(
        "  kinds drawn: " + ", ".join(f"{k} ({n})" for k, n in sorted(kinds.items()))
    )
    out.append(
        f"  begun over on another kind: {len(f['begun_over'])} ({', '.join(f['begun_over']) or 'none'})"
    )
    out.append(
        f"  cut by the budget: {len(f['cut'])}, inside a job: {len(f['cut_inside'])}"
    )
    out.append(
        f"  seconds stepping, all folders: {round(sum(f['seconds'].values()), 1)}"
    )
    out.append(f"  bytes that came back: {sum(f['bytes'].values())}, the largest {max(f['bytes'].values(), default=0)}")  # fmt: skip
    if f["check"]:
        out.append(f"  the check stepped {f['check']['stepped']} steps")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    opts: dict = {"json": False}
    it = iter(argv)
    for a in it:
        if a in ("--runs", "--ring", "--against", "--plan") and a[2:] not in opts:
            opts[a[2:]] = next(it, "")
        elif a == "--json":
            opts["json"] = True
        else:
            opts = {}
            break
    if not opts.get("runs") or not opts.get("ring"):
        print(USAGE, file=sys.stderr)
        return 2
    try:
        plan = sweep.load(
            Path(opts.get("plan") or HERE.parents[1] / "study" / "plan.json")
        )
        ring = machine.ring_of(Path(opts["ring"]))
        f = figures(
            plan,
            Path(opts["runs"]),
            ring,
            Path(opts["against"]) if opts.get("against") else None,
        )
        v = verdicts(f)
    except (OSError, ValueError, KeyError, machine.Refuse) as why:
        print(f"refused: {why!r}", file=sys.stderr)
        return 2
    print(
        json.dumps({"figures": f, "verdicts": v}, indent=1, sort_keys=True)
        if opts["json"]
        else say(f, v)
    )
    return 0 if all(how == "passed" for how, _ in v.values()) else 42


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
