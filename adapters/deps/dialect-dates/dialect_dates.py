"""dialect_dates.py: the words your folder uses far more than the world does,
each dated by its first and last appearance, with the passage that first
says it. Python 3.9+.

    python adapters/deps/dialect-dates/dialect_dates.py --box DIR [--lang CODE] [--top N]

Two add-ons, one after the other, run in this process. dialect names the
words your passages use far more than wordfreq says the world does, and the
words its counts don't have at all; first-mention reads every line that
holds each one, dated as it dates a line (the line's own date, the nearest
date above it, or its file's name). What comes out is a vocabulary with a
history, oldest first:

    2024-05-01  2026-09-16  artificial    15 mentions in 15 files
        minutes/20240501.html.txt:890  A few participants commented that higher ...

--top N is how many of dialect's words to date, 30 unless you say (each
kind, as dialect counts them). A word whose lines are all undated is listed
last, said so: your files don't say when. A word is one word: dialect counts
single words, so "artificial" stands for "artificial intelligence".

It reads and prints; it writes nothing. Exit codes, the kernel's: 0 a word
was dated; 42 no word passed dialect's bar, or none of them could be dated;
2 refused.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "dialect"))
sys.path.insert(0, str(HERE.parents[1] / "stdlib" / "first-mention"))
import dialect  # noqa: E402
import first_mention  # noqa: E402
import kernel  # noqa: E402

USAGE = (
    "usage: dialect_dates.py --box DIR [--lang CODE] [--top N]\n"
    "  the words your folder uses far more than the world does, each dated"
)
TEXT = 100  # characters of the first line shown


def dated(pile: list[dict], words: list[str], alias: dict) -> list[dict]:
    """Each word's mentions, first and last date, and the first line; words
    with no dated line last, in dialect's order."""
    rows = []
    for order, w in enumerate(words):
        found = first_mention.mentions(pile, {w}, alias)
        if not found:
            continue
        days = [r["when"] for r in found if r["when"]]
        rows.append({
            "word": w,
            "first": first_mention.day(days[0]) if days else "",
            "last": first_mention.day(days[-1]) if days else "",
            "mentions": len(found),
            "files": len({r["path"] for r in found}),
            "where": f"{found[0]['path']}:{found[0]['line']}",
            "text": found[0]["text"],
            "order": order,
        })  # fmt: skip
    return sorted(rows, key=lambda r: (r["first"] == "", r["first"], r["order"]))


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {"--lang": "en", "--top": str(dialect.TOP)}
    it = iter(argv)
    bad = False
    for a in it:
        if a in ("--box", "--lang", "--top"):
            opts[a] = next(it, "")
        else:
            bad = True
    if (
        bad
        or not opts.get("--box")
        or not opts["--top"].isdigit()
        or opts["--top"] == "0"
    ):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    try:
        import wordfreq
    except ImportError:
        print(
            f"refused: dialect-dates needs wordfreq: {dialect.INSTALL}", file=sys.stderr
        )
        return kernel.REFUSED
    lang = opts["--lang"]
    if lang not in wordfreq.available_languages():
        print(f"refused: wordfreq has no counts for {lang!r}", file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    _, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ", file=sys.stderr)
        return kernel.REFUSED
    cfg = kernel.config(box)
    alias = {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            print(f"refused: {why}", file=sys.stderr)
            return kernel.REFUSED
    pile = kernel.chunks(Path(cfg["pile"]))
    unknown, known = dialect.dialect(
        pile, lambda w: wordfreq.zipf_frequency(w, lang), int(opts["--top"])
    )
    words = [w for w, *_ in unknown] + [w for w, *_ in known]
    rows = dated(pile, words, alias)
    if not rows:
        print(
            f"No word is held by {dialect.MIN_PASSAGES} passages or more: too few files."
        )
        return kernel.ESCALATE
    print(
        f"Your words against wordfreq's {lang}, dated: {len(rows)} words, oldest first."
    )
    width = max(len(r["word"]) for r in rows)
    for r in rows:
        when = f"{r['first']}  {r['last']}" if r["first"] else "undated" + " " * 15
        print(
            f"  {when}  {r['word']:<{width}}  {r['mentions']} mentions in {r['files']} files"
        )
        print(f"      {r['where']}  {r['text'][:TEXT]}")
    undated = sum(1 for r in rows if not r["first"])
    if undated:
        print(f"{undated} undated: your files don't say when.")
    return kernel.ALIVE if any(r["first"] for r in rows) else kernel.ESCALATE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
