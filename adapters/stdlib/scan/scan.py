"""scan.py: index a folder once, then ask it many questions, fast.

    python adapters/stdlib/scan/scan.py index --from FOLDER --to INDEX
    python adapters/stdlib/scan/scan.py scan --index INDEX [--index INDEX ...]
        --questions FILE [--words FILE] [--top N]

The kernel reads the whole folder on every question; that is its promise and
its cost. A large folder (a programming language's source, 400,000
passages) takes it a minute and a half a question. `index` does the reading
once: the kernel's own passages, each one's date as the kernel gives it, and
which passages hold each word. `scan` asks every question in FILE of every
index, and each answer is exactly the kernel's: the index only narrows which
passages the kernel's own `rank` looks at, to those holding a word of the
question.

FILE holds one question a line, optionally `name<TAB>question`; blank lines
and `#` lines are skipped. Each answer is one JSON line:

    {"index": "8.5.11", "question": "618a", "state": "populated",
     "served": [{"rank": 1, "where": ..., "id": ..., "text": ...,
                 "held_in": ["8.5.12"], "gone_from": ["8.4.27"]}]}

A passage's id is the SHA-256 of its text, so asked of two indexes (two
releases, two backups) `gone_from` names each other index without those exact
words: the words changed there, or went. Nothing else is compared.

An index is the folder as it was read: index again after the folder
changes. One made with another kernel.py is refused, since its passages,
words and dates were the other kernel's.

It never writes the folder, or the record, and `scan` writes nothing. Exit
codes, the kernel's: 0 something holds a question; 42 nothing holds any, or
the folder had nothing to read; 2 refused.

How: the kernel's `rank` stops at `TOP` (3) and dates the passages it is
given with `dates`. For one call, in this process only, this lifts `TOP` to
`--top` and answers `dates` from the index, then puts both back; `kernel.py`
is never changed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

FORMAT = "willow-scan/1"
FILES = ("chunks.jsonl", "words.tsv", "index.json")  # index.json last: it means done


def build(folder: Path, to: Path) -> int:
    """Write the index of `folder` to `to`; the number of passages."""
    pile = kernel.chunks(folder)
    days = kernel.dates(pile)
    post: dict[str, list[int]] = {}
    for i, c in enumerate(pile):
        for t in kernel.toks(c):
            post.setdefault(t, []).append(i)
    to.mkdir(parents=True, exist_ok=True)
    (to / "index.json").unlink(missing_ok=True)
    with open(to / "chunks.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for c, d in zip(pile, days):
            f.write(kernel.canon({**c, "date": d}) + "\n")
    with open(to / "words.tsv", "w", encoding="utf-8", newline="\n") as f:
        for t in sorted(post):
            f.write(t + "\t" + " ".join(map(str, post[t])) + "\n")
    head = {
        "format": FORMAT,
        "kernel": kernel.VERSION,
        "chunks": len(pile),
        "files": len({c["path"] for c in pile}),
        "ids": kernel.h256("\n".join(c["id"] for c in pile)),
    }
    (to / "index.json").write_text(kernel.canon(head) + "\n", encoding="utf-8")
    return len(pile)


def passages(at: Path) -> list[dict]:
    """An index's passages, each with its date, once its index.json says it
    is a whole index made by this kernel.py and its passages are the ones it
    names."""
    try:
        head = json.loads((at / "index.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ValueError(f"{at} is not an index; make one with index") from None
    if head.get("format") != FORMAT:
        raise ValueError(f"{at} is an index of another kind: {head.get('format')}")
    if head.get("kernel") != kernel.VERSION:
        raise ValueError(f"{at} was made with another kernel.py; index again")
    with open(at / "chunks.jsonl", encoding="utf-8") as f:
        pile = [json.loads(line) for line in f]
    if kernel.h256("\n".join(c["id"] for c in pile)) != head["ids"]:
        raise ValueError(f"{at}: its passages don't match its index.json")
    return pile


class Index:
    """One index, read back: its passages in the kernel's order, their dates,
    and each word's passages, parsed only when a question asks for it."""

    def __init__(self, at: Path):
        self.name = at.name
        self.pile, self.day = passages(at), {}
        for c in self.pile:
            self.day[id(c)] = c.pop("date")
        self.copies: dict[str, list[int]] = {}
        for i, c in enumerate(self.pile):
            self.copies.setdefault(c["id"], []).append(i)
        self.words = {}
        with open(at / "words.tsv", encoding="utf-8") as f:
            for line in f:
                t, _, ns = line.rstrip("\n").partition("\t")
                self.words[t] = ns

    def holding(self, t: str) -> set[int]:
        return set(map(int, self.words.get(t, "").split()))

    def near(self, question: str, alias: dict) -> list[dict]:
        """The passages holding enough of the question's words for `rank` to
        keep them, each word held the way the kernel's `held_by` holds it,
        with every copy of each one's text, since `rank` counts a text's
        copies across the whole folder."""
        want = set(kernel.words(question)) - kernel.FUNCTION
        count: dict[int, int] = {}
        for w in want:
            got: set[int] = set()
            for x in [w, *alias.get(w, [])]:
                got |= self.holding(x) | self.holding(kernel.stem(x))
                if len(x) >= 4 and any(ch.isdigit() for ch in x):
                    for t in self.words:
                        if t.startswith(x) or t.endswith(x):
                            got |= self.holding(t)
            for i in got:
                count[i] = count.get(i, 0) + 1
        kept = [i for i, n in count.items() if n >= kernel.HOLD * len(want)]
        every = {j for i in kept for j in self.copies[self.pile[i]["id"]]}
        return [self.pile[i] for i in sorted(every)]

    def rank(self, question: str, alias: dict, top: int) -> list[dict]:
        top_was, dates_was = kernel.TOP, kernel.dates
        kernel.TOP = top
        kernel.dates = lambda pile: [self.day[id(c)] for c in pile]
        try:
            return kernel.rank(self.near(question, alias), question, alias)
        finally:
            kernel.TOP, kernel.dates = top_was, dates_was


def questions(text: str) -> list[tuple[str, str]]:
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        name, tab, q = line.partition("\t")
        out.append((name.strip(), q.strip()) if tab else (str(n), line.strip()))
    return out


def scan(paths: list[Path], qs: list[tuple[str, str]], alias: dict, top: int) -> int:
    """Print each answer of each index; the kernel's exit code over them all."""
    names = [p.name for p in paths]
    if len(set(names)) != len(names):
        raise ValueError("two indexes have the same folder name: " + ", ".join(names))
    # every index checked, and its ids kept, before a line is printed; then
    # one whole index in memory at a time
    ids = {p.name: {c["id"] for c in passages(p)} for p in paths}
    held = False
    for p in paths:
        ix = Index(p)
        others = [n for n in names if n != ix.name]
        for name, q in qs:
            served = [
                {
                    "rank": i,
                    "where": f"{c['path']}:{c['line']}",
                    "id": c["id"],
                    "echo": kernel.echo(q, c["text"]),
                    "text": c["text"],
                    "held_in": [n for n in others if c["id"] in ids[n]],
                    "gone_from": [n for n in others if c["id"] not in ids[n]],
                }
                for i, c in enumerate(ix.rank(q, alias, top), 1)
            ]
            held = held or bool(served)
            state = "populated" if served else "empty"
            row = {"index": ix.name, "question": name, "state": state, "served": served}
            print(json.dumps(row, ensure_ascii=False))
    return kernel.ALIVE if held else kernel.ESCALATE


def usage() -> int:
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("index", "scan"):
        return usage()
    cmd, opts, it = argv[0], {}, iter(argv[1:])
    takes = {
        "index": {"--from", "--to"},
        "scan": {"--index", "--questions", "--words", "--top"},
    }
    for a in it:
        v = next(it, "")
        if a not in takes[cmd] or not v or (a in opts and a != "--index"):
            return usage()
        opts[a] = opts.get(a, []) + [v] if a == "--index" else v
    if cmd == "index":
        if set(opts) != takes["index"]:
            return usage()
        src, to = Path(opts["--from"]).resolve(), Path(opts["--to"]).resolve()
        if not src.is_dir():
            print(f"refused: {opts['--from']} is not a folder", file=sys.stderr)
            return kernel.REFUSED
        if to.is_relative_to(src) or src.is_relative_to(to):
            print(
                "refused: the index and the folder can't hold each other",
                file=sys.stderr,
            )
            return kernel.REFUSED
        if to.exists() and (not to.is_dir() or (
            any(to.iterdir()) and not (to / "index.json").exists())):  # fmt: skip
            print(
                f"refused: {opts['--to']} holds something that isn't an index",
                file=sys.stderr,
            )
            return kernel.REFUSED
        n = build(src, to)
        print(f"indexed {n} passages to {opts['--to']}")
        return kernel.ALIVE if n else kernel.ESCALATE
    top = opts.get("--top", str(kernel.TOP))
    if not {"--index", "--questions"} <= set(opts) or not top.isdigit() or int(top) < 1:
        return usage()
    try:
        qs = questions(Path(opts["--questions"]).read_text(encoding="utf-8"))
        alias: dict = {}
        if "--words" in opts:
            alias, why = kernel.parse_words(
                Path(opts["--words"]).read_text(encoding="utf-8")
            )
            if why:
                raise ValueError(why)
        if not qs:
            raise ValueError(f"{opts['--questions']} holds no question")
        return scan([Path(p) for p in opts["--index"]], qs, alias, int(top))
    except (OSError, ValueError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
