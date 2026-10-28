"""pile_gold.py: each answer you approve marks the passages that held it, so
your own questions become a test of how well the search finds things, scored
as recall at five. Python 3.9+.

    python adapters/stdlib/pile-gold/pile_gold.py --box DIR --questions FILE
        [--store STORE] [--now TS]

When you seal a proposal, the kernel's record ties it to the question it
answered (by that question's key, never its words) and the proposal names
the passages it cites. Those passages are your gold: for that question,
they held the answer.

The record keeps no words, so the questions come from FILE: one a line,
optionally `name<TAB>question`, blank and `#` lines skipped, as scan reads
them. Each is matched to your seals by `kernel.bite_key`, so a question
retyped in another case or punctuation still finds its seal. Each matched
question is asked of the box's folder by two ranks, the kernel's own and
pile-rank's, and each counts how many of its gold passages are in its top
five. Over all of them:

    kernel     found 7 of 9 approved passages in the top 5
    pile-rank  found 8 of 9 approved passages in the top 5

A cited passage no longer in the folder (its words changed or went) is
counted as gone, not as a miss. Seals are read through the kernel, which
checks each against your key; this never reads the key, and never writes a
seal. It appends one row to the record, kind "gold", with the counts, the
SHA-256 of FILE and nothing else: no question, no passage, no word.

Passages come from a pile-store store while it matches the folder, else the
folder. Exit codes, the kernel's: 0 scored and recorded; 42 no question in
FILE has an approved answer, so nothing is recorded; 2 refused (a bad
command line, a broken record, or a FILE that can't be read).
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "pile-rank"))
sys.path.insert(0, str(HERE.parent / "scan"))
import kernel  # noqa: E402
import pile_rank  # noqa: E402
import scan  # noqa: E402

AT = 5  # recall at five


def gold(box: Path, rows: list[dict]) -> dict[str, set[str]]:
    """{a question's key: the passage ids its sealed answers cite}, from the
    seals whose proof holds and whose proposal still stands."""
    out: dict[str, set[str]] = {}
    for subj, row in kernel.sealed(box, rows).items():  # the kernel checks the key
        prop, asked, why = kernel.standing(box, rows, subj, row)
        cites = prop.get("cites") if why is None else None
        if isinstance(cites, list) and cites:
            out.setdefault(asked, set()).update(c for c in cites if isinstance(c, str))
    return out


def score(
    pile: list[dict], asked: list[tuple[str, str, set[str]]], alias: dict, dated
) -> dict:
    """Each rank's found and of, the gone, and each question's line."""
    here = {c["id"] for c in pile}
    ranker = pile_rank.Ranker(pile)
    found = {"kernel": 0, "pile-rank": 0}
    of = gone = 0
    lines = []
    for name, q, ids in asked:
        live = ids & here
        gone += len(ids - here)
        of += len(live)
        by = {
            "kernel": kernel.rank(pile, q, alias, top=AT, dated=dated),
            "pile-rank": [c for c, *_ in ranker.rank(q, AT)],
        }
        got = {k: len(live & {c["id"] for c in v}) for k, v in by.items()}
        for k in found:
            found[k] += got[k]
        lines.append(
            f"{name}: kernel {got['kernel']}, pile-rank {got['pile-rank']} "
            f"of {len(live)}" + (f" ({len(ids - here)} gone)" if ids - here else "")
        )
    return {"found": found, "of": of, "gone": gone, "lines": lines}


def usage() -> int:
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    it = iter(argv)
    for a in it:
        if a in ("--box", "--questions", "--store", "--now"):
            opts[a] = next(it, "")
        else:
            return usage()
    if not opts.get("--box") or not opts.get("--questions"):
        return usage()
    if any(k in opts and not opts[k] for k in ("--store", "--now")):
        return usage()
    box = Path(opts["--box"])
    if not (box / "record.jsonl").is_file():
        print(f"refused: {opts['--box']} is not a box", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ", file=sys.stderr)
        return kernel.REFUSED
    try:
        raw = Path(opts["--questions"]).read_bytes()
        qs = scan.questions(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError) as e:
        print(f"refused: the questions can't be read: {type(e).__name__}",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    cfg = kernel.config(box)
    alias = {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            print(f"refused: {why}", file=sys.stderr)
            return kernel.REFUSED
    marked = gold(box, rows)
    asked = [
        (name, q, marked[k]) for name, q in qs if (k := kernel.bite_key(q)) in marked
    ]
    if not asked:
        print(f"nothing to score: none of {len(qs)} questions has an answer you "
              "sealed; nothing recorded")  # fmt: skip
        return kernel.ESCALATE
    store = Path(opts["--store"]) if "--store" in opts else None
    pile, where = pile_rank.passages(Path(cfg["pile"]), store)
    dated = (lambda p: [c["date"] for c in p]) if where == "store" else None
    got = score(pile, asked, alias, dated)
    for line in got["lines"]:
        print(line)
    for k, n in got["found"].items():
        print(f"{k:<10} found {n} of {got['of']} approved passages in the top {AT}")
    if got["gone"]:
        print(f"{got['gone']} approved passage{'' if got['gone'] == 1 else 's'} "
              "no longer in the folder, not counted")  # fmt: skip
    row = kernel.append(
        box, opts.get("--now") or kernel.now(), "gold", who="pile-gold",
        questions_sha256=hashlib.sha256(raw).hexdigest(), asked=len(qs),
        scored=len(asked), at=AT, of=got["of"], gone=got["gone"],
        found={k.replace("-", "_"): n for k, n in got["found"].items()},
        read_from=where,
    )  # fmt: skip
    print(f"recorded at row {row['n']}")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
