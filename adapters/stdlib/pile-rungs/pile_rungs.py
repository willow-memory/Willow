"""pile_rungs.py: each lookup says which rung answered, words, phrases or an
embedder, and why a higher one was skipped, as data beside the passages.
Python 3.9+.

    python adapters/stdlib/pile-rungs/pile_rungs.py --from FOLDER [--store STORE]
        [--top N] QUESTION...

A question climbs the rungs from the strictest up, and the first that answers
serves:

1. **words**: the kernel's own `rank`, which serves a passage only when it
   holds half the question's words. Its answer is the kernel's.
2. **phrases**: pile-rank's BM25F, serving only the passages that hold one of
   the folder's phrases the question uses ("sourdough bread"). A question
   using none of them skips this rung, and says so.
3. **embedder**: none here. The standard library has none, and latent needs
   numpy; this rung is always skipped, and says why.

Every rung climbed is in the answer, with its state (answered, empty or
skipped) and why, so a reader (a hook, pile-gold, a person) sees how far
the question went and why it stopped:

    {"question": "...", "state": "populated", "rung": "phrases",
     "read_from": "store", "rungs": [{"rung": "words", "state": "empty",
     "why": "..."}, {"rung": "phrases", "state": "answered", ...},
     {"rung": "embedder", "state": "skipped", "why": "..."}], "served": [...]}

Only the words rung's answer is the kernel's; a phrase answer points at where
to look. Passages come from a pile-store store while it matches the folder,
else from the folder. It writes nothing. Exit codes, the kernel's: 0 a rung
answered; 42 none did, or the folder has nothing to read; 2 refused.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "pile-rank"))
import kernel  # noqa: E402
import pile_rank  # noqa: E402

NO_EMBEDDER = "no embedder here: the standard library has none, and latent needs numpy"


def words_rung(pile: list[dict], question: str, top: int, dated) -> tuple[list, str]:
    want = set(kernel.words(question)) - kernel.FUNCTION
    if not want:
        return [], "the question is common words only; say more"
    got = kernel.rank(pile, question, top=top, dated=dated)
    if got:
        return [(c, None, []) for c in got], f"held half of {sorted(want)}"
    return [], f"no passage holds half of {sorted(want)}"


def phrases_rung(ranker: pile_rank.Ranker, question: str, top: int) -> tuple[list, str]:
    asked = [t for t in ranker.terms(question) if " " in t]
    if not asked:
        return [], "the question uses none of the folder's phrases"
    got = [r for r in ranker.rank(question, len(ranker.texts)) if r[2]][:top]
    if got:
        return got, f"held {', '.join(asked)}"
    return [], f"no passage holds {', '.join(asked)}"


def climb(
    pile: list[dict], question: str, top: int, dated=None
) -> tuple[str | None, list[dict], list]:
    """(the rung that answered or None, every rung's state, what it served)."""
    rungs: list[dict] = []
    served: list = []
    answered = None
    for name in ("words", "phrases", "embedder"):
        if answered:
            rungs.append({"rung": name, "state": "skipped",
                          "why": f"{answered} answered"})  # fmt: skip
            continue
        if name == "words":
            got, why = words_rung(pile, question, top, dated)
        elif name == "phrases":
            got, why = phrases_rung(pile_rank.Ranker(pile), question, top)
        else:
            rungs.append({"rung": name, "state": "skipped", "why": NO_EMBEDDER})
            continue
        state = "answered" if got else "empty"
        if not got and why.startswith(("the question", "no embedder")):
            state = "skipped"
        rungs.append({"rung": name, "state": state, "why": why})
        if got:
            answered, served = name, got
    return answered, rungs, served


def usage() -> int:
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    words: list[str] = []
    it = iter(argv)
    for a in it:
        if a in ("--from", "--store", "--top"):
            opts[a] = next(it, "")
        elif a.startswith("--"):
            return usage()
        else:
            words.append(a)
    question = " ".join(words)
    if not opts.get("--from") or not question.strip():
        return usage()
    try:
        top = int(opts.get("--top", pile_rank.TOP))
    except ValueError:
        return usage()
    if top < 1 or "--store" in opts and not opts["--store"]:
        return usage()
    folder = Path(opts["--from"])
    if not folder.is_dir():
        print(f"refused: {opts['--from']} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    store = Path(opts["--store"]) if "--store" in opts else None
    pile, where = pile_rank.passages(folder, store)
    dated = (lambda p: [c["date"] for c in p]) if where == "store" else None
    rung, rungs, got = climb(pile, question, top, dated)
    served = []
    for r, (c, s, ph) in enumerate(got, 1):
        row = {"rank": r, "where": f"{c['path']}:{c['line']}", "id": c["id"]}
        if s is not None:
            row["score"] = round(s, 4)
        served.append({**row, "phrases": ph, "text": c["text"]})
    print(json.dumps({
        "question": question,
        "state": "populated" if served else "empty",
        "rung": rung,
        "read_from": where,
        "rungs": rungs,
        "served": served,
    }, ensure_ascii=False))  # fmt: skip
    return kernel.ALIVE if served else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
