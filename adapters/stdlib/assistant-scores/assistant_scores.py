"""assistant_scores.py: how often each assistant's suggestions were sealed or
declined, from the record. Python 3.9+, stdlib only.

    python adapters/stdlib/assistant-scores/assistant_scores.py --box DIR [--json]

Each suggestion that passed the kernel's door is read from its proposal file
(only while the file is the bytes its subject names) and its claim read by
the suggestions contract's one form (openai-compatible's `read_claim`): who
answered, where, at what settings. Suggestions are counted by those three
together, so one model asked at two reasoning levels is two rows, and each
says how many you sealed, how many you declined and how many still wait:

    assistant-scores: populated, 9 suggestions from 2 assistants, 6 decided by you
    ## assistants
      qwen3:8b at http://127.0.0.1:11434/v1 (temperature 0, seed 0, reasoning low)  4 sealed, 1 declined, 1 waiting; 4 of the 5 decided sealed
      qwen3:8b at http://127.0.0.1:11434/v1 (temperature 0, seed 0)                  1 sealed, 0 declined, 2 waiting; 1 of the 1 decided sealed
    ## no assistant named
      proposals  1 suggestion whose claim names no assistant: yours, or another's

A seal or a No counts only while its proof holds under your key (the
kernel's `sealed` and `declined`, so the key is read there and nowhere here).
A claim from before the contract said its settings is counted with
`(settings not said)`. A claim is the proposer's own words, not an attested
card: this counts what the record says, and judges no model.

It prints a report (adapters/stdlib/ci/README.md, the report contract), the
same as JSON with --json. Exit codes, the kernel's: 0 a report (populated or
empty); 2 refused (a bad command line, not a box, a record that doesn't
verify).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "willow_openai_compatible_for_assistant_scores",
    HERE.parent / "openai-compatible" / "openai_compatible.py",
)
oc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oc)  # read_claim: the suggestions contract's one form

NAME = "assistant-scores"
USAGE = "usage: assistant_scores.py --box DIR [--json]"


def report(addon: str, state: str, said: str, groups: list) -> dict:
    """A report, the contract's shape: groups of (name, [(where, what)])."""
    return {"addon": addon, "state": state, "said": said,
            "groups": [{"name": n, "rows": [{"where": w, "what": t} for w, t in rs]}
                       for n, rs in groups if rs]}  # fmt: skip


def report_text(doc: dict) -> str:
    rows = [r for g in doc["groups"] for r in g["rows"]]
    out = [f"{doc['addon']}: {doc['state']}, {doc['said']}"]
    if not rows:
        return out[0]
    w = min(max(len(r["where"]) for r in rows), 60)
    for g in doc["groups"]:
        if g["name"] is not None:
            out.append(f"## {g['name']}")
        out += [f"  {r['where']:<{w}}  {r['what']}".rstrip() for r in g["rows"]]
    return "\n".join(out)


def say(doc: dict, as_json: bool) -> None:
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))


def proposal_file(box: Path, subj: str) -> tuple[dict | None, str | None]:
    """(the proposal, None), or (None, why it can't be read as proposed)."""
    path = box / "proposals" / f"{subj[9:]}.json"
    try:
        prop = json.loads(path.read_text(encoding="utf-8"))
        if kernel.subject_of(prop) != subj:
            return None, "its proposal file is not the bytes proposed"
    except OSError:
        return None, "its proposal file is missing"
    except (ValueError, KeyError, TypeError):
        return None, "its proposal file is not the bytes proposed"
    return prop, None


def assistant(claim: dict) -> str:
    """Who answered, where and at what settings, as one name."""
    said = ", ".join(f"{k} {v}" for k, v in claim["settings"].items())
    return f"{claim['who']} {claim['where']} ({said or 'settings not said'})"


def scores(box: Path, rows: list[dict]) -> tuple[dict, int, list]:
    """({assistant: {sealed, declined, waiting}}, suggestions naming none,
    [(subject, why it wasn't read)]), each subject counted once."""
    good, no = kernel.sealed(box, rows), kernel.declined(box, rows)
    by: dict[str, dict[str, int]] = {}
    unnamed, unread, seen = 0, [], set()
    for r in rows:
        subj = r.get("subject")
        if r["kind"] != "proposal" or r.get("verdict") != "pass" or subj in seen:
            continue
        seen.add(subj)
        prop, why = proposal_file(box, subj)
        if why:
            unread.append((subj, why))
            continue
        claim = oc.read_claim(str(prop.get("claim", "")))
        if claim is None:
            unnamed += 1
            continue
        got = by.setdefault(
            assistant(claim), {"sealed": 0, "declined": 0, "waiting": 0}
        )
        got["sealed" if subj in good else "declined" if subj in no else "waiting"] += 1
    return by, unnamed, unread


def what(n: dict[str, int]) -> str:
    decided = n["sealed"] + n["declined"]
    out = f"{n['sealed']} sealed, {n['declined']} declined, {n['waiting']} waiting"
    return out + (f"; {n['sealed']} of the {decided} decided sealed" if decided else "")


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    if len(argv) != 2 or argv[0] != "--box" or not argv[1]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    box = Path(argv[1])
    if not (box / "kernel.json").is_file():
        print(f"refused: {box} is not a box; kernel.py init makes one", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print(
            "refused: the record doesn't verify:", *breaks, sep="\n  ", file=sys.stderr
        )
        return kernel.REFUSED
    by, unnamed, unread = scores(box, rows)
    total = sum(sum(n.values()) for n in by.values())
    decided = sum(n["sealed"] + n["declined"] for n in by.values())
    order = sorted(by, key=lambda a: (-sum(by[a].values()), a))
    groups = [
        ("assistants", [(a, what(by[a])) for a in order]),
        ("no assistant named", [("proposals", f"{unnamed} suggestion{'s' * (unnamed != 1)}"
                                 " whose claim names no assistant: yours, or another's")]
         if unnamed else []),
        ("not read", [(s[:21] + "…", why) for s, why in unread]),
    ]  # fmt: skip
    doc = report(NAME, "populated", "", groups)
    if not doc["groups"]:
        say(report(NAME, "empty", "no suggestion is on the record", []), as_json)
        return kernel.ALIVE
    doc["said"] = (
        f"{total} suggestion{'s' * (total != 1)} from {len(by)} assistant"
        f"{'s' * (len(by) != 1)}, {decided} decided by you"
        if by
        else "no assistant's suggestion is on the record"
    )
    say(doc, as_json)
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
