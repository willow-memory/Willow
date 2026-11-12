"""bought.py: what came back from the sweep with strangers cleared every round, held to its rules: what the clearings cost and what they bought.

    python demo/shared-runs/door/cleared/bought.py --runs DIR --ring FILE --against DIR
        [--plan PLAN --starts STARTS] [--json]
    python demo/shared-runs/door/cleared/bought.py foretell --against DIR [--plan PLAN --starts STARTS]

DIR holds a folder for each notebook that came back, under its name.
FILE is the ring cleared_notebooks.py wrote. `--against` is the grown
sweep's kept run, where every signer was enrolled.

    C1  every folder is whole by its seal and its signature holds; the
        rounds of places 1 and 3 are signed by keys the ring does not
        hold, and every other folder by keys it does
    C2  every round took in every earlier round of its place and held
        none: at places 1 and 3 on the checker's word, at the others as
        enrolled
    C3  every round is the enrolled sweep's, byte for byte: the same
        jobs, from the same step, the same steps stepped, ending the
        same, and the same states kept; so the strangers cost no step
        of the sweep itself
    C4  the clearings looked at every state and halt that places 1 and
        3 kept in rounds one to nine, each once and no more, found
        every one the same, and stepped what was counted beforehand
    C5  the checks at the end stepped every kept state of all fifty
        rounds again and found every one the same, and every halt a halt

Measured, with no threshold: what the clearings stepped, as a share of
the sweep alone; the saving once they are paid for; how many clearings
were carried on on another kind of processor; the kinds drawn.

`foretell` counts what C4 holds the clearings to, from the enrolled
sweep's own folders, and steps nothing.

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
RULES = ("C1", "C2", "C3", "C4", "C5")
STRANGERS = (1, 3)
SAME = ("job", "from", "stepped", "ended", "outcome", "sha256")


def rows(path: Path) -> list[dict]:
    return [
        json.loads(x)
        for x in path.read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]


def folders(root: Path) -> dict[str, Path]:
    return {p.parent.name: p.parent for p in sorted(root.rglob("run.json"))}


def enrolled(plan: dict, starts: dict, against: Path) -> dict:
    """From the sweep where every signer was enrolled: its folders, what it
    stepped, what alone would step, and what looking once at everything
    places 1 and 3 kept before the last round would step."""
    got = folders(against)
    rounds = range(1, plan["rounds"] + 1)
    first = f"round-1-machine-{STRANGERS[0]}"
    if first not in got:
        raise ValueError("the enrolled sweep's rounds are not under --against")
    power = json.loads((got[first] / "manifest.json").read_text(encoding="utf-8")).get(
        "power"
    )
    names = {
        runner.identity(starts[t["name"]], {"power": power}): t["name"]
        for t in plan["trajectories"]
    }
    halts, stepped = {}, 0
    for r in rounds:
        for k in range(plan["machines"]):
            folder = got[f"round-{r}-machine-{k}"]
            stepped += sum(a["stepped"] for a in rows(folder / "acts.jsonl"))
            for row in rows(folder / "memory.jsonl"):
                if "halt" in row:
                    halts[names[row["trajectory"]]] = row["halt"]
    alone = sum(
        n if name not in halts else min(n, halts[name])
        for _, name, n in sweep.jobs(plan)
    )
    # each clearing steps each state that is new to it from the state kept before it,
    # among everything that place has kept up to that round
    clears, states = 0, 0
    for k in STRANGERS:
        kept: dict[str, set[int]] = {}
        for r in list(rounds)[:-1]:
            fresh = rows(got[f"round-{r}-machine-{k}"] / "memory.jsonl")
            for row in fresh:
                if "step" in row:
                    kept.setdefault(row["trajectory"], set()).add(row["step"])
            for row in fresh:
                have = kept.get(row["trajectory"], set())
                if "step" in row:
                    clears += row["step"] - max(
                        (x for x in have if x < row["step"]), default=0
                    )
                    states += 1
                else:
                    clears += row["halt"] - max(
                        (x for x in have if x <= row["halt"]), default=0
                    )
    return {
        "folders": got,
        "stepped": stepped,
        "alone": alone,
        "clears": clears,
        "states": states,
    }


def figures(
    plan: dict, starts: dict, runs: Path, ring: dict[str, str], against: Path
) -> dict:
    got = folders(runs)
    places, rounds = range(plan["machines"]), range(1, plan["rounds"] + 1)
    parts = [f"round-{r}-machine-{k}" for r in rounds for k in places]
    clears = [f"clear-{r}-{k}" for r in list(rounds)[:-1] for k in STRANGERS]
    checks = [f"check-{k}" for k in places]
    f: dict = {"wanted": [*parts, *clears, *checks], "came": sorted(got)}
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
    was = enrolled(plan, starts, against)
    f["alone"], f["enrolled_stepped"], f["foretold_clears"] = (
        was["alone"],
        was["stepped"],
        was["clears"],
    )
    stranger = {f"round-{r}-machine-{k}" for r in rounds for k in STRANGERS}
    f["standing"] = {n: machine.verify(got[n], ring)[0] for n in f["wanted"]}
    f["standing_wrong"] = [
        n for n, code in f["standing"].items() if code != (42 if n in stranger else 0)
    ]
    f["stepped"], f["states"], f["differ"], f["door_wrong"] = 0, 0, [], []
    f["parts"], f["clearings"] = len(parts), len(clears)
    for r in rounds:
        for k in places:
            name = f"round-{r}-machine-{k}"
            acts, theirs = (
                rows(got[name] / "acts.jsonl"),
                rows(was["folders"][name] / "acts.jsonl"),
            )
            f["stepped"] += sum(a["stepped"] for a in acts)
            kept = sorted(map(machine.canon, rows(got[name] / "memory.jsonl")))
            f["states"] += sum(
                1 for row in rows(got[name] / "memory.jsonl") if "step" in row
            )
            same = [[a[x] for x in SAME] for a in acts] == [
                [a[x] for x in SAME] for a in theirs
            ]
            if not same or kept != sorted(
                map(machine.canon, rows(was["folders"][name] / "memory.jsonl"))
            ):
                f["differ"].append(name)
            took = seals[name]["took_in"]
            want = {f"round-{q}-machine-{k}" for q in range(1, r)}
            word = "stepped again" if k in STRANGERS else "enrolled"
            if set(took) != want or any(
                v["how"] != "taken" or word not in v["why"] for v in took.values()
            ):
                f["door_wrong"].append(name)
    f["clears"] = {
        "stepped": 0,
        "looked": 0,
        "twice": 0,
        "not_same": 0,
        "other_kind": 0,
        "of": was["states"],
    }
    for k in STRANGERS:
        last = rows(got[f"clear-{plan['rounds'] - 1}-{k}"] / "acts.jsonl")
        keys = [(a["seal"], a["trajectory"], a["step"], a["mode"]) for a in last]
        f["clears"]["stepped"] += sum(a["stepped"] for a in last)
        f["clears"]["looked"] += sum(a["mode"] == "check" for a in last)
        f["clears"]["twice"] += len(keys) - len(set(keys))
        f["clears"]["not_same"] += sum(not a["same"] for a in last)
        # a clearing's log is carried on with it, so the last one's holds every time it was said
        said = [
            row["what"]
            for row in rows(got[f"clear-{plan['rounds'] - 1}-{k}"] / "log.jsonl")
        ]
        f["clears"]["other_kind"] += said.count("carried on, on another kind")
        for r in list(rounds)[:-1]:
            found = seals[f"clear-{r}-{k}"]["checked"]
            want = {f"round-{q}-machine-{k}" for q in range(1, r + 1)}
            if set(found) != want or not all(
                v["all_the_same"] and v["states"] == v["of"] for v in found.values()
            ):
                f["clears"]["not_same"] += 1
    found = {n: v for c in checks for n, v in seals[c]["checked"].items()}
    f["check"] = {
        "folders": len(found), "of": sum(v["of"] for v in found.values()),
        "states": sum(v["states"] for v in found.values()), "same": sum(v["same"] for v in found.values()),
        "halts": sum(v["halts"] for v in found.values()),
        "halts_that_halt": sum(v["halts_that_halt"] for v in found.values()),
    }  # fmt: skip
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
    bad = f["standing_wrong"]
    out["C1"] = ("failed", f"not standing as it should: {', '.join(bad[:6])}") if bad else (
        "passed", f"{len(f['standing'])} folders whole; the strangers' rounds signed by keys the ring does not hold")  # fmt: skip
    out["C2"] = ("failed", f"did not take all its place's earlier rounds as it should: {', '.join(f['door_wrong'][:6])}") if f["door_wrong"] else (
        "passed", "every round took in every earlier round of its place: the strangers' on the checker's word")  # fmt: skip
    out["C3"] = ("failed", f"not the enrolled sweep's: {', '.join(f['differ'][:6])}") if f["differ"] else (
        "passed", f"all {f['parts']} rounds are the enrolled sweep's, byte for byte: {f['stepped']} steps")  # fmt: skip
    c = f["clears"]
    ok = (
        c["looked"] == c["of"]
        and not c["twice"]
        and not c["not_same"]
        and c["stepped"] == f["foretold_clears"]
    )
    out["C4"] = ("passed" if ok else "failed",
                 f"{c['looked']} of {c['of']} states looked at, {c['twice']} twice, {c['not_same']} not the same; "
                 f"{c['stepped']} steps, {f['foretold_clears']} foretold")  # fmt: skip
    k = f["check"]
    ok = (
        k["states"] == k["of"] == k["same"] == f["states"]
        and k["halts"] == k["halts_that_halt"]
        and k["folders"] == f["parts"]
    )
    out["C5"] = ("passed" if ok else "failed",
                 f"{k['same']} of {k['of']} states the same ({f['states']} kept), "
                 f"{k['halts_that_halt']} of {k['halts']} halts halt, over {k['folders']} folders")  # fmt: skip
    return {r: out[r] for r in RULES}


def say(f: dict, v: dict) -> str:
    out = [f"{r}  {how}: {why}" for r, (how, why) in v.items()]
    if f["missing"]:
        return "\n".join(out)
    c, alone = f["clears"], f["alone"]
    out.append("measured:")
    out.append(
        f"  the clearings stepped {c['stepped']} steps, {round(100 * c['stepped'] / alone, 1)}% of the sweep alone"
    )
    out.append(f"  saved, the sweep itself: {round(100 * (1 - f['stepped'] / alone), 1)}%; "
               f"with the clearings paid for: {round(100 * (1 - (f['stepped'] + c['stepped']) / alone), 1)}%")  # fmt: skip
    out.append(
        f"  clearings carried on on another kind of processor: {c['other_kind']} of {f['clearings']}"
    )
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
            both = was["stepped"] + was["clears"]
            print(json.dumps({"alone": was["alone"], "enrolled_stepped": was["stepped"], "clears": was["clears"],
                              "states_to_look_at": was["states"],
                              "saved_with_the_clearings_paid_for": round(100 * (1 - both / was["alone"]), 1)},
                             sort_keys=True))  # fmt: skip
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
