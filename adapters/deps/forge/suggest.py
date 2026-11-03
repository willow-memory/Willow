"""suggest.py: the Forge's matchmaker over this willow's add-on cards.
Python 3.11+ (forge-play's floor), forge-play 0.10 or newer.

    python adapters/deps/forge/suggest.py suggest --box DIR "what you want done" [--json]
    python adapters/deps/forge/suggest.py propose --box DIR "what you want done"
                                                  --choose WORD=NAME ... [--why WORD=REASON ...]

A sentence in, the add-ons it names or means out. The Forge's card box reads
every card beside this script (built, and the ideas in adapters/planned.json)
as rows for its keyword scan: a card's name, and the lines of
ui/search-words.txt that point at it, are what a sentence can hit. `suggest`
says what comes out, as a plan in the Forge's own shape:

    step    an add-on the sentence reaches and nothing else does: one line
            for a stack file, `- NAME -- --box {box}`
    fork    one word that reaches several add-ons ("email": mail, apple-mail):
            a decision with the cards as options and their lines as tradeoffs
    sealed  a fork you settled before, read from your record: the kernel
            serves it only while its seal proves under your key, so it is a
            step, not a question, and `suggest` asks you nothing twice
    idea    an add-on the sentence names that isn't built yet

A stack you sealed for these very words is served first, as the kernel
serves any sealed answer, and nothing else is asked.

`propose` settles the open forks with `--choose WORD=NAME` (and a reason with
`--why WORD=...`) and hands the result to the kernel's door, nothing more:
one proposal per settled fork, under the words `forge decision willow-WORD`,
and one for the stack, under your sentence. Each waits on your seal
(`python kernel.py seal --box DIR proposal:...`); nothing is an answer before
that, and nothing runs. It carries the card's name, line and SHA-256, so what
you sealed is what you were shown.

--json prints the whole: the cards counted, the steps, the forks, what is
sealed, the ideas, and `plan`, a document forge.plan_shape validates and
forge.decision_extract turns into decisions. No model, no ranking: a card is
here because it was named or an alias line names it, and the record says
which.

Exit codes, the kernel's: 0 steps found and nothing waits on you, or a
sealed stack for these words; 42 a fork waits on you, nothing was named, or
(propose) your seal is waited on; 2 refused (a bad command line, a folder
that isn't a box or whose record doesn't verify, a fork left unsettled or
settled with an option not on offer, forge-play missing or older than 0.10).
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

APP = "willow-stack"
STACK_PATH = "forge/stack.md"
NEEDS = "forge-play 0.10 or newer: pip install -r adapters/deps/forge/requirements.txt"


def forge():
    """The Forge's card box, plan shape and record naming, or None when
    forge-play is missing or too old to have them. Imported here, not at the
    top, so a bad command line is refused the same with or without it."""
    try:
        from forge import card_box, card_table, plan_shape, willow_record
    except ImportError:
        return None
    return card_box, card_table, plan_shape, willow_record


def quiet(fn, *args) -> tuple[int, str]:
    """A kernel verb run with its printing caught: (exit code, what it said)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = fn(*args)
    return code, out.getvalue()


def is_box(box: Path) -> str | None:
    """Why `box` can't be used, or None: not a box, or a record that
    doesn't verify. Nothing is read past a break."""
    if not (box / "kernel.json").is_file():
        return f"{box} is not a box (no kernel.json)"
    _, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return "the record doesn't verify: " + "; ".join(breaks)
    return None


def on_record(box: Path, rec) -> tuple[dict, dict]:
    """What the person sealed, through the kernel: ({decision_type: {chose,
    word, row, subject}}, {bite_key: {row, subject, text}}). The key is the
    decision type, `willow-<word>`, the same words the Forge asks the kernel
    for, so a decision the Forge's build loop proposed here is read the same
    as one this script proposed. A seal counts only while
    its proof holds under the key and the proposal still hashes to what was
    sealed (kernel.sealed, kernel.standing); the key is the kernel's to read,
    never this script's. The FIRST standing seal for a word is the one kept:
    that is what the kernel's bite serves for a question, so the Forge, which
    asks the kernel, reads the same answer as this does. A later seal for the
    same word waits its turn until the first no longer stands."""
    rows, _ = kernel.read(box / "record.jsonl")
    decisions, stacks = {}, {}
    for subj, row in kernel.sealed(box, rows).items():
        prop, asked, why = kernel.standing(box, rows, subj, row)
        if why is not None:
            continue
        if prop["path"] == STACK_PATH:
            stacks.setdefault(
                asked, {"row": row["n"], "subject": subj, "text": prop["data"]}
            )
        elif prop["path"].startswith(rec.DECISION_PATH.split("{")[0]):
            try:
                data = json.loads(prop["data"])
            except ValueError:
                continue
            if isinstance(data, dict) and isinstance(data.get("chose"), str):
                dt = data.get("decision_type")
                if not isinstance(dt, str) and isinstance(data.get("word"), str):
                    dt = rec.decision_type(data["word"])
                if isinstance(dt, str):
                    decisions.setdefault(
                        dt,
                        {"chose": data["chose"], "word": data.get("word", ""),
                         "row": row["n"], "subject": subj},
                    )  # fmt: skip
    return decisions, stacks


def tradeoff(card) -> str:
    bits = [f"writes {card.writes or '?'}", f"network {card.network or '?'}"]
    if card.needs:
        bits.append(f"needs {card.needs}")
    if not card.built:
        bits.append("an idea, not built")
    return f"{card.line} ({'; '.join(bits)})"


def step_line(name: str) -> str:
    return f"- {name} -- --box {{box}}\n"


def step_of(card, why: str) -> dict:
    return {"name": card.name, "line": card.line, "why": why, "writes": card.writes,
            "network": card.network, "needs": card.needs}  # fmt: skip


def plan(box, hits, shape, rec, sealed: dict) -> dict:
    """{cards, steps, forks, sealed, ideas, plan}: what the sentence reaches,
    what the record settled, and the Forge's plan document (or None when
    there is nothing to run)."""
    found = box.lookup(hits)
    forks = box.forks(hits)
    by_name = {c.name: c for c in box.cards}
    settled, open_forks = {}, {}
    for word, names in forks.items():
        got = sealed.get(rec.decision_type(word))
        if got and got["chose"] in names:
            settled[word] = {**got, "decision_type": rec.decision_type(word)}
        else:
            open_forks[word] = names
            if got:
                settled[word] = {
                    **got,
                    "stale": f"{got['chose']} no longer does “{word}” here",
                }
    in_fork = {n for names in open_forks.values() for n in names}
    chosen = {got["chose"]: word for word, got in settled.items() if "stale" not in got}
    steps, ideas, entries = [], [], []
    for cand in found:
        card = by_name[cand.name]
        if cand.name in in_fork:
            continue
        if cand.name in chosen:
            why = f"you sealed it for “{chosen[cand.name]}” (row {settled[chosen[cand.name]]['row']})"
        elif card.name in {n for names in forks.values() for n in names}:
            continue  # the other option of a settled fork
        else:
            why = cand.why
        if not card.built:
            ideas.append({"name": cand.name, "line": card.line, "why": why})
            continue
        steps.append(step_of(card, why))
        entries.append(
            shape.FileWrite(
                dest_path=f"steps/{cand.name}.md", content=step_line(cand.name)
            )
        )
    fork_docs = {}
    for word, names in open_forks.items():
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
        "sealed": settled,
        "ideas": ideas,
        "plan": doc,
    }


def say(out: dict) -> None:
    c = out["cards"]
    print(f"cards   {c['built']} built, {c['ideas']} ideas, read beside this script")
    if "stack" in out:
        s = out["stack"]
        print(
            f"stack   sealed for these words at row {s['row']} ({s['subject']}); nothing to ask:"
        )
        for ln in s["text"].splitlines():
            print(f"        {ln}")
        return
    for s in out["steps"]:
        needs = f"; needs {s['needs']}" if s["needs"] else ""
        print(
            f"step    {s['name']:<18} {s['line']}  (writes {s['writes']}; network {s['network']}{needs})"
        )
    for word, got in out["sealed"].items():
        if "stale" in got:
            print(
                f"sealed  “{word}”: {got['stale']} (row {got['row']}); asked again below"
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


def pairs(items: list[str], what: str) -> tuple[dict[str, str], str | None]:
    """`WORD=VALUE` arguments as a dict, or why one isn't."""
    out = {}
    for it in items or []:
        word, sep, value = it.partition("=")
        if not sep or not word.strip() or not value.strip():
            return {}, f"{what} takes WORD=VALUE, not {it!r}"
        out[word.strip()] = value.strip()
    return out, None


def propose(
    box: Path, sentence: str, out: dict, cards, choose: dict, why: dict, rec
) -> int:
    """Each settled fork, and the stack, to the kernel's door. Refuses before
    writing anything when a fork is left open or settled with an option not
    on offer; after that every write is the kernel's."""
    for word, options in out["forks"].items():
        names = [o["name"] for o in options]
        if word not in choose:
            print(
                f"refused: “{word}” is not settled: --choose {word}={'|'.join(names)}",
                file=sys.stderr,
            )
            return kernel.REFUSED
        if choose[word] not in names:
            print(f"refused: {choose[word]} is not an option for “{word}”: {', '.join(names)}", file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
    for word in choose:
        if word not in out["forks"]:
            print(f"refused: nothing to choose for “{word}”", file=sys.stderr)
            return kernel.REFUSED
    by_name = {c.name: c for c in cards}
    run = [s["name"] for s in out["steps"]] + [
        n for n in choose.values() if by_name[n].built
    ]
    if not run:
        print(
            "refused: nothing to propose: no step and no settled fork", file=sys.stderr
        )
        return kernel.REFUSED
    ts = kernel.now()
    waiting = []
    for word, name in choose.items():
        card = by_name[name]
        others = [o["name"] for o in out["forks"][word] if o["name"] != name]
        dt = rec.decision_type(word)
        pinned = hashlib.sha256((ROOT / card.where).read_bytes()).hexdigest()
        data = {
            "word": word,
            "decision_type": dt,
            "chose": name,
            "over": others,
            "why": why.get(word, ""),
            "card": {
                "name": card.name,
                "line": card.line,
                "where": card.where,
                "sha256": pinned,
            },
        }
        prop = {
            "path": rec.DECISION_PATH.format(dt),
            "data": json.dumps(data, sort_keys=True, ensure_ascii=False),
            "cites": [],
            "claim": f"for “{word}”: {name} over {', '.join(others)}; {why.get(word) or 'no reason given'}",
        }
        code, said = quiet(kernel.bite, box, rec.question(dt), ts)
        if code == kernel.REFUSED:
            print("refused:", said.strip(), file=sys.stderr)
            return kernel.REFUSED
        code, said = quiet(
            kernel.propose, box, [json.dumps(prop, ensure_ascii=False)], ts
        )
        if not said.startswith("pass "):
            print("refused:", said.strip(), file=sys.stderr)
            return kernel.REFUSED
        waiting.append((said.split()[1], prop["path"], name))
    text = f"# {sentence}\n\n## for “{sentence}”\n" + "".join(step_line(n) for n in run)
    prop = {
        "path": STACK_PATH,
        "data": text,
        "cites": [],
        "claim": f"a stack for “{sentence}”: {', '.join(run)}",
    }
    code, said = quiet(kernel.bite, box, sentence, ts)
    if code == kernel.REFUSED:
        print("refused:", said.strip(), file=sys.stderr)
        return kernel.REFUSED
    code, said = quiet(kernel.propose, box, [json.dumps(prop, ensure_ascii=False)], ts)
    if not said.startswith("pass "):
        print("refused:", said.strip(), file=sys.stderr)
        return kernel.REFUSED
    waiting.append((said.split()[1], STACK_PATH, ", ".join(run)))
    for subj, path, what in waiting:
        print(f"proposed  {subj}  {path}  {what}")
    print(
        f"{len(waiting)} waiting on your seal: python kernel.py seal --box {box} proposal:..."
    )
    return kernel.ESCALATE


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="suggest.py", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="verb", required=True)
    for verb in ("suggest", "propose"):
        s = sub.add_parser(verb)
        s.add_argument("sentence", help="what you want done, in your own words")
        s.add_argument("--box", required=True, help="your record")
        if verb == "suggest":
            s.add_argument(
                "--json", action="store_true", help="the plan as the Forge reads it"
            )
        else:
            s.add_argument(
                "--choose", action="append", metavar="WORD=NAME", help="settle a fork"
            )
            s.add_argument(
                "--why", action="append", metavar="WORD=REASON", help="your reason"
            )
    a = p.parse_args(argv)
    box = Path(a.box)
    why = is_box(box)
    if why:
        print("refused:", why, file=sys.stderr)
        return kernel.REFUSED
    got = forge()
    if got is None:
        print("refused:", NEEDS, file=sys.stderr)
        return kernel.REFUSED
    card_box, card_table, shape, rec = got
    try:
        cards = card_box.CardBox(ROOT)
    except card_table.CardTableError as e:  # a card beside this script that won't read
        print("refused:", e, file=sys.stderr)
        return kernel.REFUSED
    sealed, stacks = on_record(box, rec)
    out = plan(cards, cards.scan(a.sentence), shape, rec, sealed)
    if (k := kernel.bite_key(a.sentence)) in stacks:
        out["stack"] = stacks[k]
    if a.verb == "propose":
        if "stack" in out:
            print(f"refused: a stack is sealed for these words already (row {out['stack']['row']})", file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
        choose, bad = pairs(a.choose, "--choose")
        reasons, worse = pairs(a.why, "--why")
        if bad or worse:
            print("refused:", bad or worse, file=sys.stderr)
            return kernel.REFUSED
        return propose(box, a.sentence, out, cards.cards, choose, reasons, rec)
    if a.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        say(out)
    if "stack" in out or (out["steps"] and not out["forks"]):
        return kernel.ALIVE
    return kernel.ESCALATE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
