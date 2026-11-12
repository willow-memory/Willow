"""told.py: what came back from the strangers run held to its rules, and to the first study's kept runs.

    python demo/shared-runs/door/strangers/told.py --runs DIR --ring FILE --against DIR
        [--plan PLAN] [--json]

DIR holds a folder for each notebook that came back, under its name,
and the liar's `round-1-machine-3.lied.json`, wherever below DIR the
download put them. FILE is the ring strangers_notebooks.py wrote.
`--against` is the first study's kept runs (study/runs).

    T1  every folder is whole by its seal and its signature holds; the
        takers, the checker and places 0, 2 and 4 are in the ring, and
        the first rounds of places 1 and 3 are signed by keys that are
        not
    T2  before the check, the takers of places 1 and 3 held what they
        were given and stepped more than the first study's second round
        did for that place; the others took theirs as enrolled and
        stepped what the first study did
    T3  the check found every kept state and halt of places 0, 1, 2 and
        4 the same, and of place 3 found the changed state not the same
        and the written halt no halt
    T4  after the check, place 1 was taken on the checker's word and its
        second round is the first study's, byte for byte; place 3 was
        still held
    T5  no job of any second round, before or after, came to a byte the
        first study's did not: the same end, outcome and SHA-256

Measured, with no threshold: what being held cost each place in steps;
what the check stepped; the kinds of processor drawn.

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
RULES = ("T1", "T2", "T3", "T4", "T5")
STRANGER, LIAR = 1, 3
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
            "check", f"round-2-machine-{STRANGER}-after", f"round-2-machine-{LIAR}-after"]  # fmt: skip


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
    f["took"], f["steps"], f["first_study"], f["as_first"], f["wrong"] = (
        {},
        {},
        {},
        {},
        [],
    )
    for name in f["wanted"]:
        if not name.startswith("round-2-"):
            continue
        k = int(name.split("-")[3])
        acts = rows(got[name] / "acts.jsonl")
        f["took"][name] = {
            n: [v["how"], v["why"]] for n, v in seal(got[name])["took_in"].items()
        }
        f["steps"][name] = sum(a["stepped"] for a in acts)
        f["first_study"][name] = sum(a["stepped"] for a in theirs[k])
        f["as_first"][name] = [[a[x] for x in SAME] for a in acts] == [
            [a[x] for x in SAME] for a in theirs[k]
        ]
        f["wrong"] += [
            f"{name}: {a['job']}"
            for a in acts
            if [a[x] for x in ENDS] != ends.get(a["job"])
        ]
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
    odd = (f"round-1-machine-{STRANGER}", f"round-1-machine-{LIAR}")
    bad = [n for n, code in f["standing"].items() if code != (42 if n in odd else 0)]
    out["T1"] = ("failed", f"not standing as it should: {', '.join(bad)}") if bad else (
        "passed", f"{len(f['standing'])} folders whole; two first rounds signed by keys the ring does not hold")  # fmt: skip

    def how(name: str) -> list[str]:
        return sorted(v[0] for v in f["took"][name].values())

    wrong = []
    for k in places:
        name = f"round-2-machine-{k}-before"
        if k in (STRANGER, LIAR):
            if how(name) != ["held"] or f["steps"][name] <= f["first_study"][name]:
                wrong.append(name)
        elif how(name) != ["taken"] or not f["as_first"][name]:
            wrong.append(name)
    before = [f"round-2-machine-{k}-before" for k in (STRANGER, LIAR)]
    out["T2"] = ("failed", f"not as it should be: {', '.join(wrong)}") if wrong else (
        "passed", "; ".join(f"{n} held, {f['steps'][n]} steps where the first study stepped {f['first_study'][n]}"
                            for n in before))  # fmt: skip
    liar = f["check"].get(f"round-1-machine-{LIAR}")
    honest = [f["check"].get(f"round-1-machine-{k}") for k in places if k != LIAR]
    lied = f["lied"]
    if lied is None or liar is None or None in honest:
        out["T3"] = (
            "not tested",
            "the lie's own account, or a folder's check, did not come back",
        )
    else:
        mine = [x for x in f["not_same"] if x[0] == f"round-1-machine-{LIAR}"]
        state = ["check", *lied["state"]] in [x[1:] for x in mine]
        halt = ["halt-check", *lied["halt"]] in [x[1:] for x in mine]
        clean = all(h["all_the_same"] and h["states"] == h["of"] for h in honest)
        elsewhere = [x for x in f["not_same"] if x[0] != f"round-1-machine-{LIAR}"]
        ok = state and halt and clean and not elsewhere and not liar["all_the_same"]
        out["T3"] = ("passed" if ok else "failed",
                     f"the changed state {'found' if state else 'NOT found'}, the halt that is no halt "
                     f"{'found' if halt else 'NOT found'}; {len(mine)} of the liar's {liar['states']} states and "
                     f"halts not the same; the other four {'clean' if clean and not elsewhere else 'NOT clean'}")  # fmt: skip
    a1, a3 = f"round-2-machine-{STRANGER}-after", f"round-2-machine-{LIAR}-after"
    took1 = f["took"][a1].get(f"round-1-machine-{STRANGER}", ["", ""])
    took3 = f["took"][a3].get(f"round-1-machine-{LIAR}", ["", ""])
    ok = (
        took1[0] == "taken"
        and "stepped again" in took1[1]
        and f["as_first"][a1]
        and took3[0] == "held"
    )
    out["T4"] = ("passed" if ok else "failed",
                 f"place {STRANGER}: {took1[0]}, {f['steps'][a1]} steps (the first study's {f['first_study'][a1]}); "
                 f"place {LIAR}: {took3[0]}, {f['steps'][a3]} steps")  # fmt: skip
    out["T5"] = ("failed", f"not the first study's end: {', '.join(f['wrong'][:6])}") if f["wrong"] else (
        "passed", f"every job of {len(f['steps'])} second rounds ends as the first study's did")  # fmt: skip
    return {r: out[r] for r in RULES}


def say(f: dict, v: dict) -> str:
    out = [f"{r}  {how}: {why}" for r, (how, why) in v.items()]
    if f["missing"]:
        return "\n".join(out)
    out.append("measured:")
    for name in sorted(f["steps"]):
        extra = f["steps"][name] - f["first_study"][name]
        out.append(
            f"  {name}: {f['steps'][name]} steps, {extra} more than the first study's second round there"
        )
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
