"""grew.py: what came back from the grown sweep held to its rules: whole, as much saved as foretold, every state the same.

    python demo/shared-runs/door/grown/grew.py --runs DIR --ring FILE [--against DIR]
        [--plan PLAN --starts STARTS] [--json]

DIR holds a folder for each notebook that came back, under its name
(`round-R-machine-K`, `check-K`), wherever below DIR the download put
it. FILE is the ring grown_notebooks.py wrote. `--against` is the first
study's kept runs (study/runs).

No baseline is run: every job alone would step its own length, or to
where its trajectory halts, and the shared run finds each halt itself;
the check then steps up to each one to see it halt. So what the sweep
would cost alone is counted, and what it cost shared is what was
stepped.

    G1  every folder is whole by its seal, its log holds, its seal's
        signature holds, and its signer is in the ring
    G2  the share of steps saved is within 2 points of the share that
        stepping each trajectory once, to its longest job or its halt,
        would save
    G3  the checks stepped every kept state of every round again and
        found every one the same, and every halt the memory names a halt
    G4  each round took in its own place's earlier rounds and nothing
        else, each as enrolled
    G5  no trajectory was stepped into its halt twice
    G6  every job that is also the first study's (its 22 setups at its
        ten lengths) comes to the first study's SHA-256

Measured, with no threshold: bytes that came back, by round; states
kept; seconds stepping; what the checks stepped, as a share of the
sweep alone; the kinds of processor drawn.

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
import runner  # noqa: E402
import sweep  # noqa: E402

USAGE = __doc__.split("\n\n")[1]
RULES = ("G1", "G2", "G3", "G4", "G5", "G6")


def rows(path: Path) -> list[dict]:
    return [
        json.loads(x)
        for x in path.read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]


def figures(
    plan: dict, starts: dict, runs: Path, ring: dict[str, str], against: Path | None
) -> dict:
    got = {p.parent.name: p.parent for p in sorted(runs.rglob("run.json"))}
    places, rounds = range(plan["machines"]), range(1, plan["rounds"] + 1)
    parts = [f"round-{r}-machine-{k}" for r in rounds for k in places]
    checks = [f"check-{k}" for k in places]
    f: dict = {"wanted": [*parts, *checks], "came": sorted(got)}
    f["missing"] = [
        n
        for n in f["wanted"]
        if n not in got or not (got[n] / "manifest.json").is_file()
    ]
    if f["missing"]:
        return f
    seals = {
        n: json.loads((got[n] / "manifest.json").read_text(encoding="utf-8"))
        for n in f["wanted"]
    }
    f["not_whole"] = [n for n in f["wanted"] if machine.verify(got[n], ring)[0] != 0]
    said = {"power": seals[parts[0]].get("power")}
    names = {
        runner.identity(starts[t["name"]], said): t["name"]
        for t in plan["trajectories"]
    }
    halts: dict[str, int] = {}
    f["stepped"], f["states"], f["tried"], ends = 0, 0, {}, {}
    f["door_wrong"], f["bytes_by_round"], f["seconds"] = [], {}, 0.0
    for r in rounds:
        for k in places:
            name = f"round-{r}-machine-{k}"
            for row in rows(got[name] / "memory.jsonl"):
                if "halt" in row:
                    halts[names[row["trajectory"]]] = row["halt"]
                else:
                    f["states"] += 1
            for a in rows(got[name] / "acts.jsonl"):
                f["stepped"] += a["stepped"]
                f["seconds"] += a.get("seconds", 0)
                ends[a["job"]] = a["sha256"]
                if a["tried_halt"]:
                    f["tried"][a["trajectory"]] = f["tried"].get(a["trajectory"], 0) + 1
            took = seals[name]["took_in"]
            want = {f"round-{q}-machine-{k}" for q in range(1, r)}
            if set(took) != want or any(v["how"] != "taken" or "enrolled" not in v["why"] for v in took.values()):  # fmt: skip
                f["door_wrong"].append(name)
            size = sum(p.stat().st_size for p in got[name].iterdir() if p.is_file())
            f["bytes_by_round"][r] = f["bytes_by_round"].get(r, 0) + size
    f["halts"] = dict(sorted(halts.items()))
    f["jobs"] = len(sweep.jobs(plan))
    f["jobs_done"] = len(ends)

    def stop(name: str, steps: int) -> int:
        return steps if name not in halts else min(steps, halts[name])

    f["alone"] = sum(stop(name, n) for _, name, n in sweep.jobs(plan))
    f["once"] = sum(
        stop(t["name"], max(sweep.lengths(plan, t))) for t in plan["trajectories"]
    )
    f["foretold"] = round(100 * (1 - f["once"] / f["alone"]), 1)
    f["saved"] = round(100 * (1 - f["stepped"] / f["alone"]), 1)
    f["twice"] = sorted(t for t, n in f["tried"].items() if n > 1)
    found = {n: v for c in checks for n, v in seals[c]["checked"].items()}
    f["check"] = {
        "folders": len(found), "of": sum(v["of"] for v in found.values()),
        "states": sum(v["states"] for v in found.values()), "same": sum(v["same"] for v in found.values()),
        "halts": sum(v["halts"] for v in found.values()),
        "halts_that_halt": sum(v["halts_that_halt"] for v in found.values()),
        "stepped": sum(a["stepped"] for c in checks for a in rows(got[c] / "acts.jsonl")),
    }  # fmt: skip
    f["anchor"] = None
    if against is not None:
        theirs = {a["job"]: a["sha256"] for d in sorted(against.glob("round-*-machine-*"))
                  for a in rows(d / "acts.jsonl")}  # fmt: skip
        both = sorted(set(theirs) & set(ends))
        f["anchor"] = {
            "jobs": len(both),
            "of": len(theirs),
            "differ": [j for j in both if theirs[j] != ends[j]],
        }
    f["kinds"] = {
        n: json.loads((got[n] / "machine.json").read_text())["kind"]
        for n in f["wanted"]
    }
    f["seconds"] = round(f["seconds"], 1)
    return f


def verdicts(f: dict) -> dict[str, tuple[str, str]]:
    if f["missing"]:
        some = ", ".join(f["missing"][:6]) + (" ..." if len(f["missing"]) > 6 else "")
        return {
            r: ("not tested", f"{len(f['missing'])} did not come back sealed: {some}")
            for r in RULES
        }
    out = {}
    out["G1"] = ("failed", f"not whole, or not signed by the ring: {', '.join(f['not_whole'])}") if f["not_whole"] else (
        "passed", f"{len(f['wanted'])} folders whole and signed by the ring")  # fmt: skip
    off = abs(f["saved"] - f["foretold"])
    all_done = f["jobs_done"] == f["jobs"]
    out["G2"] = ("passed" if off <= 2 and all_done else "failed",
                 f"{f['stepped']} steps where alone would be {f['alone']}: {f['saved']}% saved, "
                 f"{f['foretold']}% foretold; {f['jobs_done']} of {f['jobs']} jobs")  # fmt: skip
    c = f["check"]
    ok = (
        c["states"] == c["of"] == c["same"] == f["states"]
        and c["halts"] == c["halts_that_halt"]
    )
    ok = ok and c["folders"] == len(f["wanted"]) - len(
        [n for n in f["wanted"] if n.startswith("check-")]
    )
    out["G3"] = ("passed" if ok else "failed",
                 f"{c['same']} of {c['of']} states the same ({f['states']} kept), "
                 f"{c['halts_that_halt']} of {c['halts']} halts halt, over {c['folders']} folders")  # fmt: skip
    out["G4"] = ("failed", f"took in something else, or not as enrolled: {', '.join(f['door_wrong'][:6])}") if f["door_wrong"] else (
        "passed", "each round took in its own place's earlier rounds, as enrolled")  # fmt: skip
    if not f["halts"]:
        out["G5"] = ("not tested", "no trajectory halted")
    else:
        out["G5"] = ("failed", f"stepped into its halt twice: {', '.join(f['twice'])}") if f["twice"] else (
            "passed", f"{len(f['halts'])} trajectories halt, none stepped into its halt twice")  # fmt: skip
    a = f["anchor"]
    if a is None:
        out["G6"] = ("not tested", "no kept runs were given to hold it to")
    else:
        ok = not a["differ"] and a["jobs"] == a["of"] > 0
        out["G6"] = ("passed" if ok else "failed",
                     f"{a['jobs'] - len(a['differ'])} of the first study's {a['of']} jobs come to its SHA-256")  # fmt: skip
    return {r: out[r] for r in RULES}


def say(f: dict, v: dict) -> str:
    out = [f"{r}  {how}: {why}" for r, (how, why) in v.items()]
    if f["missing"]:
        return "\n".join(out)
    out.append("measured:")
    out.append(
        "  bytes back by round: "
        + ", ".join(f"{r}: {n}" for r, n in sorted(f["bytes_by_round"].items()))
    )
    out.append(f"  states kept: {f['states']}; seconds stepping: {f['seconds']}")
    share = round(100 * f["check"]["stepped"] / f["alone"], 1)
    out.append(
        f"  the checks stepped {f['check']['stepped']} steps, {share}% of the sweep alone"
    )
    kinds: dict[str, int] = {}
    for kind in f["kinds"].values():
        kinds[kind] = kinds.get(kind, 0) + 1
    out.append(
        "  kinds drawn: " + ", ".join(f"{k} ({n})" for k, n in sorted(kinds.items()))
    )
    return "\n".join(out)


def main(argv: list[str]) -> int:
    opts: dict = {"json": False}
    it = iter(argv)
    for a in it:
        if (
            a in ("--runs", "--ring", "--against", "--plan", "--starts")
            and a[2:] not in opts
        ):
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
        plan = sweep.load(Path(opts.get("plan") or HERE / "plan.json"))
        starts = json.loads(
            Path(opts.get("starts") or HERE / "starts.json").read_text(encoding="utf-8")
        )
        f = figures(plan, starts, Path(opts["runs"]), machine.ring_of(Path(opts["ring"])),
                    Path(opts["against"]) if opts.get("against") else None)  # fmt: skip
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
