"""why_not.py: why a question got "not enough to say". Python 3.9+.

    python adapters/stdlib/why-not/why_not.py --box DIR "when does the frost come"

A bite that finds nothing says only that. This asks the same question of the
same folder, the kernel's own way, and says why, without asking it for real:
nothing is written, so the record does not hold one more question.

    when does the frost come in autumn
      frost   held by 1 passage: diary.txt:3
      come    no passage holds it
      autumn  no passage holds it
    A passage has to hold 2 of the 3 words at once.
    The nearest it came:
      diary.txt:3  holds 1 (frost); lacks come, autumn
    What would have answered it: a dated note, an event or a deadline, with the date on the line.

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

If your files do hold the question, it says so and where, and stops. A words
list (the box's own, if it has one) is read as the bite reads it.

Exit codes, the kernel's: 0 your files do hold it; 42 they don't, and this
says why; 2 refused (a bad command line, a words list that doesn't read).
"""

from __future__ import annotations

import difflib
import math
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


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a == "--box":
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or len(args) != 1 or args[0].startswith("--"):
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
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
    held, lines = explain(kernel.chunks(Path(cfg["pile"])), args[0], alias or {})
    print(" ".join(args[0].split()))
    print("\n".join(lines))
    return kernel.ALIVE if held else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
