"""pile_rank.py: phrases as well as words. BM25F over each passage's words and
the word pairs the folder uses together, title and question lines weighted,
no model. Python 3.9+.

    python adapters/stdlib/pile-rank/pile_rank.py --from FOLDER [--store STORE]
        [--top N] QUESTION...

Each passage is read as three fields: its body; its title, the file's path
and any heading line (`# ...`); and its question lines, those ending in `?`.
A term is a word, split and with common words dropped the kernel's way and
taken in its plain form (`kernel.stem`), or a pair of such words next to each
other in one clause of a line (no comma or full stop between), kept only
when two or more of the folder's texts use that pair. "sourdough bread" is then one term in a folder that bakes, and a
passage saying it outranks one that says "bread" here and "sourdough" there.

Scored by BM25F: each field's count of a term, weighted (title 2, question
lines 1.5, body 1) and normalised by that field's length against its mean
(b 0.75), summed, then saturated (k1 1.2) and weighed by the term's rarity.
Each text is served once, at its first place; equal scores keep the kernel's
order. The answer is one JSON line:

    {"question": "...", "state": "populated", "ranked_by": "pile-rank",
     "read_from": "store", "served": [{"rank": 1, "where": "path:line",
     "id": ..., "score": 3.1, "phrases": ["sourdough bread"], "text": ...}]}

This points at where to look; it is not the kernel's answer. The kernel serves
a passage only when it holds half the question's words, and this serves its
top passages whatever they hold, as `scan --rank bm25` does.

With --store, the passages come from a pile-store store while it still
matches the folder; when it doesn't, the folder is read as the kernel reads
it, and the answer says "read_from": "folder". It writes nothing, not even
the store: build that with pile-store. Exit codes, the kernel's: 0 something
was served; 42 nothing holds a word of the question, or the folder has
nothing to read; 2 refused.
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "pile-store"))
import kernel  # noqa: E402
import pile_store  # noqa: E402

TOP = 5
K1, B = 1.2, 0.75
WEIGHT = {"title": 2.0, "asks": 1.5, "body": 1.0}
PAIRED = 2  # texts that must use a pair before it is a phrase of the folder
BREAK = re.compile(r"[.,;:!?()\[\]{}\"|]")  # a pair never spans one


def line_terms(line: str) -> list[str]:
    """A line's words in their plain forms, common words dropped."""
    return [kernel.stem(w) for w in kernel.words(line) if w not in kernel.FUNCTION]


def clauses(line: str) -> list[list[str]]:
    """A line's terms, cut at punctuation: "sourdough, bread" is no pair."""
    return [ts for part in BREAK.split(line) if (ts := line_terms(part))]


def pairs(ws: list[str]) -> list[str]:
    return [f"{a} {b}" for a, b in zip(ws, ws[1:])]


def fields(c: dict) -> dict[str, list[list[str]]]:
    """A passage's three fields, each as its clauses' terms."""
    lines = c["text"].splitlines()
    return {
        "body": [ts for x in lines for ts in clauses(x)],
        "title": [line_terms(c["path"])]
        + [ts for x in lines if x.lstrip().startswith("#") for ts in clauses(x)],
        "asks": [ts for x in lines if x.rstrip().endswith("?") for ts in clauses(x)],
    }


class Ranker:
    """The folder's passages, counted once, ready for any number of questions."""

    def __init__(self, pile: list[dict]):
        self.pile = pile
        first: dict[str, int] = {}
        for i, c in enumerate(pile):
            first.setdefault(c["id"], i)
        self.texts = sorted(first.values())  # each text once, at its first place
        split = {i: fields(pile[i]) for i in self.texts}
        users: dict[str, int] = {}
        for f in split.values():
            for p in {p for ln in f["body"] for p in pairs(ln)}:
                users[p] = users.get(p, 0) + 1
        self.phrases = {p for p, n in users.items() if n >= PAIRED}
        self.counts: dict[int, dict[str, dict[str, int]]] = {}
        self.length: dict[int, dict[str, int]] = {}
        self.post: dict[str, list[int]] = {}
        for i, f in split.items():
            per: dict[str, dict[str, int]] = {}
            for name, lines in f.items():
                got: dict[str, int] = {}
                for ln in lines:
                    for t in ln + [p for p in pairs(ln) if p in self.phrases]:
                        got[t] = got.get(t, 0) + 1
                per[name] = got
            self.counts[i] = per
            self.length[i] = {n: sum(len(ln) for ln in f[n]) for n in f}
            for t in {t for got in per.values() for t in got}:
                self.post.setdefault(t, []).append(i)
        n = max(len(self.texts), 1)
        self.mean = {
            name: sum(x[name] for x in self.length.values()) / n for name in WEIGHT
        }

    def terms(self, question: str) -> list[str]:
        """The question's words, then the folder's phrases among its pairs."""
        cs = clauses(question)
        ps = [p for ts in cs for p in pairs(ts) if p in self.phrases]
        return list(dict.fromkeys([t for ts in cs for t in ts] + ps))

    def rank(self, question: str, top: int = TOP) -> list[tuple[dict, float, list]]:
        """(passage, score, the phrases it holds) for the `top` best, best first."""
        ts = [t for t in self.terms(question) if t in self.post]
        n = len(self.texts)
        score: dict[int, float] = {}
        for t in ts:
            df = len(self.post[t])
            idf = math.log((n - df + 0.5) / (df + 0.5) + 1)
            for i in self.post[t]:
                tf = 0.0
                for name, w in WEIGHT.items():
                    f = self.counts[i][name].get(t, 0)
                    if f:
                        mean = self.mean[name] or 1
                        tf += w * f / (1 - B + B * self.length[i][name] / mean)
                score[i] = score.get(i, 0.0) + idf * tf * (K1 + 1) / (tf + K1)
        best = sorted(score, key=lambda i: (-score[i], i))[:top]
        return [
            (
                self.pile[i],
                score[i],
                [t for t in ts if " " in t and t in self.counts[i]["body"]],
            )
            for i in best
        ]


def passages(folder: Path, store: Path | None) -> tuple[list[dict], str]:
    """The folder's passages, from the store while it matches, else the folder."""
    if store is not None:
        got = pile_store.load(store, folder)
        if got is not None:
            return got, "store"
    return kernel.chunks(folder), "folder"


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
        top = int(opts.get("--top", TOP))
    except ValueError:
        return usage()
    if top < 1 or "--store" in opts and not opts["--store"]:
        return usage()
    folder = Path(opts["--from"])
    if not folder.is_dir():
        print(f"refused: {opts['--from']} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    store = Path(opts["--store"]) if "--store" in opts else None
    pile, where = passages(folder, store)
    got = Ranker(pile).rank(question, top)
    served = [
        {
            "rank": r,
            "where": f"{c['path']}:{c['line']}",
            "id": c["id"],
            "score": round(s, 4),
            "phrases": ph,
            "text": c["text"],
        }
        for r, (c, s, ph) in enumerate(got, 1)
    ]
    row = {
        "question": question,
        "state": "populated" if served else "empty",
        "ranked_by": "pile-rank",
        "read_from": where,
        "served": served,
    }
    print(json.dumps(row, ensure_ascii=False))
    return kernel.ALIVE if served else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
