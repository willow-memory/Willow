"""synonyms.py: words-list lines for a word no file has, from WordNet. Python 3.9+.

    python adapters/stdlib/synonyms/synonyms.py --box DIR --data DICT [--embed MODEL [--url URL]]
        ("your question" | --questions FILE)

    deferred = postponed, shelved
    # snooze: no file holds it, nor any of the dictionary's 3 other words for it

You ask in your words; your files answer in theirs. For each word of a
question that no file of yours holds, this looks the word up in WordNet, a
dictionary of which English words mean the same, and keeps only the ones your
files do hold, most passages first. Each is one line of a words list, your
word on the left, so the kernel reads it that way every time.

DICT is a folder holding WordNet's own database files (`index.noun`,
`data.noun` and the same for verb, adj and adv), which you get once from
Princeton or your system's packages; the card says where. It is read here by
these few lines, with nothing installed and nothing asked of the network.

A dictionary doesn't know which sense you meant: "postponed" brings "table"
(to table a motion) as well as "defer", and your files may hold "table" for
another reason. So read each line before you keep it. `--embed MODEL` helps:
a model on this machine that turns words into numbers (an embedder, such as
Ollama's nomic-embed-text) puts each line's words nearest your word first.
It only orders them; it drops none. URL is Ollama's http://127.0.0.1:11434/v1
unless you give another, and one off this machine is refused before a word
is sent.

Everything printed is a words list: a line that suggests nothing is a note,
after a `#`. With --questions, every question in FILE is read (one a line, or
`name<TAB>question`, as scan takes them) and each word is looked up once.

It reads only, and writes nothing, not even the record. Exit codes, the
kernel's: 0 every word no file holds got a line, or your files hold every
word; 42 a word got none, or the embedder couldn't be asked; 2 refused.
"""

from __future__ import annotations

import json
import math
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: WordNet's four kinds of word, as its files are named, in the order asked
KINDS = ("noun", "verb", "adj", "adv")
#: WordNet's own rules of detachment: an ending, and what a base form has there
ENDINGS = {
    "noun": (("s", ""), ("ses", "s"), ("xes", "x"), ("zes", "z"), ("ches", "ch"),
             ("shes", "sh"), ("men", "man"), ("ies", "y")),
    "verb": (("s", ""), ("ies", "y"), ("es", "e"), ("es", ""), ("ed", "e"),
             ("ed", ""), ("ing", "e"), ("ing", "")),
    "adj": (("er", ""), ("est", ""), ("er", "e"), ("est", "e")),
    "adv": (),
}  # fmt: skip


class Dictionary:
    """WordNet's database in a folder: which words share a meaning."""

    def __init__(self, folder: Path):
        self.folder = folder
        self.index: dict[str, dict[str, list[int]]] = {}
        for kind in KINDS:
            self.index[kind] = self._index(folder / f"index.{kind}")

    @staticmethod
    def missing(folder: Path) -> list[str]:
        """The database files a folder lacks, by name."""
        names = [f"{part}.{kind}" for kind in KINDS for part in ("index", "data")]
        return [n for n in names if not (folder / n).is_file()]

    @staticmethod
    def _index(path: Path) -> dict[str, list[int]]:
        """{a word: where each of its meanings starts in the data file}, most
        used meaning first, as the index lists them."""
        out: dict[str, list[int]] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith(" ") or not line.strip():
                continue  # the licence at the top of each file
            f = line.split()
            out[f[0]] = [int(x) for x in f[len(f) - int(f[2]) :]]
        return out

    def bases(self, word: str, kind: str) -> list[str]:
        """`word` as the dictionary lists it: itself, or with an ending off."""
        found = [word] if word in self.index[kind] else []
        for ending, base in ENDINGS[kind]:
            if word.endswith(ending) and len(word) > len(ending):
                b = word[: len(word) - len(ending)] + base
                if b in self.index[kind] and b not in found:
                    found.append(b)
        return found

    def meaning(self, kind: str, at: int) -> list[str]:
        """The words of the meaning that starts at byte `at` of a data file."""
        with open(self.folder / f"data.{kind}", "rb") as f:
            f.seek(at)
            row = f.readline().decode("utf-8").split()
        return [row[4 + 2 * i] for i in range(int(row[3], 16))]

    def others(self, word: str) -> list[str]:
        """Every other single word sharing a meaning with `word`, the most
        used meaning's first: no phrases, and never the word or its base."""
        mine = {word}
        out: list[str] = []
        for kind in KINDS:
            for base in self.bases(word, kind):
                mine.add(base)
                for at in self.index[kind][base]:
                    for w in self.meaning(kind, at):
                        w = w.split("(")[0].lower()
                        if kernel.words(w) == [w] and w not in out:
                            out.append(w)
        return [w for w in out if w not in mine]


def here(url: str) -> bool:
    """Whether a URL names this machine and nowhere else."""
    return urlsplit(url).scheme == "http" and urlsplit(url).hostname in (
        "127.0.0.1",
        "localhost",
        "::1",
    )


def embed(url: str, model: str, texts: list[str]) -> list[list[float]]:
    """Each text as the embedder's numbers, asked the way every
    OpenAI-compatible server on this machine answers. Raises OSError or
    ValueError when it can't be asked or answers in another shape."""
    req = urllib.request.Request(
        url.rstrip("/") + "/embeddings",
        json.dumps({"model": model, "input": texts}).encode("utf-8"),
        {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        rows = json.load(r)["data"]
    got = [[float(x) for x in row["embedding"]] for row in rows]
    if len(got) != len(texts) or not all(got):
        raise ValueError("an embedding for each word was not returned")
    return got


def nearness(a: list[float], b: list[float]) -> float:
    """The cosine of two embeddings: 1 the same direction, 0 unrelated."""
    size = math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))
    return sum(x * y for x, y in zip(a, b)) / size if size else 0.0


def nearest_first(word: str, kept: list[str], ask) -> list[str]:
    """`kept` with the words nearest `word` in meaning first, by `ask`'s
    embeddings; a tie keeps the order it came in."""
    mine, *theirs = ask([word, *kept])
    near = {o: nearness(mine, e) for o, e in zip(kept, theirs)}
    return sorted(kept, key=lambda o: -near[o])


def passages(pile: list[dict]) -> dict[str, int]:
    """{a word as the kernel holds it: how many passages hold it}."""
    out: dict[str, int] = {}
    for c in pile:
        for t in kernel.toks(c):
            out[t] = out.get(t, 0) + 1
    return out


def suggest(
    asked: list[str], held: dict[str, int], alias: dict, wn: Dictionary, ask=None
):
    """(the lines, the notes, whether a word was left with nothing) for the
    words of `asked` that no file holds: each line `word = others your files
    hold`, most passages first, or nearest in meaning first when `ask` gives
    embeddings; each note says why a word got no line."""
    every = set(held)
    lines: list[str] = []
    notes: list[str] = []
    for w in dict.fromkeys(asked):
        if w in kernel.FUNCTION or kernel.held_by(w, every, alias):
            continue
        others = wn.others(w)
        kept = sorted(
            (o for o in others if kernel.holds(o, every)),
            key=lambda o: (-(held.get(o) or held.get(kernel.stem(o), 0)), o),
        )
        if kept and ask is not None:
            kept = nearest_first(w, kept, ask)
        if kept:
            lines.append(f"{w} = {', '.join(kept)}")
        elif others:
            n = len(others)
            notes.append(
                f"# {w}: no file holds it, nor any of the dictionary's "
                f"{n} other word{'s' * (n != 1)} for it"
            )
        else:
            notes.append(
                f"# {w}: no file holds it, and the dictionary has no other word for it"
            )
    return lines, notes, bool(notes)


def questions(path: Path) -> list[str]:
    """Each question of a file: one a line, or `name<TAB>question`; blank
    lines and notes skipped."""
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            out.append(line.split("\t", 1)[-1])
    return out


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    args: list[str] = []
    it = iter(argv)
    for a in it:
        if a in ("--box", "--data", "--questions", "--embed", "--url"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if (
        not opts.get("--box")
        or not opts.get("--data")
        or bool(opts.get("--questions")) == bool(args)
        or len(args) > 1
        or ("--url" in opts and not opts.get("--embed"))
        or ("--embed" in opts and not opts["--embed"])
        or any(a.startswith("--") for a in args)
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box, data = Path(opts["--box"]), Path(opts["--data"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    _, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ", file=sys.stderr)
        return kernel.REFUSED
    url = opts.get("--url", "http://127.0.0.1:11434/v1")
    if "--embed" in opts and not here(url):
        print(
            f"refused: {url} is not on this machine; nothing was sent", file=sys.stderr
        )
        return kernel.REFUSED
    lacks = Dictionary.missing(data)
    if lacks:
        print(
            f"refused: {data} isn't WordNet's database; it has no {', '.join(lacks)}",
            file=sys.stderr,
        )
        return kernel.REFUSED
    if "--questions" in opts:
        try:
            asked_of = questions(Path(opts["--questions"]))
        except (OSError, ValueError) as e:
            print(
                f"refused: the questions could not be read: {type(e).__name__}",
                file=sys.stderr,
            )
            return kernel.REFUSED
    else:
        asked_of = args
    asked = [w for q in asked_of for w in kernel.words(q)]
    if not asked:
        print("refused: a question with no words", file=sys.stderr)
        return kernel.REFUSED
    cfg = kernel.config(box)
    alias: dict = {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            print(f"refused: {why}", file=sys.stderr)
            return kernel.REFUSED
    held = passages(kernel.chunks(Path(cfg["pile"])))
    ask = None
    if "--embed" in opts:

        def ask(texts: list[str]) -> list[list[float]]:
            return embed(url, opts["--embed"], texts)

    try:
        lines, notes, short = suggest(asked, held, alias, Dictionary(data), ask)
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(
            f"unreachable: {opts.get('--embed')} at {url} could not be asked "
            f"({type(e).__name__}); run it without --embed for the dictionary's own order",
            file=sys.stderr,
        )
        return kernel.ESCALATE
    if lines and ask is not None:
        notes.insert(
            0, f"# each line's words are nearest in meaning first, by {opts['--embed']}"
        )
    if not lines and not notes:
        print("# your files hold every word of it; nothing to suggest")
    print("\n".join(lines + notes), end="\n" if lines or notes else "")
    return kernel.ESCALATE if short else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
