"""suggest.py: the Forge's matchmaker over this willow's add-on cards.
Python 3.11+ (forge-play's floor), forge-play 0.10 or newer.

    python adapters/deps/forge/suggest.py --box DIR "what you want done" [--json]

A sentence in, the add-ons it names or means out. The Forge's card box reads
every card beside this script (built, and the ideas in adapters/planned.json)
as rows for its keyword scan: a card's name, and the lines of
ui/search-words.txt that point at it, are what a sentence can hit. What comes
out is a plan in the Forge's own shape:

    step    an add-on the sentence reaches and nothing else does: one line
            for a stack file, `- NAME -- --box {box}`
    fork    one word that reaches several add-ons ("email": mail, apple-mail):
            a decision with the cards as options and their lines as tradeoffs,
            for the Forge's checkpoint to put to the person, once, and
            remember
    idea    an add-on the sentence names that isn't built yet

--json prints the whole: the cards counted, the steps, the forks, the ideas,
and `plan`, a document forge.plan_shape validates and forge.decision_extract
turns into decisions. No model, no ranking: a card is here because it was
named or an alias line names it, and the record says which.

It only reads: the cards, the alias file, and the box's record to see it is
one. Nothing is proposed and nothing is written; that is the next add-on's
job, once the person has settled the forks. Exit codes, the kernel's: 0 steps
found and nothing waits on you; 42 a fork waits on you, or nothing was named;
2 refused (a bad command line, a folder that isn't a box or whose record
doesn't verify, forge-play missing or older than 0.10).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

APP = "willow-stack"
NEEDS = "forge-play 0.10 or newer: pip install -r adapters/deps/forge/requirements.txt"


def forge():
    """The Forge's card box and plan shape, or None when forge-play is
    missing or too old to have them. Imported here, not at the top, so a
    bad command line is refused the same with or without it."""
    try:
        from forge import card_box, card_table, plan_shape
    except ImportError:
        return None
    return card_box, card_table, plan_shape


def is_box(box: Path) -> str | None:
    """Why `box` can't be used, or None: not a box, or a record that
    doesn't verify. Nothing is read past a break."""
    if not (box / "kernel.json").is_file():
        return f"{box} is not a box (no kernel.json)"
    _, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return "the record doesn't verify: " + "; ".join(breaks)
    return None


def decision_type(word: str) -> str:
    """The fork's calibration key: the word said, in the Forge's charset."""
    return "willow-" + re.sub(r"[^A-Za-z0-9_.-]+", "-", word).strip("-")


def tradeoff(card) -> str:
    out = card.line
    bits = [f"writes {card.writes or '?'}", f"network {card.network or '?'}"]
    if card.needs:
        bits.append(f"needs {card.needs}")
    if not card.built:
        bits.append("an idea, not built")
    return f"{out} ({'; '.join(bits)})"


def step_line(name: str) -> str:
    return f"- {name} -- --box {{box}}\n"


def plan(box, hits, shape) -> dict:
    """{cards, steps, forks, ideas, plan}: what the sentence reaches, and the
    Forge's plan document (or None when there is nothing to run)."""
    found = box.lookup(hits)
    forks = box.forks(hits)
    by_name = {c.name: c for c in box.cards}
    in_fork = {n for names in forks.values() for n in names}
    steps, ideas, entries = [], [], []
    for cand in found:
        card = by_name[cand.name]
        if cand.name in in_fork:
            continue
        if not card.built:
            ideas.append({"name": cand.name, "line": card.line, "why": cand.why})
            continue
        steps.append({"name": cand.name, "line": card.line, "why": cand.why,
                      "writes": card.writes, "network": card.network, "needs": card.needs})  # fmt: skip
        entries.append(
            shape.FileWrite(
                dest_path=f"steps/{cand.name}.md", content=step_line(cand.name)
            )
        )
    fork_docs = {}
    for word, names in forks.items():
        options, resolves = [], {}
        for n in names:
            card = by_name[n]
            options.append(shape.ForkOption(label=n, tradeoff=tradeoff(card)))
            resolves[n] = (
                (shape.FileWrite(dest_path=f"steps/{n}.md", content=step_line(n)),)
                if card.built
                else ()
            )
        fork = shape.Fork(
            decision_type=decision_type(word),
            surface=f"“{word}” could be {', '.join(names)}: which add-on?",
            options=tuple(options),
            recommended=None,
            confidence=None,
            resolves=resolves,
        )
        entries.append(fork)
        fork_docs[word] = [
            {"name": n, "tradeoff": o.tradeoff} for n, o in zip(names, options)
        ]
    doc = (
        shape.PlanDoc(app_name=APP, entries=tuple(entries)).to_dict()
        if entries
        else None
    )
    if doc is not None:
        shape.validate(doc)  # the Forge's own check, before anyone is told it is a plan
    built = sum(1 for c in box.cards if c.built)
    return {
        "cards": {"built": built, "ideas": len(box.cards) - built},
        "steps": steps,
        "forks": fork_docs,
        "ideas": ideas,
        "plan": doc,
    }


def say(out: dict) -> None:
    c = out["cards"]
    print(f"cards   {c['built']} built, {c['ideas']} ideas, read beside this script")
    for s in out["steps"]:
        needs = f"; needs {s['needs']}" if s["needs"] else ""
        print(
            f"step    {s['name']:<18} {s['line']}  (writes {s['writes']}; network {s['network']}{needs})"
        )
    for word, options in out["forks"].items():
        print(f"fork    “{word}” could be:")
        for o in options:
            print(f"          {o['name']:<16} {o['tradeoff']}")
    for i in out["ideas"]:
        print(f"idea    {i['name']:<18} {i['line']}  (not built)")
    if not out["steps"] and not out["forks"] and not out["ideas"]:
        print(
            "nothing named: no card or alias line matched; add a line to ui/search-words.txt if one should"
        )
    elif out["forks"]:
        n = len(out["forks"])
        print(f"{n} fork{'s wait' if n != 1 else ' waits'} on you")


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="suggest.py", description=__doc__.splitlines()[0])
    p.add_argument("sentence", help="what you want done, in your own words")
    p.add_argument(
        "--box", required=True, help="your record; only read, to see it is one"
    )
    p.add_argument("--json", action="store_true", help="the plan as the Forge reads it")
    a = p.parse_args(argv)
    why = is_box(Path(a.box))
    if why:
        print("refused:", why, file=sys.stderr)
        return kernel.REFUSED
    got = forge()
    if got is None:
        print("refused:", NEEDS, file=sys.stderr)
        return kernel.REFUSED
    card_box, card_table, shape = got
    try:
        box = card_box.CardBox(ROOT)
    except card_table.CardTableError as e:  # a card beside this script that won't read
        print("refused:", e, file=sys.stderr)
        return kernel.REFUSED
    out = plan(box, box.scan(a.sentence), shape)
    if a.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        say(out)
    if out["steps"] and not out["forks"]:
        return kernel.ALIVE
    return kernel.ESCALATE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
