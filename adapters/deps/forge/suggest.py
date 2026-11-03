"""suggest.py: the Forge's matchmaker over this willow's add-on cards.
Python 3.11+ (forge-play's floor), forge-play 0.10 or newer.

    python adapters/deps/forge/suggest.py --box DIR "what you want done" [--json | --plan]

A sentence in, the add-ons it names or means out. The Forge's card box reads
every card beside this script (built, and the ideas in adapters/planned.json)
as rows for its keyword scan: a card's name, and the lines of
ui/search-words.txt that point at it, are what a sentence can hit. What comes
out is a report (adapters/stdlib/ci/README.md, the report contract), a group
per kind of thing:

    forge: populated, 2 forks wait on you
    ## fork “email”
      adapters/stdlib/apple-mail/README.md  apple-mail: Apple Mail's .emlx ...
      adapters/stdlib/mail/README.md        mail: Email in .eml and mbox ...
    ## fork “due”
      ...

    steps   an add-on the sentence reaches and nothing else does: one line
            for a stack file, `- NAME -- --box {box}`
    fork    one word that reaches several add-ons ("email": mail, apple-mail):
            a decision with the cards as options and their lines as tradeoffs,
            for the Forge's checkpoint to put to the person, once, and
            remember
    ideas   an add-on the sentence names that isn't built yet

--json prints the same report as one JSON object. --plan prints the whole as
the Forge reads it: the cards counted, the steps, the forks, the ideas, and
`plan`, a document forge.plan_shape validates, forge.decision_extract turns
into decisions and forge.build_loop resolves. No model, no ranking: a card is
here because it was named or an alias line names it, and the report says
which.

It only reads: the cards, the alias file, and the box's record to see it is
one. Nothing is proposed and nothing is written; that is the next add-on's
job, once the person has settled the forks. Exit codes, the report's: 0
steps found and nothing waits on you, or nothing named (`empty`); 42 a fork
waits on you (`populated`), or forge-play missing or older than 0.10
(`unreachable`, said); 2 refused (a bad command line, a folder that isn't a
box or whose record doesn't verify, a card beside this script that won't
read).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

NAME = "forge"
APP = "willow-stack"
NEEDS = "forge-play 0.10 or newer is not installed: pip install -r adapters/deps/forge/requirements.txt"


# ── the report: the shape every report add-on prints (ci/README.md) ─────────
def report(addon: str, state: str, said: str, groups: list) -> dict:
    """A report: its state, one line said, and each group's rows (where,
    what); a group named None comes first and has no heading."""
    return {"addon": addon, "state": state, "said": said,
            "groups": [{"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
                       for g, rows in groups if rows]}  # fmt: skip


def report_text(doc: dict) -> str:
    """A report as every report add-on prints it: the same twenty lines each
    keeps, held to this one by test_contract.py."""
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


def forge():
    """The Forge's card box and plan shape, or None when forge-play is
    missing or too old to have them. Imported here, not at the top, so a
    bad command line is refused the same with or without it."""
    try:
        from forge import card_box, card_table, plan_shape, willow_record
    except ImportError:
        return None
    return card_box, card_table, plan_shape, willow_record


def is_box(box: Path) -> str | None:
    """Why `box` can't be used, or None: not a box, or a record that
    doesn't verify. Nothing is read past a break."""
    if not (box / "kernel.json").is_file():
        return f"{box} is not a box (no kernel.json)"
    _, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return "the record doesn't verify: " + "; ".join(breaks)
    return None


def promises(card) -> str:
    bits = [f"writes {card.writes or '?'}", f"network {card.network or '?'}"]
    if card.needs:
        bits.append(f"needs {card.needs}")
    if not card.built:
        bits.append("an idea, not built")
    return "; ".join(bits)


def tradeoff(card) -> str:
    return f"{card.line} ({promises(card)})"


def step_line(name: str) -> str:
    return f"- {name} -- --box {{box}}\n"


def plan(box, hits, shape, rec) -> dict:
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
            ideas.append(
                {
                    "name": cand.name,
                    "line": card.line,
                    "why": cand.why,
                    "where": card.where,
                }
            )
            continue
        steps.append({"name": cand.name, "line": card.line, "why": cand.why, "where": card.where,
                      "promises": promises(card)})  # fmt: skip
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
        entries.append(
            shape.Fork(
                decision_type=rec.decision_type(word),
                surface=f"“{word}” could be {', '.join(names)}: which add-on?",
                options=tuple(options),
                recommended=None,
                confidence=None,
                resolves=resolves,
            )
        )
        fork_docs[word] = [
            {"name": n, "where": by_name[n].where, "tradeoff": o.tradeoff}
            for n, o in zip(names, options)
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


def to_report(out: dict) -> tuple[dict, int]:
    """The plan as a report, and the exit code: a fork waits on you (42), or
    nothing does (0)."""
    groups = [
        (
            "steps",
            [
                (s["where"], f"{s['name']}: {s['line']} ({s['promises']})")
                for s in out["steps"]
            ],
        )
    ]
    for word, options in out["forks"].items():
        groups.append(
            (
                f"fork “{word}”",
                [(o["where"], f"{o['name']}: {o['tradeoff']}") for o in options],
            )
        )
    groups.append(
        (
            "ideas",
            [
                (i["where"], f"{i['name']}: {i['line']} (not built)")
                for i in out["ideas"]
            ],
        )
    )
    n_forks, n_steps = len(out["forks"]), len(out["steps"])
    if n_forks:
        said = f"{n_forks} fork{'s wait' if n_forks != 1 else ' waits'} on you"
        return report(NAME, "populated", said, groups), kernel.ESCALATE
    if n_steps:
        said = f"{n_steps} step{'s' if n_steps != 1 else ''}, nothing waits on you"
        return report(NAME, "populated", said, groups), kernel.ALIVE
    if out["ideas"]:
        return report(
            NAME, "populated", "only ideas, nothing built to run", groups
        ), kernel.ALIVE
    said = "nothing named: no card or alias line matched; add a line to ui/search-words.txt if one should"
    return report(NAME, "empty", said, []), kernel.ALIVE


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    p = argparse.ArgumentParser(prog="suggest.py", description=__doc__.splitlines()[0])
    p.add_argument("sentence", help="what you want done, in your own words")
    p.add_argument(
        "--box", required=True, help="your record; only read, to see it is one"
    )
    p.add_argument(
        "--plan", action="store_true", help="the plan as the Forge reads it, as JSON"
    )
    a = p.parse_args(argv)
    why = is_box(Path(a.box))
    if why:
        print("refused:", why, file=sys.stderr)
        return kernel.REFUSED
    got = forge()
    if got is None:
        say(report(NAME, "unreachable", NEEDS, []), as_json)
        return kernel.ESCALATE
    card_box, card_table, shape, rec = got
    try:
        cards = card_box.CardBox(ROOT)
    except card_table.CardTableError as e:  # a card beside this script that won't read
        print("refused:", e, file=sys.stderr)
        return kernel.REFUSED
    out = plan(cards, cards.scan(a.sentence), shape, rec)
    doc, code = to_report(out)
    if a.plan:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        say(doc, as_json)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
