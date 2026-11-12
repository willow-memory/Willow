"""seen.py: what came back from the trusted-liar run held to its rules: taken before anyone looked, held after.

    python demo/shared-runs/door/trusted/seen.py --runs DIR --ring FILE --against DIR
        [--plan PLAN] [--json]

DIR holds a folder for each notebook that came back, under its name,
and the liar's `round-1-machine-3.lied.json`. FILE is the ring
trusted_notebooks.py wrote. `--against` is the first study's kept runs.

    N1  every folder is whole by its seal, its signature holds, and its
        signer is in the ring, the liar's among them
    N2  before the check, the liar's folder was taken as enrolled and
        the harm went out: a job of the trajectory with the written halt
        stopped at it, and a job of the trajectory with the changed
        state came to a SHA-256 the first study's did not
    N3  the check found both changes in the liar's first round, and
        every state and halt of the other four first rounds the same
    N4  after the check, the liar's first round and the second round
        that went on from it were both held, whoever signed them, and
        every job of that second round done again ends as the first
        study's did
    N5  the other four places took their own first round as enrolled
        and their second round is the first study's, byte for byte

Measured, with no threshold: how many jobs went out wrong before the
check; what the check found of the round that went on from the lie;
steps; the kinds of processor drawn.

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
RULES = ("N1", "N2", "N3", "N4", "N5")
LIAR = 3
SAME = ("job", "from", "stepped", "ended", "outcome", "sha256")
ENDS = ("job", "ended", "outcome", "sha256")


def rows(path: Path) -> list[dict]:
    return [
        json.loads(x)
        for x in path.read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]


def seal(folder: Path) -> dict:
    return json.loads((folder / "manifest.json").read_text(encoding="utf-8"))


def wanted(plan: dict) -> list[str]:
    places = range(plan["machines"])
    return [*(f"round-1-machine-{k}" for k in places), *(f"round-2-machine-{k}-before" for k in places),
            "check", f"round-2-machine-{LIAR}-after"]  # fmt: skip


def figures(plan: dict, runs: Path, ring: dict[str, str], against: Path) -> dict:
    got = {p.parent.name: p.parent for p in sorted(runs.rglob("run.json"))}
    f: dict = {"wanted": wanted(plan), "came": sorted(got)}
    f["missing"] = [
        n
        for n in f["wanted"]
        if n not in got or not (got[n] / "manifest.json").is_file()
    ]
    if f["missing"]:
        return f
    lied = next(iter(sorted(runs.rglob(f"round-1-machine-{LIAR}.lied.json"))), None)
    f["lied"] = json.loads(lied.read_text(encoding="utf-8")) if lied else None
    f["standing"] = {n: machine.verify(got[n], ring)[0] for n in f["wanted"]}
    theirs = {
        k: rows(against / f"round-2-machine-{k}" / "acts.jsonl")
        for k in range(plan["machines"])
    }
    ends = {a["job"]: [a[x] for x in ENDS] for k in theirs for a in theirs[k]}
    f["took"], f["steps"], f["as_first"], f["wrong"] = {}, {}, {}, {}
    for name in f["wanted"]:
        if not name.startswith("round-2-"):
            continue
        k = int(name.split("-")[3])
        acts = rows(got[name] / "acts.jsonl")
        f["took"][name] = {
            n: [v["how"], v["why"]] for n, v in seal(got[name])["took_in"].items()
        }
        f["steps"][name] = sum(a["stepped"] for a in acts)
        f["as_first"][name] = [[a[x] for x in SAME] for a in acts] == [
            [a[x] for x in SAME] for a in theirs[k]
        ]
        f["wrong"][name] = [[a["job"], a["trajectory"], a["ended"], a["outcome"]] for a in acts
                            if [a[x] for x in ENDS] != ends.get(a["job"])]  # fmt: skip
    found = seal(got["check"])["checked"]
    f["check"] = {n: {x: v[x] for x in ("of", "states", "same", "halts", "halts_that_halt", "all_the_same")}
                  for n, v in found.items()}  # fmt: skip
    not_same = [a for a in rows(got["check"] / "acts.jsonl") if not a["same"]]
    f["not_same"] = sorted(
        [a["of"], a["mode"], a["trajectory"], a["step"]] for a in not_same
    )
    f["check_stepped"] = sum(a["stepped"] for a in rows(got["check"] / "acts.jsonl"))
    f["kinds"] = {
        n: json.loads((got[n] / "machine.json").read_text())["kind"]
        for n in f["wanted"]
    }
    return f


def verdicts(plan: dict, f: dict) -> dict[str, tuple[str, str]]:
    if f["missing"]:
        why = f"did not come back sealed: {', '.join(f['missing'])}"
        return {r: ("not tested", why) for r in RULES}
    out = {}
    places = range(plan["machines"])
    first, before, after = (
        f"round-1-machine-{LIAR}",
        f"round-2-machine-{LIAR}-before",
        f"round-2-machine-{LIAR}-after",
    )
    bad = [n for n, code in f["standing"].items() if code != 0]
    out["N1"] = ("failed", f"not whole, or not signed by the ring: {', '.join(bad)}") if bad else (
        "passed", f"{len(f['standing'])} folders whole and signed by the ring, the liar's among them")  # fmt: skip
    lied = f["lied"]
    took = f["took"][before].get(first, ["", ""])
    if lied is None:
        out["N2"] = out["N3"] = (
            "not tested",
            "the lie's own account did not come back",
        )
    else:
        wrong = f["wrong"][before]
        halted = [
            w
            for w in wrong
            if w[1] == lied["halt"][0] and w[2] == lied["halt"][1] and w[3] == "halted"
        ]
        spoiled = [w for w in wrong if w[1] == lied["state"][0]]
        ok = took[0] == "taken" and "enrolled" in took[1] and halted and spoiled
        out["N2"] = ("passed" if ok else "failed",
                     f"the liar's folder was {took[0] or 'not given'}; {len(wrong)} jobs went out wrong: "
                     f"{len(halted)} stopped at the halt that is no halt, {len(spoiled)} from the changed state")  # fmt: skip
        liar = f["check"].get(first)
        honest = [f["check"].get(f"round-1-machine-{k}") for k in places if k != LIAR]
        if liar is None or None in honest:
            out["N3"] = ("not tested", "a folder's check did not come back")
        else:
            mine = [x[1:] for x in f["not_same"] if x[0] == first]
            state, halt = (
                ["check", *lied["state"]] in mine,
                ["halt-check", *lied["halt"]] in mine,
            )
            clean = all(h["all_the_same"] and h["states"] == h["of"] for h in honest)
            out["N3"] = ("passed" if state and halt and clean and not liar["all_the_same"] else "failed",
                         f"the changed state {'found' if state else 'NOT found'}, the halt that is no halt "
                         f"{'found' if halt else 'NOT found'}; the other four {'clean' if clean else 'NOT clean'}")  # fmt: skip
    t1, t2 = (
        f["took"][after].get(first, ["", ""]),
        f["took"][after].get(before, ["", ""]),
    )
    ok = (
        t1[0] == t2[0] == "held"
        and "whoever signed it" in t1[1]
        and "whoever signed it" in t2[1]
    )
    ok = ok and not f["wrong"][after]
    out["N4"] = ("passed" if ok else "failed",
                 f"the liar's first round {t1[0] or 'not given'}, the round that went on from it {t2[0] or 'not given'}; "
                 f"{len(f['wrong'][after])} jobs wrong after, {f['steps'][after]} steps")  # fmt: skip
    others = [f"round-2-machine-{k}-before" for k in places if k != LIAR]
    bad = [
        n
        for n in others
        if not f["as_first"][n]
        or sorted(v[0] for v in f["took"][n].values()) != ["taken"]
    ]
    out["N5"] = ("failed", f"not the first study's: {', '.join(bad)}") if bad else (
        "passed", "the other four places took their own and are the first study's, byte for byte")  # fmt: skip
    return {r: out[r] for r in RULES}


def say(f: dict, v: dict) -> str:
    out = [f"{r}  {how}: {why}" for r, (how, why) in v.items()]
    if f["missing"]:
        return "\n".join(out)
    before = f"round-2-machine-{LIAR}-before"
    out.append("measured:")
    out.append(
        f"  jobs that went out wrong before the check: {len(f['wrong'][before])} of place {LIAR}'s second round"
    )
    went = f["check"].get(before)
    if went:
        out.append(f"  of the round that went on from the lie, the check found {went['same']} of {went['states']} "
                   f"states the same: a state stepped rightly from a wrong one looks right to a check of that step")  # fmt: skip
    for name in sorted(f["steps"]):
        out.append(f"  {name}: {f['steps'][name]} steps")
    out.append(f"  the check stepped {f['check_stepped']} steps")
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
        if a in ("--runs", "--ring", "--against", "--plan") and a[2:] not in opts:
            opts[a[2:]] = next(it, "")
        elif a == "--json":
            opts["json"] = True
        else:
            opts = {}
            break
    if not all(opts.get(k) for k in ("runs", "ring", "against")):
        print(USAGE, file=sys.stderr)
        return 2
    try:
        plan = sweep.load(
            Path(opts.get("plan") or HERE.parents[1] / "study" / "plan.json")
        )
        f = figures(
            plan,
            Path(opts["runs"]),
            machine.ring_of(Path(opts["ring"])),
            Path(opts["against"]),
        )
        v = verdicts(plan, f)
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
