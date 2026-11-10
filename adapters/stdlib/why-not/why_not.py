"""why_not.py: why a question got "not enough to say". Python 3.9+.

    python adapters/stdlib/why-not/why_not.py --box DIR "when does the frost come" [--json]
    python adapters/stdlib/why-not/why_not.py --box DIR --questions FILE [--of SCANNED] [--json]

A bite that finds nothing says only that. This asks the same question of the
same folder, the kernel's own way, and says why, without asking it for real:
nothing is written, so the record does not hold one more question.

    why-not: populated, "when does the frost come in autumn": a passage has to hold 2 of the 3 words at once
    ## words
      frost         held by 1 passage: diary.txt:3
      come          no passage holds it
      autumn        no passage holds it
    ## the nearest it came
      diary.txt:3   holds 1 (frost); lacks come, autumn
    ## what would have answered it
      kind of file  a dated note, an event or a deadline, with the date on the line

It lists, for each word that counts (the kernel leaves "when", "does" and the
like out), how many passages hold it and the first few, or that none does.
Then the nearest it came: the passages holding the most of the words, which
they held and which they lacked, against the share the kernel asks for
(`kernel.HOLD`, half). For a word nothing holds, a close spelling in your files, if there is
one, comes with the line a words list would take to teach it:

    frost        no passage holds it   (your files say "frosts": frost = frosts)

And last, by the question's first word, what kind of file would have
answered: for "when", a dated note or a deadline; for "how much", a line with
the number and what it counts; for "who", a line naming the person.

If your files do hold the question, it says so and where in the first line
(an empty report: nothing to explain), and stops. A words
list (the box's own, if it has one) is read as the bite reads it.

--questions FILE asks every question of a file (one a line, or
`name<TAB>question`, as scan takes them) and explains each that found
nothing, a group a question. --of SCANNED hands it what scan already found:
the lines scan printed for that file, so only the questions scan said were
empty are explained and none is asked twice. In a stack that is an earlier
step's output, named by its number: `--of {01}`.

It prints a report (ci/README.md, "The report contract"); `--json` gives the
same as one object. States and exit codes: empty, 0, your files do hold the
question, so there is nothing to explain; populated, 42, they don't, and the
rows say why (that waits on you); unreachable, 42, every word is a common
one, so it couldn't look; 2 refused (a bad command line, a words list that
doesn't read).
"""

from __future__ import annotations

import difflib
import json
import math
import re
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

SHOWN = 3  # places listed for a word, and passages for the nearest misses
KIND = (  # (the question's opening words, what would have answered)
    (("how much", "how many", "how long", "how far", "how old"), "a line with the number and what it counts"),
    (("when", "what time", "what date", "what day"), "a dated note, an event or a deadline, with the date on the line"),
    (("who", "whom", "whose"), "a line naming the person and what they did"),
    (("where",), "a line naming the place"),
    (("why",), "a note that gives the reason, in a line like \"because...\""),
    (("how",), "a note of the steps, in order"),
    (("what", "which"), "a note that states it plainly"),
)  # fmt: skip


NAME = "why-not"


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


def kind_of(question: str) -> str | None:
    head = " ".join(kernel.words(question)[:2])
    first = head.split(" ")[0] if head else ""
    for openers, kind in KIND:
        if any(head == o or head.startswith(o + " ") or first == o for o in openers):
            return kind
    return None


def want_of(question: str) -> list[str]:
    """The words that count, once each, in the order asked."""
    seen, out = set(), []
    for w in kernel.words(question):
        if w not in kernel.FUNCTION and w not in seen:
            seen.add(w)
            out.append(w)
    return out


def places(held: list[dict]) -> str:
    shown = ", ".join(f"{c['path']}:{c['line']}" for c in held[:SHOWN])
    return shown + (f" and {len(held) - SHOWN} more" if len(held) > SHOWN else "")


def explain(pile: list[dict], question: str, alias: dict) -> tuple[bool, list[str]]:
    """(your files hold it, the lines that say why they don't)."""
    want = want_of(question)
    if not want:
        return False, ["Every word is a common one; name the thing you mean."]
    served = kernel.rank(pile, question, alias)
    if served:
        return True, [f"Your files do hold it: {places(served)}."]
    toks = [kernel.toks(c) for c in pile]
    held = {
        w: [c for c, t in zip(pile, toks) if kernel.held_by(w, t, alias)] for w in want
    }
    vocab = sorted({t for ts in toks for t in ts if t.isalpha() and len(t) > 3})
    width = max(len(w) for w in want)
    lines = []
    for w in want:
        if held[w]:
            lines.append(
                f"  {w:<{width}}  held by {len(held[w])} passage{'s' if len(held[w]) != 1 else ''}: {places(held[w])}"
            )
            continue
        near = [
            v for v in difflib.get_close_matches(w, vocab, n=2, cutoff=0.8) if v != w
        ]
        hint = (
            f"   (your files say {' or '.join(repr(v) for v in near)}: {w} = {', '.join(near)})"
            if near
            else ""
        )
        lines.append(f"  {w:<{width}}  no passage holds it{hint}")
    need = math.ceil(kernel.HOLD * len(want))  # the kernel's share, rounded up
    lines.append(
        f"A passage has to hold {need} of the {len(want)} word{'s' if len(want) != 1 else ''} at once."
    )
    scored = sorted(
        ((sum(1 for w in want if c in held[w]), c) for c in pile),
        key=lambda s: (-s[0], s[1]["path"], s[1]["line"]),
    )
    best = [(n, c) for n, c in scored if n][:SHOWN]
    if best:
        lines.append("The nearest it came:")
        for n, c in best:
            has = [w for w in want if c in held[w]]
            lacks = [w for w in want if c not in held[w]]
            lines.append(
                f"  {c['path']}:{c['line']}  holds {n} ({', '.join(has)}); lacks {', '.join(lacks)}"
            )
    else:
        lines.append("No passage holds any of them.")
    if kind := kind_of(question):
        lines.append(f"What would have answered it: {kind}.")
    return False, lines


def one(pile: list[dict], question: str, alias: dict) -> tuple[str, str, list]:
    """(the state, the line said, the groups) for one question: empty when
    your files hold it, unreachable when every word is a common one."""
    held, lines = explain(pile, question, alias)
    asked = " ".join(question.split())
    if held or not want_of(question):
        said = f'"{asked}": {lines[0][0].lower()}{lines[0][1:].rstrip(".")}'
        return ("empty" if held else "unreachable"), said, []
    # the lines explain gave, sorted into the report's groups
    said, words, nearest, kind = f'"{asked}": ', [], [], []
    in_nearest = False
    for ln in lines:
        if ln.startswith("A passage has to hold"):
            said += ln.rstrip(".").replace("A passage", "a passage", 1)
        elif ln == "The nearest it came:":
            in_nearest = True
        elif ln == "No passage holds any of them.":
            said += "; no passage holds any of them"
        elif ln.startswith("What would have answered it: "):
            kind.append(("kind of file", ln.split(": ", 1)[1].rstrip(".")))
        else:
            where, what = re.split(r"\s{2,}", ln.strip(), maxsplit=1)
            (nearest if in_nearest else words).append((where, what))
    groups = [("words", words), ("the nearest it came", nearest),
              ("what would have answered it", kind)]  # fmt: skip
    return "populated", said, groups


def questions(text: str) -> list[tuple[str, str]]:
    """(name, question) for each line of a questions file, as scan reads
    one: `name<TAB>question`, or a bare question named by its line."""
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        name, tab, q = line.partition("\t")
        out.append((name.strip(), q.strip()) if tab else (str(n), line.strip()))
    return out


def empties(text: str) -> tuple[set[str] | None, str]:
    """(the names of the questions scan said were empty, "") from the lines
    scan printed, or (None, why they aren't scan's)."""
    out: set[str] = set()
    rows = [ln for ln in text.splitlines() if ln.strip()]
    if not rows:
        return None, "it is empty: the step before said nothing to hand on"
    for n, ln in enumerate(rows, 1):
        try:
            row = json.loads(ln)
            name, state = row["question"], row["state"]
        except (ValueError, KeyError, TypeError):
            return None, f"line {n} has no question and state, as scan's lines do"
        if state == "empty":
            out.add(str(name))
    return out, ""


def several(pile: list[dict], asked: list[tuple[str, str]], alias: dict, as_json: bool) -> int:  # fmt: skip
    """Every question that found nothing explained, a group a question."""
    groups, short = [], 0
    for name, q in asked:
        state, said, parts = one(pile, q, alias)
        if state == "empty":
            continue
        short += 1
        rows = [("it needs", said.split('": ', 1)[-1])]
        rows += [r for g, rs in parts if g != "what would have answered it" for r in rs]
        groups.append((f"{name}: {' '.join(q.split())}", rows))
    n = len(asked)
    if not short:
        said = f"your files hold all {n} question{'s' * (n != 1)}; nothing to explain"
        say(report(NAME, "empty", said, []), as_json)
        return kernel.ALIVE
    said = f"{short} of {n} question{'s' * (n != 1)} found nothing; each says why"
    say(report(NAME, "populated", said, groups), as_json)
    return kernel.ESCALATE


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--questions", "--of"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if (
        not opts.get("--box")
        or bool(opts.get("--questions")) == bool(args)
        or len(args) > 1
        or any(a.startswith("--") for a in args)
        or ("--of" in opts and not (opts["--of"] and opts.get("--questions")))
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    many = None
    if "--questions" in opts:
        try:
            many = questions(Path(opts["--questions"]).read_text(encoding="utf-8"))
            scanned = (
                Path(opts["--of"]).read_text(encoding="utf-8")
                if "--of" in opts
                else None
            )
        except (OSError, ValueError) as e:
            print(
                f"refused: a file could not be read: {type(e).__name__}",
                file=sys.stderr,
            )
            return kernel.REFUSED
        if not many:
            print(f"refused: {opts['--questions']} holds no question", file=sys.stderr)
            return kernel.REFUSED
        if scanned is not None:
            names, why = empties(scanned)
            if names is None:
                print(f"refused: {opts['--of']} can't be taken: {why}", file=sys.stderr)
                return kernel.REFUSED
            many = [(n, q) for n, q in many if n in names]
            if not many:
                said = "the scan handed on no empty question; nothing to explain"
                say(report(NAME, "empty", said, []), as_json)
                return kernel.ALIVE
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    cfg = kernel.config(box)
    alias: dict = {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            print(f"refused: {why}", file=sys.stderr)
            return kernel.REFUSED
    pile = kernel.chunks(Path(cfg["pile"]))
    if many is not None:
        return several(pile, many, alias or {}, as_json)
    state, said, groups = one(pile, args[0], alias or {})
    say(report(NAME, state, said, groups), as_json)
    return kernel.ALIVE if state == "empty" else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
