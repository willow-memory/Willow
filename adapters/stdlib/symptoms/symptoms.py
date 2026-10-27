"""symptoms.py: one symptom's diary from your files, ready to show a doctor.

    python adapters/stdlib/symptoms/symptoms.py --box DIR "knee"

Every line of your folder that names the symptom, oldest first, each dated,
its turn marked where the line says one, and cited, so a doctor can see the
course of it and check any line against your files:

    2026-03-01  worse    Knee bad on the stairs. Voltaren and a hot pack.  Daily/2026-03-01.md:4
    2026-03-04  better   Walked the lake loop, 6.2km, knee held up.        Daily/2026-03-04.md:2
    2026-03-09  5/10     Physio: knee pain 5/10 after the stairs test.     Health/physio.md:7
    41 lines name "knee", 2024-04-30 to 2026-10-24: 9 worse, 14 better, 3 scored

You name the symptom with words, as a question is asked: "knee", "lower
back", "migraine". A line counts when it itself holds every one of your
content words, each read the kernel's way (your words list, and a word's
plain form). The line has to say it: a folder named knee/ holds the word for
asking, but writes no diary line.

**A turn is marked only where the line says one.** Worse is worse,
worsening, bad, badly, flare, flared, flaring, swollen, agony or worst;
better is better, easing, eased, improved, improving, settled, fine, or
held up. A line saying both is marked mixed, and a score the line gives as
N/10 is shown as written. Nothing is averaged, trended or diagnosed: the
course of it is yours and your doctor's to read.

A line's date is the latest it says, read as the kernel reads one (its
`newest`), else the nearest date written above it in its file, else the date
its file is named for, and the diary says which; undated lines come last.
The whole story of a matter, passages and all, written to a file to hand
over, is the timeline add-on's job; this is the quick dated diary of one
symptom's own lines.

It only reads. Exit codes, the kernel's: 0 the symptom is named somewhere;
42 never, or only common words; 2 refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

WORSE = re.compile(
    r"\b(?:worse|worsening|bad|badly|flares?|flared|flaring|swollen|agony|worst)\b",
    re.IGNORECASE,
)
BETTER = re.compile(
    r"\b(?:better|easing|eased|improved|improving|settled|fine|held up)\b",
    re.IGNORECASE,
)
SCORE = re.compile(r"\b(\d{1,2})\s*/\s*10\b")


def turn_of(line: str) -> str:
    """The turn the line says: worse, better, mixed when it says both, a
    score it gives as N/10, or nothing."""
    worse, better = bool(WORSE.search(line)), bool(BETTER.search(line))
    score = SCORE.search(line)
    if worse and better:
        return "mixed"
    if worse:
        return "worse"
    if better:
        return "better"
    return f"{score.group(1)}/10" if score else ""


def file_lines(pile: list[dict]) -> dict[str, list[tuple[int, str]]]:
    """Each file's lines with their numbers, put back together from its
    passages (the kernel cuts a long run of lines into passages of 500)."""
    out: dict[str, list[tuple[int, str]]] = {}
    for c in pile:
        rows = out.setdefault(c["path"], [])
        rows += [(c["line"] + i, ln) for i, ln in enumerate(c["text"].splitlines())]
    return out


def diary(pile: list[dict], want: set[str], alias: dict) -> list[dict]:
    """A row per line that itself holds every word of `want` (the kernel's
    `held_by`: the words list, and a word's plain form), dated by the line,
    the nearest date above it in its file, or its file's name, each saying
    so; dated rows oldest first, undated after, by file and line."""
    out = []
    for path, rows in file_lines(pile).items():
        above, filed = None, kernel.newest(path)
        for n, line in rows:
            said = kernel.newest(line)
            toks = kernel.forms(kernel.words(line))
            if all(kernel.held_by(w, toks, alias) for w in want):
                if said:
                    when, note = said, ""
                elif above:
                    when, note = above[0], f"date from line {above[1]}"
                elif filed:
                    when, note = filed, "date from file name"
                else:
                    when, note = "", ""
                out.append({"when": when, "note": note, "turn": turn_of(line),
                            "path": path, "line": n, "text": line.strip()})  # fmt: skip
            if said:
                above = (said, n)
    return sorted(out, key=lambda r: (r["when"] == "", r["when"], r["path"], r["line"]))


def day(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}" if d else "undated"


def show(asked: str, rows: list[dict]) -> list[str]:
    wt = max(len(r["turn"]) for r in rows)
    wp = max(len(f"{r['path']}:{r['line']}") for r in rows)
    out = []
    for r in rows:
        where = f"{r['path']}:{r['line']}"
        tail = f"  ({r['note']})" if r["note"] else ""
        out.append(f"{day(r['when']):<10}  {r['turn']:<{wt}}  {r['text'][:90]:<90}"
                   f"  {where:<{wp}}{tail}")  # fmt: skip
    dated = [r["when"] for r in rows if r["when"]]
    span = f", {day(dated[0])} to {day(dated[-1])}" if dated else ""
    worse = sum(r["turn"] == "worse" for r in rows)
    better = sum(r["turn"] == "better" for r in rows)
    scored = sum(r["turn"].endswith("/10") for r in rows)
    one = len(rows) == 1
    out.append(f'{len(rows)} line{"" if one else "s"} name{"s" if one else ""}'
               f' "{asked}"{span}: {worse} worse, {better} better, {scored} scored')  # fmt: skip
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a == "--box":
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or len(args) != 1 or args[0].startswith("-"):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
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
    want = set(kernel.words(args[0])) - kernel.FUNCTION
    if not want:
        print(f'"{args[0]}" is only common words, held by everything; say more.')
        return kernel.ESCALATE
    rows = diary(kernel.chunks(Path(cfg["pile"])), want, alias)
    if not rows:
        print(f'No line of your folder names "{args[0]}".')
        return kernel.ESCALATE
    for line in show(args[0], rows):
        print(line)
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
