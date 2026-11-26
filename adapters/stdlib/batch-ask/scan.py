"""scan.py: index a folder once, then ask it many questions, fast.

    python adapters/stdlib/scan/scan.py index --from FOLDER --to INDEX
    python adapters/stdlib/scan/scan.py scan --index INDEX [--index INDEX ...]
        --questions FILE [--words FILE] [--top N] [--changed-from INDEX] [--todo]
        [--rank kernel|bm25]

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

--changed-from INDEX asks each question of only the passages that INDEX
lacks: what changed since it, or before it. They are ranked as the kernel
ranks a folder holding only them, and dated as they are in their own folder
(a log's date heading that didn't change still dates the lines under it).
Index a release and its fix, and the questions are asked of the fix.

--todo adds, to each passage served, the lines its file marks to do, by the
todo add-on's own marks (TODO, FIXME, "need to", ...): what the file's
authors wrote down as not yet right, beside what was found.

--rank bm25 ranks by BM25 instead of by the kernel: the same words, split
the kernel's way with its common words dropped, but scored by how often each
appears against how rare it is. Its answers are not the kernel's, and each
says "ranked_by": "bm25". It takes no words list. On PHP's source it found
more of the PHP2Shell fix than the kernel's rank did (demo/php2shell).

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

import array
import json
import math
import mmap
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "todo"))
import kernel  # noqa: E402
import todo  # noqa: E402

FORMAT = "willow-scan/1"
#: index.json last: it means done. offsets.bin (where each passage's line
#: starts, eight bytes each, little-endian) and copies.tsv (each text held
#: more than once, by its id, and the passages holding it) let a question
#: read only the passages and words it needs; an index without them is read
#: whole, as before
FILES = ("chunks.jsonl", "words.tsv", "offsets.bin", "copies.tsv", "index.json")


def build(folder: Path, to: Path) -> int:
    """Write the index of `folder` to `to`; the number of passages."""
    return build_from(kernel.chunks(folder), to)


def build_from(pile: list[dict], to: Path) -> int:
    """Write the index of passages the kernel read (a folder's, or a list's
    files where they are kept) to `to`; the number of passages."""
    days = kernel.dates(pile)
    post: dict[str, list[int]] = {}
    for i, c in enumerate(pile):
        for t in kernel.toks(c):
            post.setdefault(t, []).append(i)
    to.mkdir(exist_ok=True)
    (to / "index.json").unlink(missing_ok=True)
    offsets = array.array("Q")
    at = 0
    with open(to / "chunks.jsonl", "wb") as f:
        for c, d in zip(pile, days):
            line = (kernel.canon({**c, "date": d}) + "\n").encode("utf-8")
            offsets.append(at)
            f.write(line)
            at += len(line)
    if sys.byteorder != "little":
        offsets.byteswap()
    (to / "offsets.bin").write_bytes(offsets.tobytes())
    copies: dict[str, list[int]] = {}
    for i, c in enumerate(pile):
        copies.setdefault(c["id"], []).append(i)
    with open(to / "copies.tsv", "w", encoding="utf-8", newline="\n") as f:
        for k in sorted(k for k, v in copies.items() if len(v) > 1):
            f.write(k + "\t" + " ".join(map(str, copies[k])) + "\n")
    with open(to / "words.tsv", "w", encoding="utf-8", newline="\n") as f:
        for t in sorted(post):
            f.write(t + "\t" + " ".join(map(str, post[t])) + "\n")
    head = {
        "format": FORMAT,
        "kernel": kernel.VERSION,
        "chunks": len(pile),
        "files": len({c["path"] for c in pile}),
        "ids": kernel.h256("\n".join(c["id"] for c in pile)),
        "bytes": at,
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


def head_of(at: Path) -> dict:
    """An index's index.json, once it says the index is whole and this
    kernel.py's; ValueError otherwise."""
    try:
        head = json.loads((at / "index.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ValueError(f"{at} is not an index; make one with index") from None
    if head.get("format") != FORMAT:
        raise ValueError(f"{at} is an index of another kind: {head.get('format')}")
    if head.get("kernel") != kernel.VERSION:
        raise ValueError(f"{at} was made with another kernel.py; index again")
    return head


class Lines:
    """A file of lines sorted by their key (`key<TAB>rest`, keys compared as
    UTF-8 bytes, which is the order of `sorted` on the words), a line found
    by a binary search over the bytes of the file itself: only the few lines
    the search lands on are read."""

    def __init__(self, path: Path):
        self.f = open(path, "rb")
        size = path.stat().st_size
        self.mm = (
            mmap.mmap(self.f.fileno(), 0, access=mmap.ACCESS_READ) if size else b""
        )

    def _line(self, start: int) -> tuple[bytes, int]:
        """The key of the line starting at start, and where the next starts."""
        mm = self.mm
        end = mm.find(b"\n", start)
        end = len(mm) if end < 0 else end
        tab = mm.find(b"\t", start, end)
        return mm[start : end if tab < 0 else tab], end + 1

    def get(self, key: str, default: str = "") -> str:
        """The rest of key's line, or default when there is none, as a dict's
        get would answer."""
        want, mm = key.encode("utf-8"), self.mm
        lo, hi = 0, len(mm)  # lo and hi each the start of a line, or the end
        while lo < hi:
            mid = (lo + hi) // 2
            start = mm.rfind(b"\n", 0, mid) + 1 if mid > lo else lo
            k, nxt = self._line(start)
            if k < want:
                lo = nxt
            else:
                hi = start
        if lo < len(mm):
            k, nxt = self._line(lo)
            if k == want:
                return mm[lo + len(k) + 1 : nxt - 1].decode("utf-8")
        return default

    def keys(self):
        at = 0
        while at < len(self.mm):
            k, at = self._line(at)
            yield k.decode("utf-8")


class Index:
    """One index, read back: its passages in the kernel's order, their dates,
    and each word's passages, parsed only when a question asks for it. An
    index with offsets.bin and copies.tsv is read a passage and a word at a
    time, only those a question needs; one without them is read whole."""

    def __init__(self, at: Path):
        self.name, self.at = at.name, at
        self.day = {}
        self.lengths: dict[int, int] | None = None  # words a passage, for bm25
        self._pile: list[dict] | None = None
        self._files: dict[str, list[int]] | None = None
        head = head_of(at)
        lazy = (
            (at / "offsets.bin").is_file()
            and (at / "copies.tsv").is_file()
            and head.get("bytes") == (at / "chunks.jsonl").stat().st_size
        )
        if not lazy:
            self._pile = passages(at)
            for c in self._pile:
                self.day[id(c)] = c.pop("date")
            self.copies: dict[str, list[int]] = {}
            for i, c in enumerate(self._pile):
                self.copies.setdefault(c["id"], []).append(i)
            self.words = {}
            with open(at / "words.tsv", encoding="utf-8") as f:
                for line in f:
                    t, _, ns = line.rstrip("\n").partition("\t")
                    self.words[t] = ns
            self.n = len(self._pile)
            return
        raw = array.array("Q")
        raw.frombytes((at / "offsets.bin").read_bytes())
        if sys.byteorder != "little":
            raw.byteswap()
        self.offsets, self.n = raw, len(raw)
        if self.n != head.get("chunks"):
            raise ValueError(f"{at}: its offsets don't match its index.json")
        self._chunks = open(at / "chunks.jsonl", "rb")
        size = head["bytes"]
        self._mm = (
            mmap.mmap(self._chunks.fileno(), 0, access=mmap.ACCESS_READ)
            if size
            else b""
        )
        self._read: dict[int, dict] = {}
        self.copies = {}
        with open(at / "copies.tsv", encoding="utf-8") as f:
            for line in f:
                k, _, ns = line.rstrip("\n").partition("\t")
                self.copies[k] = list(map(int, ns.split()))
        self.words = Lines(at / "words.tsv")

    def chunk(self, i: int) -> dict:
        """Passage i, read from its line when it is first asked for."""
        if self._pile is not None:
            return self._pile[i]
        got = self._read.get(i)
        if got is None:
            at = self.offsets[i]
            end = self.offsets[i + 1] if i + 1 < self.n else len(self._mm)
            got = json.loads(self._mm[at:end].decode("utf-8"))
            self.day[id(got)] = got.pop("date")
            self._read[i] = got
        return got

    @property
    def pile(self) -> list[dict]:
        """Every passage, read whole the first time it is wanted."""
        if self._pile is None:
            self._pile = [self.chunk(i) for i in range(self.n)]
        return self._pile

    @property
    def files(self) -> dict[str, list[int]]:
        if self._files is None:
            self._files = {}
            for i, c in enumerate(self.pile):
                self._files.setdefault(c["path"], []).append(i)
        return self._files

    def copies_of(self, i: int) -> list[int]:
        """Every passage holding passage i's text: i alone unless copies.tsv
        names it (or, read whole, the copies counted then)."""
        return self.copies.get(self.chunk(i)["id"], [i])

    def terms(self):
        """Every word the index holds."""
        return iter(self.words) if isinstance(self.words, dict) else self.words.keys()

    def holding(self, t: str) -> set[int]:
        return set(map(int, self.words.get(t, "").split()))

    def near(
        self, question: str, alias: dict, lacked_by: set | None = None
    ) -> list[dict]:
        """The passages holding enough of the question's words for `rank` to
        keep them, each word held the way the kernel's `held_by` holds it,
        with every copy of each one's text, since `rank` counts a text's
        copies across the whole folder. With `lacked_by`, a set of ids, only
        the passages whose ids it lacks, and so only their copies."""
        want = set(kernel.words(question)) - kernel.FUNCTION
        count: dict[int, int] = {}
        for w in want:
            got: set[int] = set()
            for x in [w, *alias.get(w, [])]:
                got |= self.holding(x) | self.holding(kernel.stem(x))
                if len(x) >= 4 and any(ch.isdigit() for ch in x):
                    for t in self.terms():
                        if t.startswith(x) or t.endswith(x):
                            got |= self.holding(t)
            for i in got:
                count[i] = count.get(i, 0) + 1
        kept = [i for i, n in count.items() if n >= kernel.HOLD * len(want)]
        if lacked_by is not None:
            kept = [i for i in kept if self.chunk(i)["id"] not in lacked_by]
        every = {j for i in kept for j in self.copies_of(i)}
        return [self.chunk(i) for i in sorted(every)]

    def rank(
        self, question: str, alias: dict, top: int, lacked_by: set | None = None
    ) -> list[dict]:
        near = self.near(question, alias, lacked_by)
        return kernel.rank(
            near, question, alias, top, lambda pile: [self.day[id(c)] for c in pile]
        )

    def bm25(self, question: str, top: int, lacked_by: set | None = None) -> list[dict]:
        """BM25 (k1 1.2, b 0.75) over the passages' words, split and with
        common words dropped as the kernel does, but ranked by BM25, not by
        the kernel: an answer here is not one a `bite` would give. With
        `lacked_by`, over only the passages whose ids it lacks, counted as a
        folder of their own. Equal scores keep the index's order."""
        if lacked_by is None:
            pool = range(len(self.pile))
        else:
            pool = [i for i, c in enumerate(self.pile) if c["id"] not in lacked_by]
        if lacked_by is not None or self.lengths is None:
            lengths = {i: len(kernel.words(self.pile[i]["text"])) for i in pool}
            if lacked_by is None:
                self.lengths = lengths
        else:
            lengths = self.lengths
        inside = set(lengths)
        n, avg = len(lengths), sum(lengths.values()) / max(len(lengths), 1)
        ws = [
            w for w in dict.fromkeys(kernel.words(question)) if w not in kernel.FUNCTION
        ]
        docs: dict[int, list[str]] = {}
        df: dict[str, int] = {}
        for w in ws:  # a word's passages are among those holding it, by the index
            for i in self.holding(w) & inside:
                d = docs.setdefault(i, kernel.words(self.pile[i]["text"]))
                df[w] = df.get(w, 0) + (w in d)
        scored = []
        for i, d in docs.items():
            s = 0.0
            for w in ws:
                f = d.count(w)
                if f:
                    idf = math.log((n - df[w] + 0.5) / (df[w] + 0.5) + 1)
                    s += (
                        idf
                        * f
                        * (1.2 + 1)
                        / (f + 1.2 * (1 - 0.75 + 0.75 * lengths[i] / avg))
                    )
            if s > 0:
                scored.append((-s, i))
        return [self.pile[i] for _, i in sorted(scored)][:top]

    def marked(self, path: str) -> list[dict]:
        """The lines `path` marks to do, by the todo add-on's marks."""
        return [
            {"where": f"{path}:{c['line'] + n}", "text": line.strip()[:120]}
            for c in (self.pile[i] for i in self.files.get(path, []))
            for n, line in enumerate(c["text"].splitlines())
            if todo.MARK.search(line)
        ]


def questions(text: str) -> list[tuple[str, str]]:
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        name, tab, q = line.partition("\t")
        out.append((name.strip(), q.strip()) if tab else (str(n), line.strip()))
    return out


def scan(
    paths: list[Path],
    qs: list[tuple[str, str]],
    alias: dict,
    top: int,
    base: Path | None = None,
    marks: bool = False,
    by: str = "kernel",
) -> int:
    """Print each answer of each index; the kernel's exit code over them all."""
    names = [p.name for p in paths]
    if len(set(names)) != len(names):
        raise ValueError("two indexes have the same folder name: " + ", ".join(names))
    # every index checked, and its ids kept, before a line is printed; then
    # one whole index in memory at a time
    ids = {p.name: {c["id"] for c in passages(p)} for p in paths}
    lacked_by = None if base is None else {c["id"] for c in passages(base)}
    held = False
    for p in paths:
        ix = Index(p)
        others = [n for n in names if n != ix.name]
        for name, q in qs:
            served = []
            got = (
                ix.bm25(q, top, lacked_by)
                if by == "bm25"
                else ix.rank(q, alias, top, lacked_by)
            )
            for i, c in enumerate(got, 1):
                s = {
                    "rank": i,
                    "where": f"{c['path']}:{c['line']}",
                    "id": c["id"],
                    "echo": kernel.echo(q, c["text"]),
                    "text": c["text"],
                    "held_in": [n for n in others if c["id"] in ids[n]],
                    "gone_from": [n for n in others if c["id"] not in ids[n]],
                }
                if marks:
                    s["marked"] = ix.marked(c["path"])
                served.append(s)
            held = held or bool(served)
            state = "populated" if served else "empty"
            row = {"index": ix.name, "question": name, "state": state}
            if by != "kernel":
                row["ranked_by"] = by
            if base is not None:
                row["changed_from"] = base.name
            print(json.dumps({**row, "served": served}, ensure_ascii=False))
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
        "scan": {
            "--index",
            "--questions",
            "--words",
            "--top",
            "--changed-from",
            "--rank",
        },
    }
    flags = {"scan": {"--todo"}}.get(cmd, set())
    for a in it:
        if a in flags and a not in opts:
            opts[a] = True
            continue
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
        if not to.parent.is_dir():
            print(
                f"refused: {to.parent} is not a folder; make it first", file=sys.stderr
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
    by = opts.get("--rank", "kernel")
    if not {"--index", "--questions"} <= set(opts) or not top.isdigit() or int(top) < 1:
        return usage()
    if by not in ("kernel", "bm25") or (by == "bm25" and "--words" in opts):
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
        base = Path(opts["--changed-from"]) if "--changed-from" in opts else None
        paths = [Path(p) for p in opts["--index"]]
        return scan(paths, qs, alias, int(top), base, "--todo" in opts, by)
    except (OSError, ValueError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
