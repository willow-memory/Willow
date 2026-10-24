"""claim_check.py: a claim checked against your sources, part by part.

    python adapters/stdlib/claim-check/claim_check.py --box DIR "the claim" [--top N]

A claim is made of parts: "Google scans Gmail for ads" needs Google, scans,
Gmail and ads in one place before a source can be said to back it. This
lists, for a claim:

    all parts    policy.txt:12    google, scans, gmail, ads
    some parts   policy.txt:203   gmail, ads           lacks scans, google
    no file has  scans

- **all parts**: every passage holding every part, by the kernel's own
  reading (a word or its plain form, in the passage or its file's path, and
  your words list if the box has one);
- **some parts**: the passages holding the most parts short of all, up to
  `--top` (3), each with what it lacks;
- **no file has**: the parts nothing in your folder holds at all.

A passage that holds every part may still deny the claim ("we never scan
Gmail for ads" holds all four): this finds where to read, and never reads
for you. A part no file has is the strongest thing it can say: nothing in
your folder names it. The parts are the claim's words less the kernel's
common ones (the, for, is ...), so "for" is never asked for.

It only reads. Exit codes, the kernel's: 0 some passage holds every part;
42 none does; 2 refused.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

TOP = 3


def parts(claim: str) -> list[str]:
    """The claim's words in order, once each, less the common ones."""
    return [w for w in dict.fromkeys(kernel.words(claim)) if w not in kernel.FUNCTION]


def check(pile: list[dict], want: list[str], alias: dict, top: int) -> dict:
    """Which passages hold every part, which hold the most short of that, and
    which parts no passage holds."""
    full, some, seen = [], [], set()
    for c in pile:
        ts = kernel.toks(c)
        held = [w for w in want if kernel.held_by(w, ts, alias)]
        seen.update(held)
        if len(held) == len(want):
            full.append((c, held))
        elif held:
            some.append((c, held))
    some.sort(key=lambda x: (-len(x[1]), x[0]["path"], x[0]["line"]))
    return {
        "all": full,
        "some": some[:top],
        "absent": [w for w in want if w not in seen],
    }


def main(argv: list[str]) -> int:
    top = TOP
    if len(argv) == 5 and argv[3] == "--top" and argv[4].isdigit() and int(argv[4]) > 0:
        top, argv = int(argv[4]), argv[:3]
    if len(argv) != 3 or argv[0] != "--box":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(argv[1])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    want = parts(argv[2])
    if not want:
        print("refused: a claim needs a word that isn't a common one", file=sys.stderr)
        return kernel.REFUSED
    cfg, alias = kernel.config(box), {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            print(f"refused: {why}", file=sys.stderr)
            return kernel.REFUSED
    got = check(kernel.chunks(Path(cfg["pile"])), want, alias, top)
    for c, held in got["all"]:
        print(f"all parts    {c['path']}:{c['line']}   {', '.join(held)}")
    for c, held in got["some"]:
        lacks = ", ".join(w for w in want if w not in held)
        print(
            f"some parts   {c['path']}:{c['line']}   {', '.join(held)}   lacks {lacks}"
        )
    if got["absent"]:
        print(f"no file has  {', '.join(got['absent'])}")
    if not got["all"] and not got["some"]:
        print("Nothing in your folder holds any part of it.")
    return kernel.ALIVE if got["all"] else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
