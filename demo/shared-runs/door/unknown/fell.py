"""fell.py: what came back from the sweep where nobody is known, held to its rules: what the saving fell to, and that no byte was wrong.

    python demo/shared-runs/door/unknown/fell.py --runs DIR --ring FILE --against DIR
        [--plan PLAN --starts STARTS] [--json]
    python demo/shared-runs/door/unknown/fell.py foretell --against DIR [--plan PLAN --starts STARTS]

DIR holds a folder for each notebook that came back, under its name.
FILE is the ring unknown_notebooks.py wrote. `--against` is the grown
sweep's kept run, where every signer was enrolled (its folders, as they
came back from Kaggle): the same jobs, to hold the bytes to, and the
halts it found, to count with.

    U1  every folder is whole by its seal and its signature holds; no
        round's signer is in the ring
    U2  every round held every folder it was given, as a signer the
        door has not enrolled
    U3  the share of steps saved is within 2 points of the share
        counted beforehand for a memory nobody trusts: each round, each
        place stepping from nothing but what that round has kept
    U4  every job ends as it did where every signer was enrolled: the
        same end, outcome and SHA-256, all of them
    U5  the checks stepped every kept state of every round again and
        found every one the same, and every halt a halt

Measured, with no threshold: steps, beside the enrolled sweep's; states
kept; bytes that came back; the kinds of processor drawn.

`foretell` counts what U3 holds the run to, from the plan and the halts
the enrolled sweep found, and steps nothing.

It reads and writes nothing. Exit codes, the kernel's: 0 every rule
passed, or foretold; 42 a rule failed or was not tested; 2 refused.
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
RULES = ("U1", "U2", "U3", "U4", "U5")
ENDS = ("job", "ended", "outcome", "sha256")


def rows(path: Path) -> list[dict]:
    return [
        json.loads(x)
        for x in path.read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]


def enrolled(plan: dict, starts: dict, against: Path) -> dict:
    """From the sweep where every signer was enrolled: where each
    trajectory halts, how each job ended, and what it stepped."""
    got = {p.parent.name: p.parent for p in sorted(against.rglob("run.json"))}
    parts = [n for n in sorted(got) if n.startswith("round-")]
    if not parts:
        raise ValueError("no rounds of the enrolled sweep are under --against")
    power = json.loads(
        (got[parts[0]] / "manifest.json").read_text(encoding="utf-8")
    ).get("power")
    names = {
        runner.identity(starts[t["name"]], {"power": power}): t["name"]
        for t in plan["trajectories"]
    }
    halts, ends, stepped = {}, {}, 0
    for name in parts:
        for row in rows(got[name] / "memory.jsonl"):
            if "halt" in row:
                halts[names[row["trajectory"]]] = row["halt"]
        for a in rows(got[name] / "acts.jsonl"):
            ends[a["job"]] = [a[x] for x in ENDS]
            stepped += a["stepped"]
    return {"halts": halts, "ends": ends, "stepped": stepped}


def foretold(plan: dict, halts: dict[str, int]) -> dict:
    """Counted, not run: the steps of the sweep when a round goes on from
    nothing but what that round has kept. A trajectory is one place's in
    every round, so a round's memory of it is that place's alone."""
    spacing = plan["spacing"]
    alone = shared = 0
    for round_jobs in sweep.dealt(plan):
        kept: dict[str, set[int]] = {}
        known: set[str] = set()
        for _, name, n in round_jobs:
            stop = halts.get(name)
            alone += n if stop is None else min(n, stop)
            target = n if stop is None or name not in known else min(n, stop)
            have = kept.setdefault(name, {0})
            at = max(k for k in have if k <= target)
            end = target if stop is None else min(target, stop)
            shared += end - at
            have.update(range(at - at % spacing, end + 1, spacing))
            have.add(end)
            if stop is not None and n > stop:
                known.add(name)
    return {
        "alone": alone,
        "stepped": shared,
        "saved": round(100 * (1 - shared / alone), 1),
    }


def figures(
    plan: dict, starts: dict, runs: Path, ring: dict[str, str], against: Path
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
    f["standing"] = {n: machine.verify(got[n], ring)[0] for n in parts}
    was = enrolled(plan, starts, against)
    f["foretold"] = foretold(plan, was["halts"])
    f["enrolled_stepped"] = was["stepped"]
    f["stepped"], f["states"], f["wrong"], f["not_held"], done = 0, 0, [], [], set()
    for r in rounds:
        for k in places:
            name = f"round-{r}-machine-{k}"
            f["states"] += sum(
                1 for row in rows(got[name] / "memory.jsonl") if "step" in row
            )
            for a in rows(got[name] / "acts.jsonl"):
                f["stepped"] += a["stepped"]
                done.add(a["job"])
                if [a[x] for x in ENDS] != was["ends"].get(a["job"]):
                    f["wrong"].append(a["job"])
            took = seals[name]["took_in"]
            want = {f"round-{q}-machine-{k}" for q in range(1, r)}
            if set(took) != want or any(v["how"] != "held" or "not one this door has enrolled" not in v["why"]
                                        for v in took.values()):  # fmt: skip
                f["not_held"].append(name)
    f["jobs"], f["jobs_done"] = len(sweep.jobs(plan)), len(done)
    f["saved"] = round(100 * (1 - f["stepped"] / f["foretold"]["alone"]), 1)
    found = {n: v for c in checks for n, v in seals[c]["checked"].items()}
    f["check"] = {
        "folders": len(found), "of": sum(v["of"] for v in found.values()),
        "states": sum(v["states"] for v in found.values()), "same": sum(v["same"] for v in found.values()),
        "halts": sum(v["halts"] for v in found.values()),
        "halts_that_halt": sum(v["halts_that_halt"] for v in found.values()),
        "stepped": sum(a["stepped"] for c in checks for a in rows(got[c] / "acts.jsonl")),
    }  # fmt: skip
    f["bytes"] = sum(
        p.stat().st_size for n in parts for p in got[n].iterdir() if p.is_file()
    )
    f["kinds"] = {
        n: json.loads((got[n] / "machine.json").read_text())["kind"]
        for n in f["wanted"]
    }
    return f


def verdicts(f: dict) -> dict[str, tuple[str, str]]:
    if f["missing"]:
        some = ", ".join(f["missing"][:6]) + (" ..." if len(f["missing"]) > 6 else "")
        return {
            r: ("not tested", f"{len(f['missing'])} did not come back sealed: {some}")
            for r in RULES
        }
    out = {}
    bad = [n for n, code in f["standing"].items() if code != 42]
    out["U1"] = ("failed", f"not whole, or signed by the ring: {', '.join(bad[:6])}") if bad else (
        "passed", f"{len(f['standing'])} rounds whole, each signed by a key the ring does not hold")  # fmt: skip
    out["U2"] = ("failed", f"did not hold all it was given: {', '.join(f['not_held'][:6])}") if f["not_held"] else (
        "passed", "every round held every folder it was given")  # fmt: skip
    off = abs(f["saved"] - f["foretold"]["saved"])
    ok = off <= 2 and f["jobs_done"] == f["jobs"]
    out["U3"] = ("passed" if ok else "failed",
                 f"{f['stepped']} steps where alone would be {f['foretold']['alone']}: {f['saved']}% saved, "
                 f"{f['foretold']['saved']}% foretold; {f['jobs_done']} of {f['jobs']} jobs")  # fmt: skip
    out["U4"] = ("failed", f"{len(f['wrong'])} jobs do not end as the enrolled sweep's: {', '.join(f['wrong'][:5])}") if f["wrong"] else (
        "passed", f"all {f['jobs_done']} jobs end as they did where every signer was enrolled")  # fmt: skip
    c = f["check"]
    ok = (
        c["states"] == c["of"] == c["same"] == f["states"]
        and c["halts"] == c["halts_that_halt"]
    )
    ok = ok and c["folders"] == len(f["standing"])
    out["U5"] = ("passed" if ok else "failed",
                 f"{c['same']} of {c['of']} states the same ({f['states']} kept), "
                 f"{c['halts_that_halt']} of {c['halts']} halts halt, over {c['folders']} folders")  # fmt: skip
    return {r: out[r] for r in RULES}


def say(f: dict, v: dict) -> str:
    out = [f"{r}  {how}: {why}" for r, (how, why) in v.items()]
    if f["missing"]:
        return "\n".join(out)
    out.append("measured:")
    times = round(f["stepped"] / f["enrolled_stepped"], 2)
    out.append(
        f"  {f['stepped']} steps, {times} times the {f['enrolled_stepped']} of the sweep where every signer was enrolled"
    )
    out.append(
        f"  states kept: {f['states']}; bytes back from the rounds: {f['bytes']}"
    )
    out.append(f"  the checks stepped {f['check']['stepped']} steps")
    kinds: dict[str, int] = {}
    for kind in f["kinds"].values():
        kinds[kind] = kinds.get(kind, 0) + 1
    out.append(
        "  kinds drawn: " + ", ".join(f"{k} ({n})" for k, n in sorted(kinds.items()))
    )
    return "\n".join(out)


def main(argv: list[str]) -> int:
    telling = argv[:1] == ["foretell"]
    opts: dict = {"json": False}
    it = iter(argv[1:] if telling else argv)
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
    if not opts.get("against") or (
        not telling and not (opts.get("runs") and opts.get("ring"))
    ):
        print(USAGE, file=sys.stderr)
        return 2
    try:
        grown = HERE.parent / "grown"
        plan = sweep.load(Path(opts.get("plan") or grown / "plan.json"))
        starts = json.loads(
            Path(opts.get("starts") or grown / "starts.json").read_text(
                encoding="utf-8"
            )
        )
        if telling:
            was = enrolled(plan, starts, Path(opts["against"]))
            print(json.dumps({**foretold(plan, was["halts"]), "halts": len(was["halts"]),
                              "enrolled_stepped": was["stepped"]}, sort_keys=True))  # fmt: skip
            return 0
        f = figures(
            plan,
            starts,
            Path(opts["runs"]),
            machine.ring_of(Path(opts["ring"])),
            Path(opts["against"]),
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
