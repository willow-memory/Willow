"""abbreviations.py: your shorthand read as your files write it, either way.

    python adapters/stdlib/abbreviations/abbreviations.py --box DIR "when is the appointment"
    read appointment as appt: 3 passages hold it
    ask:  when is the appt

    python adapters/stdlib/abbreviations/abbreviations.py lines --box DIR --to FILE
    wrote 4 words-list lines to FILE

To the kernel a word is its letters, so "appt" isn't "appointment". A word
of your question that no file of yours holds is looked up in a small table
of common shorthand (appt, tmrw, mtg, rx, thurs, the months), both ways
round: "appointment" finds the files' "appt", and "appt" finds their
"appointment". It's read as the form the most passages hold, a tie going to
the first in sorted order, and it never asks for you: the question as read
is printed, for you to ask.

`lines` is the lasting fix: one words-list line for each shorthand of the
table your files write only one way, written to FILE for you to read before
you keep them (willow's words list format, the word you'd type on the
left). Add the lines you agree with to your words list, and the kernel
reads each one that way every time, on its own.

The table is this file's, not yours to teach here: a shorthand of your own
goes straight in your words list. Shorthand the kernel splits at a slash
(w/c, b/c) is out of its reach, and so out of this one's. It suggests,
never decides: a line is yours to keep or drop, and "st" offered as
"street" beside a saint is exactly why you read them first.

Exit codes, the kernel's, as accents uses them: 0 every word is held, or a
reading is offered (`lines`: written, or none needed); 42 a word nothing
covers, or nothing to write; 2 refused.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: common shorthand, each a single word to the kernel, mapped to its full
#: forms; the question's word may be either side
SHORT = {
    "acct": ["account"], "amt": ["amount"], "appt": ["appointment"],
    "approx": ["approximately"], "ave": ["avenue"], "bday": ["birthday"],
    "bldg": ["building"], "blvd": ["boulevard"], "dept": ["department"],
    "dr": ["doctor", "drive"], "fri": ["friday"], "govt": ["government"],
    "hrs": ["hours"], "info": ["information"], "mins": ["minutes"],
    "msg": ["message"], "mtg": ["meeting"], "mth": ["month"],
    "qty": ["quantity"], "rd": ["road"], "rx": ["prescription"],
    "st": ["street", "saint"], "tel": ["telephone"], "thru": ["through"],
    "thurs": ["thursday"], "tmrw": ["tomorrow"], "tues": ["tuesday"],
    "uni": ["university"], "vs": ["versus"], "weds": ["wednesday"],
    "wk": ["week"], "xmas": ["christmas"], "yr": ["year"],
    "jan": ["january"], "feb": ["february"], "mar": ["march"],
    "apr": ["april"], "jun": ["june"], "jul": ["july"], "aug": ["august"],
    "sep": ["september"], "sept": ["september"], "oct": ["october"],
    "nov": ["november"], "dec": ["december"],
}  # fmt: skip
#: the other way round: a full form back to its shorthands
LONG: dict[str, list[str]] = {}
for _s, _fulls in SHORT.items():
    for _f in _fulls:
        LONG.setdefault(_f, []).append(_s)


def other_forms(w: str) -> list[str]:
    """The word's other forms the table knows: its expansions when it is a
    shorthand, its shorthands when it is a full form."""
    return sorted(set(SHORT.get(w, [])) | set(LONG.get(w, [])))


def held_counts(pile: list[dict], xs: list[str]) -> dict[str, int]:
    """{form: passages holding it (the kernel's `holds`, plain forms too)}."""
    out = dict.fromkeys(xs, 0)
    for c in pile:
        toks = kernel.toks(c)
        for x in xs:
            out[x] += kernel.holds(x, toks)
    return {x: n for x, n in out.items() if n}


def readings(question: str, pile: list[dict], alias: dict) -> tuple[dict, list]:
    """({word: (as the files write it, passages)}, [words nothing covers]),
    for the question's words no file holds."""
    every: set[str] = set()
    for c in pile:
        every |= kernel.toks(c)
    read, missing = {}, []
    for w in dict.fromkeys(kernel.words(question)):
        if w in kernel.FUNCTION or kernel.held_by(w, every, alias):
            continue
        found = held_counts(pile, other_forms(w))
        if found:
            best = min((-n, x) for x, n in found.items())
            read[w] = (best[1], -best[0])
        else:
            missing.append(w)
    return read, missing


def words_lines(pile: list[dict]) -> list[str]:
    """One words-list line per shorthand of the table whose two forms the
    files write only one way: the form you'd type on the left, the files' on
    the right, sorted. Files holding both ways need no line."""
    out = []
    for short, fulls in sorted(SHORT.items()):
        held = held_counts(pile, [short, *fulls])
        if short in held:
            absent = sorted(f for f in fulls if f not in held)
            for f in absent:
                out.append(f"{f} = {short}")
        else:
            present = sorted(f for f in fulls if f in held)
            if present:
                out.append(f"{short} = {', '.join(present)}")
    return out


def main(argv: list[str]) -> int:
    verb = "lines" if argv[:1] == ["lines"] else "read"
    rest = argv[1:] if verb == "lines" else argv
    opts: dict[str, str] = {}
    args: list[str] = []
    it = iter(rest)
    for a in it:
        if a in ("--box", "--to"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if (
        not opts.get("--box")
        or len(args) != (verb == "read")
        or any(a.startswith("-") for a in args)
        or (verb == "lines") != bool(opts.get("--to"))
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    cfg = kernel.config(box)
    pile = kernel.chunks(Path(cfg["pile"]))
    if verb == "lines":
        to = Path(opts["--to"])
        for name, root in (("your folder", Path(cfg["pile"])), ("the box", box)):
            if to.resolve().is_relative_to(root.resolve()):
                print(f"refused: FILE is inside {name}", file=sys.stderr)
                return kernel.REFUSED
        lines = words_lines(pile)
        if not lines:
            print("No shorthand of the table is in your files; nothing written.")
            return kernel.ESCALATE
        try:
            fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except OSError as e:
            print(f"refused: could not write {to}: {type(e).__name__}", file=sys.stderr)
            return kernel.REFUSED
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        print(f"wrote {len(lines)} words-list line{'s' if len(lines) != 1 else ''}"
              f" to {opts['--to']}")  # fmt: skip
        return kernel.ALIVE
    if not kernel.words(args[0]):
        print("refused: a question with no words", file=sys.stderr)
        return kernel.REFUSED
    alias: dict = {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            print(f"refused: {why}", file=sys.stderr)
            return kernel.REFUSED
    read, missing = readings(args[0], pile, alias)
    for w, (x, n) in read.items():
        print(f"read {w} as {x}: {n} passage{'s' * (n != 1)} hold{'s' * (n == 1)} it")
    for w in missing:
        print(f"no file has {w}, written out or short")
    if read:
        asked = " ".join(read.get(w, (w,))[0] for w in kernel.words(args[0]))
        print(f"ask:  {asked}")
    elif not missing:
        print("Your files hold every word of it; nothing to read differently.")
    return kernel.ESCALATE if missing and not read else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
