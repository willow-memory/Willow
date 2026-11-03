"""again.py: the questions you keep asking, counted from the record.

    python adapters/stdlib/again/again.py --box DIR [--json]   every repeat
    python adapters/stdlib/again/again.py --box DIR "words"    one question

The record keeps a question as the SHA-256 of its words (its bite key), never
the words, so this can't print a question back. What it can say, exactly:

    again: populated, 2 questions asked more than once, 1 at an offer
    ## make it standing? approve an answer for it, and it's served as yours
      question 3f1c0a9e2b7d  asked 3 times, last 2026-10-22, answered from hives/2026.txt:143
    ## standing: answered by your approval
      question 8d02e6b4c1aa  asked 2 times, last 2026-10-20, answered by your approval proposal:0a6f…

Every repeat is a report, as every report add-on prints one
(adapters/stdlib/ci/README.md, the report contract), and `--json` gives the
same report as one JSON object. Given your words, it says how often you've
asked that one, as it always has.

willow-bot's repetition ladder, by count: asked once, it's answered; twice,
noticed; three times, and every third time after, offered: "make it
standing?" An approved answer is the standing one, and once there is one the
offer stops. Offering is all it does: approving stays yours.

It only reads. Exit codes, the kernel's: 0 nothing waits on you (no repeat,
empty; or repeats, none at an offer); 42 a question is at an offer; 2
refused.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

NAME = "again"
NOTICE_AT = 2  # willow-bot's ladder: the second ask is noticed
OFFER_AT = 3  # and every third ask is offered


def repeats(rows: list[dict]) -> dict[str, dict]:
    """Per bite key: how often asked, when last, and the last thing served."""
    out: dict[str, dict] = {}
    for r in rows:
        if r["kind"] != "bite" or not r.get("bite_key"):
            continue
        e = out.setdefault(r["bite_key"], {"times": 0})
        e["times"] += 1
        e["last"] = r["ts"]
        e["by"] = r.get("answered_by")
        e["served"] = [s["where"] for s in r.get("served", []) if not s.get("echo")]
    return out


def rung(e: dict) -> str:
    if e.get("by"):
        return "standing"
    if e["times"] >= OFFER_AT and e["times"] % OFFER_AT == 0:
        return "offer"
    return "noticed" if e["times"] >= NOTICE_AT else "asked"


def told(e: dict) -> str:
    """How often, when last, and what answered it, on one line."""
    out = f"asked {e['times']} time{'s' * (e['times'] != 1)}, last {e['last'][:10]}, "
    if e.get("by"):
        return out + f"answered by your approval {e['by'][:21]}…"
    if e["served"]:
        return out + f"answered from {', '.join(e['served'])}"
    return out + "nothing in your folder answered it"


def line(key: str, e: dict) -> str:
    out = told(e)
    if rung(e) == "offer":
        out += (
            "\n  make it standing? approve an answer for it, and it's served as yours"
        )
    return out + f"\n  (question {key[:12]})"


#: the report's groups, in its order: what waits on you first
GROUPS = {
    "offer": "make it standing? approve an answer for it, and it's served as yours",
    "noticed": "noticed",
    "standing": "standing: answered by your approval",
}


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


def say(doc: dict, as_json: bool) -> None:
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))


def every_repeat(every: dict[str, dict]) -> tuple[dict, int]:
    """The report of every question asked more than once, by rung, the most
    asked first; and its exit code: 42 when one is at an offer."""
    shown = sorted(
        ((k, e) for k, e in every.items() if e["times"] >= NOTICE_AT),
        key=lambda x: (-x[1]["times"], x[1]["last"]),
    )
    if not shown:
        return report(
            NAME, "empty", "no question asked more than once", []
        ), kernel.ALIVE
    offers = sum(rung(e) == "offer" for _, e in shown)
    said = f"{len(shown)} question{'s' * (len(shown) != 1)} asked more than once"
    if offers:
        said += f", {offers} at an offer"
    groups = [(name, [(f"question {k[:12]}", told(e)) for k, e in shown
                      if rung(e) == r]) for r, name in GROUPS.items()]  # fmt: skip
    doc = report(NAME, "populated", said, groups)
    return doc, kernel.ESCALATE if offers else kernel.ALIVE


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    if len(argv) not in (2, 3) or argv[0] != "--box" or as_json and len(argv) == 3:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(argv[1])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ", file=sys.stderr)
        return kernel.REFUSED
    every = repeats(rows)
    if len(argv) == 3:
        key = kernel.bite_key(argv[2])
        e = every.get(key or "")
        print(line(key, e) if e else "You haven't asked that before.")
        return kernel.ESCALATE if e and rung(e) == "offer" else kernel.ALIVE
    doc, code = every_repeat(every)
    say(doc, as_json)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
