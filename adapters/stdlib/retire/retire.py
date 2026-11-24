"""retire.py: propose setting aside an approved answer that no longer holds; it's aside only once you seal that. Python 3.9+.

    python adapters/stdlib/retire/retire.py --box DIR [--json]
    python adapters/stdlib/retire/retire.py --box DIR propose SUBJECT --because WHY [--instead SUBJECT] [--now TS]
    python adapters/stdlib/retire/retire.py --box DIR propose --stale [--now TS]

An approved answer stands for its question for good: the kernel serves it
first whenever the same words come again, and a seal can't be declined
afterwards. When one stops being true, this is how you say so. `propose`
puts a suggestion at the kernel's door, under the question "retire
proposal:<sha256>": set that answer aside, and why, and what stands instead
if anything does. Nothing is aside yet. It waits on your seal like any other
suggestion, and you can decline it.

    pass  proposal:9c1e…  waiting on your seal
    to set proposal:0a6fde95fa41… aside, seal it with your key:
        python kernel.py seal --box DIR proposal:9c1e…

`propose --stale` asks stale-answers which approvals cite a passage that has
changed or gone, and proposes setting each of those aside, one suggestion
each, so you seal or decline them one at a time.

With no verb it reports, as every report add-on does (adapters/stdlib/ci/README.md,
the report contract; `--json` the same as one JSON object): the answers you
have set aside, the ones proposed and waiting on your seal, and the ones
that no longer hold and that nobody has proposed yet.

    retire: populated, 3 approved; 1 set aside; 1 waiting on your seal; 0 no longer hold
    ## set aside
      proposal:0a6fde95fa41…  at row 14: the county moved the date; instead proposal:77b0c1d2e3f4…
    ## waiting on your seal
      proposal:5d21aa0c9e77…  by proposal:c40e11b2a9d3…: its cited passage is no longer in your folder (notes/sun.md:1)

Setting a retirement aside brings its answer back: the latest seal that
stands is the one that counts.

What it doesn't do: the kernel still serves a set-aside answer for its own
words, since the kernel reads only its own rows; skipping one is the
kernel's to learn, not an add-on's to force. Until then an add-on that reads
your approvals asks this one which are aside, with `set_aside(box, rows)`,
and anything that asks through the kernel can ask "retire proposal:<sha256>"
and be served the retirement you sealed.

Exit codes, the kernel's: 0 nothing waits (empty, or only answers already
aside); 42 a retirement waits on your seal, an answer no longer holds, or a
suggestion was just made; 2 refused: not a box, a record that doesn't verify,
a subject that isn't an approved answer still standing, one already aside or
already proposed or declined, or no reason given.

It writes the record only, through the kernel, and never reads the key.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

NAME = "retire"
USAGE = __doc__.split("\n\n")[1]
PATH = "retire/"  # where a retirement is proposed, inside the box's written/


def question(subj: str) -> str:
    """The words a retirement is proposed and sealed under."""
    return f"retire {subj}"


def proposal(subj: str, because: str, instead: str | None) -> dict:
    data = {"retire": subj, "because": because, "instead": instead}
    return {
        "path": f"{PATH}{subj[9:]}.json",
        "data": json.dumps(data, sort_keys=True, ensure_ascii=False),
        "cites": [],
        "claim": f"set aside {subj}: {because}",
    }


def retires(prop: dict, key: str | None) -> dict | None:
    """What a suggestion sets aside, {retire, because, instead}, or None when
    it is no retirement: its path, its data, and the question it was made
    under must all name the same answer, so nothing else you sealed can be
    read as one."""
    if not str(prop.get("path", "")).startswith(PATH):
        return None
    try:
        data = json.loads(prop["data"])
        subj = data["retire"]
    except (ValueError, KeyError, TypeError):
        return None
    if not isinstance(subj, str) or key != kernel.bite_key(question(subj)):
        return None
    instead = data.get("instead")
    return {"retire": subj, "because": str(data.get("because", "")),
            "instead": instead if isinstance(instead, str) else None}  # fmt: skip


def approvals(box: Path, rows: list[dict]) -> list[tuple[str, dict, dict, str]]:
    """Every approval that still stands on the bytes that were sealed:
    (subject, its seal row, the proposal, its question's key), oldest first."""
    out = []
    for subj, row in sorted(kernel.sealed(box, rows).items(), key=lambda x: x[1]["n"]):
        prop, key, why = kernel.standing(box, rows, subj, row)
        if why is None:
            out.append((subj, row, prop, key))
    return out


def set_aside(box: Path, rows: list[dict]) -> dict[str, dict]:
    """Each approved answer you have set aside, by subject: {by, row, because,
    instead}. A retirement counts only while it stands itself: sealed after
    the answer it names, and not set aside by a later one. So the latest seal
    decides, and setting a retirement aside brings its answer back."""
    held = approvals(box, rows)
    sealed_at = {subj: row["n"] for subj, row, _, _ in held}
    aside: dict[str, dict] = {}
    for subj, row, prop, key in reversed(held):  # the latest first
        r = retires(prop, key)
        if r is None or subj in aside:
            continue
        target = r["retire"]
        if sealed_at.get(target, row["n"]) >= row["n"] or target in aside:
            continue
        aside[target] = {"by": subj, "row": row["n"], "because": r["because"],
                         "instead": r["instead"]}  # fmt: skip
    return aside


def waiting(box: Path, rows: list[dict]) -> dict[str, dict]:
    """Each answer a retirement waits on your seal for, by subject: {by, because}."""
    out: dict[str, dict] = {}
    for subj in kernel.waiting(box, rows):
        try:
            prop = json.loads((box / "proposals" / f"{subj[9:]}.json").read_text())
            r = retires(prop, prop.get("bite_key")) if kernel.subject_of(prop) == subj else None  # fmt: skip
        except (OSError, ValueError, KeyError, TypeError):
            r = None
        if r is not None:
            out.setdefault(r["retire"], {"by": subj, "because": r["because"]})
    return out


def stale_answers():
    """The stale-answers add-on, or None when it isn't beside this one."""
    path = Path(__file__).resolve().parents[1] / "stale-answers" / "stale_answers.py"
    if not path.is_file():
        return None
    mod = types.ModuleType("retire_stale_answers")
    mod.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), mod.__dict__)
    return mod


def stale(box: Path) -> tuple[dict[str, str] | None, str | None]:
    """({answer: why it no longer holds}, None), or (None, why it couldn't look)."""
    sa = stale_answers()
    if sa is None:
        return None, "stale-answers isn't beside this add-on"
    try:
        code, entries = sa.check(box)
    except (
        ValueError
    ) as e:  # a box that reads several places; stale-answers reads one folder
        return None, str(e)
    if code == kernel.REFUSED:
        return None, "; ".join(e["refused"] for e in entries)
    return {
        e["subject"]: "its cited passage is no longer in your folder ("
        + ", ".join(g["was"] for g in e["gone"]) + ")"
        for e in entries if e.get("gone")
    }, None  # fmt: skip


def short(subj: str) -> str:
    return f"{subj[:21]}…"


def refuse(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def why_not(box: Path, rows: list[dict], subj: str, because: str, instead: str | None) -> str | None:  # fmt: skip
    """Why this retirement can't be proposed, or None."""
    held = {s: (prop, key) for s, _, prop, key in approvals(box, rows)}
    aside = set_aside(box, rows)
    if subj not in held:
        return f"{subj} is not an approved answer that still stands in this box"
    if subj in aside:
        return f"{subj} is already set aside, at row {aside[subj]['row']}"
    if not because.strip():
        return "say why it no longer holds: --because WHY"
    if instead is not None:
        if instead == subj:
            return "an answer can't stand instead of itself"
        if (
            instead not in held
            or instead in aside
            or retires(*held[instead]) is not None
        ):
            return f"{instead} is not an approved answer that still stands, to stand instead"
    was = kernel.offered(box, rows, kernel.subject_of(proposal(subj, because, instead)))
    return f"this was proposed before: {was}" if was else None


def propose(box: Path, subj: str, because: str, instead: str | None, ts: str) -> int:
    """One retirement to the kernel's door, under its own question."""
    with contextlib.redirect_stdout(
        io.StringIO()
    ):  # the bite's answer isn't ours to print
        code = kernel.bite(box, question(subj), ts)
    if code == kernel.REFUSED:
        return code
    prop = proposal(subj, because, instead)
    kernel.propose(box, [kernel.canon(prop)], ts)
    print(f"to set {short(subj)} aside, seal it with your key:\n"
          f"    python kernel.py seal --box {box} {kernel.subject_of(prop)}")  # fmt: skip
    return kernel.ESCALATE


def do_propose(box: Path, rows: list[dict], subj: str, because: str, instead: str | None, ts: str) -> int:  # fmt: skip
    why = why_not(box, rows, subj, because, instead)
    return refuse(why) if why else propose(box, subj, because, instead, ts)


def do_stale(box: Path, ts: str) -> int:
    found, why = stale(box)
    if found is None:
        return refuse(why or "stale-answers couldn't look")
    made = []
    for subj, because in found.items():
        rows = kernel.read(box / "record.jsonl")[0]  # each proposal adds rows
        why = why_not(box, rows, subj, because, None)
        if why:
            print(f"left  {short(subj)}  {why}")
            continue
        propose(box, subj, because, None, ts)
        made.append(subj)
    if not found:
        print("nothing to propose: every approved answer's cited passages are still in your folder")  # fmt: skip
    return kernel.ESCALATE if made else kernel.ALIVE


# ── the report: the shape every report add-on prints (ci/README.md) ─────────
def report(addon: str, state: str, said: str, groups: list) -> dict:
    """A report: its state, one line said, and each group's rows (where,
    what); a group named None comes first and has no heading."""
    return {"addon": addon, "state": state, "said": said,
            "groups": [{"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
                       for g, rows in groups if rows]}  # fmt: skip


def report_text(doc: dict) -> str:
    rows = [r for g in doc["groups"] for r in g["rows"]]
    w = min(max((len(r["where"]) for r in rows), default=0), 60)
    out = [f"{doc['addon']}: {doc['state']}, {doc['said']}"]
    for g in doc["groups"]:
        if g["name"] is not None:
            out.append(f"## {g['name']}")
        out += [f"  {r['where']:<{w}}  {r['what']}".rstrip() for r in g["rows"]]
    return "\n".join(out)


def do_report(box: Path, rows: list[dict], as_json: bool) -> int:
    held = approvals(box, rows)
    answers = [s for s, _, prop, key in held if retires(prop, key) is None]
    aside, owed = set_aside(box, rows), waiting(box, rows)
    found, why = stale(box)
    loose = {s: b for s, b in (found or {}).items() if s not in aside and s not in owed}
    groups = [
        ("set aside", [
            (short(s), f"at row {a['row']}: {a['because']}"
             + (f"; instead {short(a['instead'])}" if a["instead"] else ""))
            for s, a in sorted(aside.items(), key=lambda x: x[1]["row"]) if s in answers]),
        ("waiting on your seal", [
            (short(s), f"by {short(o['by'])}: {o['because']}") for s, o in owed.items()]),
        ("no longer holds, not proposed yet", [(short(s), b) for s, b in loose.items()]),
    ]  # fmt: skip
    said = (f"{len(answers)} approved; {len(groups[0][1])} set aside; "
            f"{len(owed)} waiting on your seal; {len(loose)} no longer hold")  # fmt: skip
    if found is None:
        said += f"; stale answers not looked for: {why}"
    doc = report(
        NAME, "populated" if any(r for _, r in groups) else "empty", said, groups
    )
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))
    return kernel.ESCALATE if owed or loose else kernel.ALIVE


def main(argv: list[str]) -> int:
    opts, flags, args, it = {}, set(), [], iter(argv)
    for a in it:
        if a in ("--box", "--because", "--instead", "--now"):
            opts[a] = next(it, "")
        elif a in ("--json", "--stale"):
            flags.add(a)
        else:
            args.append(a)
    verb, rest = (args[0], args[1:]) if args else (None, [])
    named = verb == "propose" and len(rest) == 1 and not flags and "--because" in opts
    swept = verb == "propose" and not rest and flags == {"--stale"} and set(opts) <= {"--box", "--now"}  # fmt: skip
    told = verb is None and flags <= {"--json"} and set(opts) == {"--box"}
    if not opts.get("--box") or not (named or swept or told):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").is_file():
        return refuse(f"{box} isn't a box: make one with kernel.py init")
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return refuse("the record doesn't verify: " + "; ".join(breaks))
    ts = opts.get("--now") or kernel.now()
    if named:
        return do_propose(
            box, rows, rest[0], opts["--because"], opts.get("--instead"), ts
        )
    if swept:
        return do_stale(box, ts)
    return do_report(box, rows, "--json" in flags)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
