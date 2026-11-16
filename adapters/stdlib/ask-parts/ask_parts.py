"""ask_parts.py: a question that asks two things in one breath, split into parts, each asked by the kernel's own rule. Python 3.9+.

    python adapters/stdlib/ask-parts/ask_parts.py [--box DIR] "your question"

"what did colleen say about mam's headstone, how much was my half" asks two
things. The kernel serves a passage only when it holds half the question's
content words, so the email that says "Your half is 725" holds one of five
and is never served. Asked as its own question, "how much was my half"
finds it.

`parts(question)` says where the question breaks. It splits only at a
comma, a semicolon, "and" or "also", and only where each side is itself a
question: it opens with a question word (what, how, did, is, ...) and holds
a content word (the kernel's `words` minus `FUNCTION`). So "salt and
pepper", "scone recipe" and "tom and jerry's address" stay whole, and so
does anything inside quotation marks. A side that isn't a question of its
own is not cut off: it stays in the part before it.

Without `--box` it prints the parts. With one it asks each part of the
box's pile by the kernel's own `rank`, the same rule, order and words list
as a bite, and prints each part's passages:

    {"state": "populated", "parts": [{"part": ..., "bite_key": ...,
        "state": "populated", "served": [{"where": ..., "echo": ..., "text": ...}]}]}

It only reads: it writes no row to the record, so what it serves is not
something an approval can cite. To cite a part's passages, a caller bites
that part through the kernel (`kernel.py bite --box DIR "<part>"`, the
text printed here), then proposes: a proposal reaches only what the box's
last bite served, so the part to cite is the last one bitten.

Exit codes, the kernel's: 0 every part is held by something; 42 a part
nothing holds (or no parts, a question of function words), left to the
person; 2 refused.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = 'usage: ask_parts.py [--box DIR] "your question"'

#: a part opens with one of these: the words a question begins with
QUESTION = frozenset(
    "what which who whom whose when where why how did does do is are was were"
    " can could would should will shall may might has have had".split()
)
#: where a part ends: a comma or semicolon, or "and" / "also" between spaces;
#: ", and how" is one break, not two
BREAK = re.compile(r"(?:\s*[,;]\s*|\s+)(?:(?:and|also)\s+)+|\s*[,;]\s*", re.IGNORECASE)
QUOTES = {'"': '"', "“": "”"}  # an opening mark and what closes it


def content(text: str) -> list[str]:
    """The words of `text` that count toward holding it: the kernel's own."""
    return [w for w in kernel.words(text) if w not in kernel.FUNCTION]


def quoted(text: str) -> str | None:
    """`text` with every quoted span blanked out to NULs, the same length, so
    an offset in it is an offset in `text`; None when a quote is left open."""
    out, close = [], None
    for ch in text:
        if close is None:
            if ch in QUOTES:
                close = QUOTES[ch]
                out.append("\0")
            else:
                out.append(ch)
        else:
            if ch == close:
                close = None
            out.append("\0")
    return None if close is not None else "".join(out)


def asks(side: str) -> bool:
    """Whether a side is a question of its own: it opens with a question word
    and holds a word that counts."""
    ws = kernel.words(side)
    return bool(ws) and ws[0] in QUESTION and bool(content(side))


def parts(question: str) -> list[str]:
    """The question's parts, in order: the question itself, as it was typed,
    when it is one."""
    masked = quoted(question)
    if masked is None:  # an open quotation: not ours to cut
        return [question]
    out: list[str] = []
    cur = 0  # where the part now being built begins
    for m in BREAK.finditer(masked):
        left = question[cur : m.start()]
        # the part so far must ask on its own, and so must what follows it up
        # to the next break that also qualifies; a side that doesn't is kept
        nxt = BREAK.search(masked, m.end())
        side = question[m.end() : nxt.start() if nxt else len(question)]
        if asks(left) and asks(side):
            out.append(left.strip())
            cur = m.end()
    out.append(question[cur:].strip())
    return [p for p in out if p] if len(out) > 1 else [question]


def ranked(box: Path, part: str) -> list[dict]:
    """What the kernel's rank serves for `part`: its words list, its order."""
    cfg = kernel.config(box)
    alias = {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            raise ValueError(why)
    return kernel.rank(kernel.chunks(Path(cfg["pile"])), part, alias)


def ask(box: Path, question: str) -> dict:
    """Each part asked of the box, with the kernel's own bite key beside it."""
    asked = []
    for part in parts(question):
        served = [
            {
                "id": c["id"],
                "where": f"{c['path']}:{c['line']}",
                "echo": kernel.echo(part, c["text"]),
                "text": c["text"],
            }
            for c in ranked(box, part)
        ]
        answers = [s for s in served if not s["echo"]]
        state = "populated" if answers else "echo" if served else "empty"
        asked.append(
            {
                "part": part,
                "bite_key": kernel.bite_key(part),
                "state": state,
                "served": served,
            }
        )
    state = "populated" if all(p["state"] == "populated" for p in asked) else "partial"
    if not any(p["state"] == "populated" for p in asked):
        state = "empty"
    return {"state": state, "parts": asked}


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a == "--box":
            opts[a] = next(it, "")
        else:
            args.append(a)
    if len(args) != 1 or ("--box" in opts and not opts["--box"]):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    question = args[0]
    if not kernel.words(question):
        print("refused: a question with no words", file=sys.stderr)
        return kernel.REFUSED
    if "--box" not in opts:
        found = parts(question)
        print(json.dumps({"parts": found}, ensure_ascii=False))
        return kernel.ALIVE if any(content(p) for p in found) else kernel.ESCALATE
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ", file=sys.stderr)
        return kernel.REFUSED
    try:
        doc = ask(box, question)
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    print(json.dumps(doc, ensure_ascii=False))
    return kernel.ALIVE if doc["state"] == "populated" else kernel.ESCALATE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
