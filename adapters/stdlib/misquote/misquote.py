"""misquote.py: a quote that is almost in your files, and how it differs.

    python adapters/stdlib/misquote/misquote.py --box DIR "the quote"

quote-check says whether a quote is in your files. When it isn't, the
question is usually whether it is nearly there: a word dropped, a word
changed, two sentences run together. This finds the passage that holds the
most of the quote's words in the quote's order, and says what differs:

    closest      policy.txt:203   (24 of 25 words, in order)
      dropped    Google           your files have it here; the quote doesn't
      added      now              the quote has it; your files don't

or `as written   policy.txt:203` when the quote's words are there in order,
which is quote-check's "verbatim" or "same words". A passage is the closest
only when it holds at least half the quote's words in order; else nothing is
close, and it says so. Words are split the kernel's way (its `WORD`, case
aside), and each is shown as the file spells it.

It only reads. Exit codes, the kernel's: 0 the quote is in your files as
written; 42 it isn't (the closest passage, or nothing close); 2 refused.
"""

from __future__ import annotations

import json
import difflib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

CLOSE = 0.5  # the share of the quote's words, in order, that makes a passage close


NAME = "misquote"


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


def tokens(text: str) -> list[str]:
    """The words as the text spells them, the kernel's way."""
    return kernel.WORD.findall(text)


def closest(pile: list[dict], quote: str) -> tuple[dict, int, list] | None:
    """The passage holding most of the quote's words in order, how many, and
    what differs as (kind, words): dropped from the quote, added by it, or
    changed from one to the other. Ties go to the shorter stretch, then to
    the file and line first."""
    want = [w.lower() for w in tokens(quote)]
    best = None
    for c in pile:
        have = tokens(c["text"])
        sm = difflib.SequenceMatcher(
            None, want, [w.lower() for w in have], autojunk=False
        )
        blocks = [b for b in sm.get_matching_blocks() if b.size]
        kept = sum(b.size for b in blocks)
        if not blocks or kept < CLOSE * len(want):
            continue
        lo, hi = blocks[0].b, blocks[-1].b + blocks[-1].size
        rank = (-kept, hi - lo, c["path"], c["line"])
        if best is None or rank < best[0]:
            best = (rank, c, kept, have[lo:hi])
    if best is None:
        return None
    _, c, kept, span = best
    sm = difflib.SequenceMatcher(None, want, [w.lower() for w in span], autojunk=False)
    quoted = tokens(quote)
    out = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "delete":
            out.append(("added", quoted[i1:i2], []))
        elif op == "insert":
            out.append(("dropped", span[j1:j2], []))
        elif op == "replace":
            out.append(("changed", quoted[i1:i2], span[j1:j2]))
    return c, kept, out


def main(argv: list[str]) -> int:
    as_json = "--json" in argv  # noqa: F841  wire: say(report(...), as_json)
    argv = [a for a in argv if a != "--json"]
    if len(argv) != 3 or argv[0] != "--box":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(argv[1])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    quote = argv[2]
    if not tokens(quote):
        print("refused: a quote with no words", file=sys.stderr)
        return kernel.REFUSED
    got = closest(kernel.chunks(Path(kernel.config(box)["pile"])), quote)
    if got is None:
        print("Nothing in your folder holds even half of it, in that order.")
        return kernel.ESCALATE
    c, kept, diffs = got
    where = f"{c['path']}:{c['line']}"
    if not diffs:
        print(f"as written   {where}")
        return kernel.ALIVE
    print(f"closest      {where}   ({kept} of {len(tokens(quote))} words, in order)")
    for kind, ws, instead in diffs:
        if kind == "dropped":
            print(
                f"  dropped    {' '.join(ws):<16} your files have it here; the quote doesn't"
            )
        elif kind == "added":
            print(f"  added      {' '.join(ws):<16} the quote has it; your files don't")
        else:
            print(
                f"  changed    {' '.join(ws)} -> {' '.join(instead)}   the quote's words, then your files'"
            )
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
