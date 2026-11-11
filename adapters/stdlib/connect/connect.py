"""connect.py: what a model on this machine says connects two passages. Python 3.9+.

    python adapters/stdlib/connect/connect.py --box DIR --first PLACE --second PLACE
        [--model TAG] [--host HOST:PORT] [--chars N] [--timeout SECONDS] [--json]
    python adapters/stdlib/connect/connect.py --box DIR --pairs FILE [the same options]

    connect: populated, 1 pair: 1 connection said, every number and name in it is in the passages
    ## invoices.txt:1 and work/log.csv:98, by llama3.2:3b
      invoices.txt:1   overdue INV-2026-011 Larkfield Community Theatre $640.00 due 2026-06-27
      work/log.csv:98  2026-05-28, Larkfield Community Theatre, Wurlitzer studio upright, service visit, 640.00, INV-2026-011
      said             The first is an overdue invoice and the second is the service visit it bills: the same theatre, invoice number INV-2026-011 and amount.
      checked          every number and name it gives is in one of the two passages, and it speaks of both

Code finds where a thing is. It can't say why two places belong together
unless they share a number or a name. A small model can: asked one plain
question about two passages, it answers in a few sentences. This asks it,
and checks the part of the answer that can be checked.

A PLACE is a file of your folder and a line in it, as every report writes
one: `notes/iou.txt:3`. The passage is the kernel's own, the one holding
that line. The model is asked only this, and nothing about format:

    What's the connection between these two?
    First: (the first passage)
    Second: (the second passage)
    Answer in a few plain sentences, under 500 characters.

--chars sets the 500. Short is the point: a model given room to fill finds
a connection between any two things, and one held to a few sentences says
the one thing it sees, or that there is none.

What is checked: every number, and every word with a capital letter or a
digit in it, that the answer gives is looked for in the two passages. One
found in neither is named, and the exit code is 42: the model added it. An
answer that uses no word belonging to one of the two passages alone is
named too: it has described one end, not connected them.
What is not checked, and can't be: the reading itself. It is the model's,
said as the model's, and yours to judge.

--pairs FILE is many pairs, one a line: two places with a tab between
them. Blank lines and lines that start with # are skipped.

The model is Ollama's, on this machine only, asked as the say add-on asks
it; any other address is not asked. --model is the tag (llama3.2:3b).

It reads the two files and asks the model on this machine. It writes
nothing: no row on your record, and no suggestion, since a suggestion can
cite only what your last question was served. It prints a report
(ci/README.md, "The report contract"); --json gives the same as one
object. Exit codes, the kernel's: 0 every pair has a connection said and
nothing in it was added; 42 a pair's answer names something neither
passage holds, a place has no passage, or the model couldn't be asked; 2
refused.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = (
    "usage: connect.py --box DIR (--first PLACE --second PLACE | --pairs FILE) "
    "[--model TAG] [--host HOST:PORT] [--chars N] [--timeout SECONDS] [--json]"
)
NAME = "connect"
STDLIB = Path(__file__).resolve().parents[1]
MODEL = "llama3.2:3b"
#: how many characters the answer is asked to stay under
CHARS = 500
#: how much of a passage is shown on its row
SHOWN = 160
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)*")
#: a word that names something: it holds a capital letter or a digit
TOKEN = re.compile(r"[^\W_][\w'’-]*")


def sibling(folder: str, module: str):
    """Another add-on's module, from its source beside this one."""
    path = STDLIB / folder / f"{module}.py"
    mod = types.ModuleType(f"connect_{module}")
    mod.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), mod.__dict__)
    return mod


def flat(text: str) -> str:
    return " ".join(text.split())


def short(text: str, most: int = SHOWN) -> str:
    one = flat(text)
    return one if len(one) <= most else one[:most].rsplit(" ", 1)[0] + "…"


def place(text: str) -> tuple[str, int] | None:
    """(file, line) for a place written `file:line`, or None."""
    path, colon, line = text.strip().rpartition(":")
    if not colon or not path or not line.isdigit() or int(line) < 1:
        return None
    return path, int(line)


def passage(pile: Path, path: str, line: int) -> dict | None:
    """The kernel's passage of a file that holds a line: the kernel's own
    `chunks`, run on a scratch copy of that one file at the same path. None
    when the file isn't in the folder, is one the kernel doesn't read, or
    has no passage at that line."""
    src = pile / path
    try:
        inside = src.resolve().is_relative_to(pile.resolve())
        if not inside or not src.is_file() or src.stat().st_size > kernel.MAX_FILE:
            return None
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / path
            copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, copy)
            chunks = kernel.chunks(Path(tmp))
    except (OSError, ValueError):
        return None
    for c in chunks:
        if c["line"] <= line < c["line"] + c["text"].count("\n") + 1:
            return c
    return None


def question(first: str, second: str, chars: int = CHARS) -> str:
    """The one plain question a small model is asked. No rules, no format:
    those are what small models don't follow."""
    return (
        "What's the connection between these two?\n\n"
        f"First: {flat(first)}\n\nSecond: {flat(second)}\n\n"
        f"Answer in a few plain sentences, under {chars} characters."
    )


def _norm(n: str) -> str:
    """A number as it is compared: no commas, and 640.00 the same as 640."""
    n = n.replace(",", "").rstrip(".")
    whole, dot, rest = n.partition(".")
    return whole if dot and rest.strip("0") == "" else n


def added(answer: str, first: str, second: str) -> list[str]:
    """The numbers, and the words with a capital letter or a digit in them,
    that the answer gives and neither passage holds. A capital that only
    opens a sentence names nothing, so a sentence's first word is let be:
    a name that opens one is missed. Words of the question itself (First,
    Second) are let be too."""
    both = f"{first}\n{second}"
    have_n = {_norm(n) for n in NUMBER.findall(both)}
    low = both.lower()
    out: list[str] = []
    for n in NUMBER.findall(answer):
        if _norm(n) not in have_n and _norm(n) not in out:
            out.append(_norm(n))
    starts = {m.end() for m in re.finditer(r"(?:^|[.!?:]\s+|[\"“(]\s*)", answer)}
    for m in TOKEN.finditer(answer):
        w = m.group(0).rstrip("'’-")
        w = re.sub(r"['’]s$", "", w)
        named = any(c.isupper() for c in w) or any(c.isdigit() for c in w)
        if not named or NUMBER.fullmatch(w) or w in ("First", "Second", "I"):
            continue
        if w.lower() in low:
            continue
        if m.start() in starts and w[1:].islower() and not any(c.isdigit() for c in w):
            continue  # only a sentence's capital
        if w not in out:
            out.append(w)
    return out


def _stems(text: str) -> set[str]:
    return {kernel.stem(w) for w in kernel.words(text) if w not in kernel.FUNCTION}


def drawn_from(answer: str, first: str, second: str) -> tuple[bool, bool]:
    """Whether the answer uses a word of the first passage, and of the second,
    that the other doesn't hold: a connection speaks of both ends. Words are
    read the kernel's way, without the common ones, by their plain form."""
    said, one, two = _stems(answer), _stems(first), _stems(second)
    return bool(said & (one - two)), bool(said & (two - one))


def connect(a: dict, b: dict, ask, chars: int = CHARS) -> tuple[str, list[str], str]:
    """(what the model said connects two passages, what in it neither holds,
    which passage it never speaks of: "first", "second", "either" or "")."""
    said = flat(ask(question(a["text"], b["text"], chars)))
    one, two = drawn_from(said, a["text"], b["text"])
    missed = "" if one and two else "second" if one else "first" if two else "either"
    if _stems(a["text"]) == _stems(b["text"]):
        missed = ""  # two passages that say the same have no word of their own
    return said, added(said, a["text"], b["text"]), missed


def pairs_of(text: str) -> tuple[list[tuple[str, str]], str | None]:
    out = []
    for n, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        parts = [p.strip() for p in raw.split("\t") if p.strip()]
        if len(parts) != 2:
            return [], f"line {n} isn't two places with a tab between them"
        out.append((parts[0], parts[1]))
    return out, None


def report_text(doc: dict) -> str:
    rows = [r for g in doc["groups"] for r in g["rows"]]
    w = min(max((len(r["where"]) for r in rows), default=0), 60)
    lines = [f"{doc['addon']}: {doc['state']}, {doc['said']}"]
    for g in doc["groups"]:
        lines.append(f"## {g['name']}")
        lines += [f"  {r['where']:<{w}}  {r['what']}".rstrip() for r in g["rows"]]
    return "\n".join(lines)


def main(argv: list[str], ask=None) -> int:
    """`ask` is prompt -> words, in place of the model on this machine."""
    opts: dict[str, str] = {}
    as_json = False
    it = iter(argv)
    for a in it:
        if a in ("--box", "--first", "--second", "--pairs", "--model", "--host", "--chars", "--timeout"):  # fmt: skip
            opts[a] = next(it, "")
        elif a == "--json":
            as_json = True
        else:
            print(USAGE, file=sys.stderr)
            return kernel.REFUSED
    one = "--first" in opts or "--second" in opts
    try:
        chars = int(opts.get("--chars", CHARS))
        timeout = float(opts.get("--timeout", 60))
    except ValueError:
        chars, timeout = 0, 0.0
    if (
        not opts.get("--box")
        or any(v == "" for v in opts.values())
        or one == ("--pairs" in opts)
        or (one and not ("--first" in opts and "--second" in opts))
        or not 50 <= chars <= 5000
        or not 0 < timeout < float("inf")
    ):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    pile = Path(kernel.config(box)["pile"])
    if one:
        pairs = [(opts["--first"], opts["--second"])]
    else:
        try:
            pairs, why = pairs_of(Path(opts["--pairs"]).read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            print(f"refused: {opts['--pairs']} could not be read: {type(e).__name__}", file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
        if why or not pairs:
            print(f"refused: {opts['--pairs']}: {why or 'it holds no pair'}", file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
    for x in (p for pair in pairs for p in pair):
        if place(x) is None:
            print(f"refused: {x!r} isn't a place: a file, a colon, a line", file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
    model = opts.get("--model", MODEL)
    say = sibling("say", "say")
    if ask is None:
        # about four characters a token, and room to finish a sentence
        ask = say.ollama_say(model, opts.get("--host"), timeout, most=chars // 3 + 40)
    groups, said_n, flagged, down = [], 0, 0, ""
    for x, y in pairs:
        a, b = (passage(pile, *place(p)) for p in (x, y))
        rows = [
            (p, short(c["text"]) if c else "no passage of your folder holds this line")
            for p, c in ((x, a), (y, b))
        ]
        if a is None or b is None:
            flagged += 1
            groups.append((f"{x} and {y}: not asked", rows))
            continue
        try:
            answer, extra, missed = connect(a, b, ask, chars)
        except say.SayUnreachable as e:
            down = str(e)
            break
        if not answer:
            down = f"{model} said nothing"
            break
        said_n += 1
        flagged += bool(extra or missed)
        rows.append(("said", answer))
        notes = []
        if extra:
            notes.append("in neither passage: " + ", ".join(extra))
        if missed:
            notes.append(f"it speaks of nothing that is only in the {missed} passage")
        rows.append((
            "checked",
            "; ".join(notes)
            or "every number and name it gives is in one of the two passages, and it speaks of both",
        ))  # fmt: skip
        groups.append((f"{x} and {y}, by {model}", rows))
    if down:
        doc = {"addon": NAME, "state": "unreachable", "said": down, "groups": []}
    else:
        n = len(pairs)
        line = (
            f"{n} pair{'s' * (n != 1)}: {said_n} connection{'s' * (said_n != 1)} said"
        )
        line += (
            f", {flagged} to look at"
            if flagged
            else ", every number and name in "
            + ("it is" if n == 1 else "them is")
            + " in the passages"  # fmt: skip
        )
        doc = {
            "addon": NAME,
            "state": "populated",
            "said": line,
            "groups": [
                {"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
                for g, rows in groups
            ],
        }
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))
    return kernel.ESCALATE if down or flagged else kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
