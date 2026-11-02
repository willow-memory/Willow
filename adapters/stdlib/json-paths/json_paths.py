r"""json_paths.py: any JSON file as `key: value` lines, a record to a passage. Python 3.9+.

    python adapters/stdlib/json-paths/json_paths.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .json files, and .jsonl and .ndjson (one value per line),
hidden folders and files skipped, and writes each value flattened, a value
to a line, its key beside it, a record to a passage headed by its path:

    {"shop": "Hollow Lane", "orders": [{"id": 7, "items": [{"name": "leeks"}]}]}
    ->  shop: Hollow Lane

        orders
        id: 7
        items[0].name: leeks

Keys: a line's key is its path below its passage's heading. A key is written
after a dot, `.name`, unless it is empty or holds a space, a dot, a bracket,
a quote, a colon or a backslash; then it is written in brackets as a JSON
string, `["first name"]`, `["a.b"]`. An array's elements are `[0]`, `[1]`
and on; a JSON Lines record's heading is its line, `#12`. Values are written
as the JSON file writes them: numbers digit for digit (`1.50` stays `1.50`),
`true`, `false`, `null`, and strings without their quotes, but an empty or
blank string with them (`""`), so it is not mistaken for nothing. A string's
own lines are each a line of their own; a line longer than WIDTH characters
is wrapped at a space onto more lines. Control characters are written as
JSON escapes. A key given twice keeps both values.

A key in more than half a file's records, or more than half its passages
(three at least), is left out, in the headings too, and a line with no key
left is its value alone: written into every record, its words would make a
question pairing one of them with a word the file doesn't hold ("volcano
date") find a record that doesn't answer it. So a chat export's messages are written as their values (the
date, who, the text), and a map's keys that name their values (a file's
path, a day) stay, since each is in one record.

Passages (the kernel cuts a mirror at blank lines) are headed by their path,
and a value stays whole in one passage when it fits in kernel.MAX_CHUNK
characters. Records: each line of a JSON Lines file is one, and so is each
array or object in the first array found from the top that doesn't fit
whole (a top-level array, or `orders` in `{"orders": [...]}`, or
`data.orders`), so "what was in order 3" lands on `orders[3]` alone. Above
the records, the top is always cut: an object's plain values (strings,
numbers, true, false, null) run together, first and unheaded, and each of
its arrays and objects is its own passage, or cut by this rule when it
doesn't fit. A record too big for a passage fills passages under its
heading in the file's order, each value kept whole while it fits, and an
array or object too big for one is cut the same way. A run of lines longer
than a passage is cut between lines, never inside one, and each piece has
the same heading.

Caps: an array or object nested deeper than MAX_DEPTH levels is written as
compact JSON on its key's line; a string longer than MAX_STRING characters
is cut there and says how many characters were left out; a file over
MAX_READ bytes is not read. A mirror bigger than the kernel reads from one
file (kernel.MAX_FILE) is cut between passages into parts: `NAME.txt`, then
`NAME.part2.txt` and on; parts a shorter earlier run left behind are removed.

Skipped and counted: a file that isn't UTF-8 (with or without a BOM), isn't
JSON, is nested too deep for Python to read, or holds only an empty array or
object. In a JSON Lines file a line that isn't JSON, or holds an empty array
or object, is skipped and counted in a passage of its own at the end of its
mirror (`skipped 2: 4, 9`, the lines); a file with no line left is skipped.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

MAX_DEPTH = 32  # levels of arrays and objects written path by path
MAX_STRING = 10_000  # characters of one string kept
MAX_READ = 50_000_000  # bytes of one file read
WIDTH = 240  # characters of a value on one line before it wraps
EXTS = (".json", ".jsonl", ".ndjson")
LINES = (".jsonl", ".ndjson")
ERRORS = (OSError, UnicodeDecodeError, ValueError, RecursionError)
USAGE = "usage: json_paths.py mirror --from FOLDER --to MIRROR"

PLAIN_KEY = re.compile(r"[^\s.\[\]\"':\\\x00-\x1f\x7f]+")
# characters a line can't hold as themselves: JSON's control characters, and
# the ones Python's splitlines (which the kernel uses) would cut a line at
CONTROL = re.compile("[\x00-\x08\x0a-\x1f\x7f\x85  ]")
NEWLINE = re.compile(r"\r\n|\r|\n")


class Num(str):
    """A number as the file writes it, digit for digit."""


class Obj:
    """An object's pairs in the file's order; a key given twice keeps both."""

    def __init__(self, pairs: list[tuple[str, object]]):
        self.pairs = pairs


def loads(text: str) -> object:
    return json.loads(
        text,
        object_pairs_hook=Obj,
        parse_float=Num,
        parse_int=Num,
        parse_constant=Num,
    )


def escape(text: str) -> str:
    return CONTROL.sub(lambda m: "\\u%04x" % ord(m.group(0)), text)


def key_part(key: str) -> str:
    if PLAIN_KEY.fullmatch(key):
        return "." + escape(key)
    return "[" + escape(json.dumps(key, ensure_ascii=False)) + "]"


def children(node: object) -> list[tuple[str | int, object]]:
    if isinstance(node, Obj):
        return list(node.pairs)
    if isinstance(node, list):
        return list(enumerate(node))
    return []


def is_box(node: object) -> bool:
    return isinstance(node, (Obj, list))


def compact(node: object) -> str:
    """`node` as one line of JSON, for what lies past MAX_DEPTH."""
    if isinstance(node, Obj):
        inner = ",".join(
            json.dumps(k, ensure_ascii=False) + ":" + compact(v) for k, v in node.pairs
        )
        return "{" + inner + "}"
    if isinstance(node, list):
        return "[" + ",".join(compact(v) for v in node) + "]"
    if isinstance(node, Num):
        return str(node)
    return json.dumps(node, ensure_ascii=False)


def wrap(text: str, width: int = WIDTH) -> list[str]:
    """`text` in pieces of at most `width` characters, cut at a space when
    there is one."""
    out = []
    while len(text) > width:
        cut = text.rfind(" ", 1, width + 1)
        cut = cut if cut > 0 else width
        out.append(text[:cut].rstrip())
        text = text[cut:].lstrip()
    out.append(text)
    return [piece for piece in out if piece.strip()]


class LineNo(int):
    """A JSON Lines record's line in its file, written `#12`."""


Steps = tuple  # a value's path: keys (str), indices (int), a LineNo first
Line = tuple  # (steps, the value's text on this line)
Passage = tuple  # (the steps it is headed by, or None; its lines; its record)


def render(steps: Steps, drop: frozenset = frozenset()) -> str:
    """A path as written: `orders[3].items[0].name`, a key in brackets when it
    must be. A key in `drop` is left out."""
    out = ""
    for step in steps:
        if isinstance(step, LineNo):
            out += f"#{int(step)}"
        elif isinstance(step, int):
            out += f"[{step}]"
        elif step not in drop:
            part = key_part(step)
            out += part[1:] if not out and part.startswith(".") else part
    return out


def text_lines(steps: Steps, text: str) -> list[Line]:
    """A long or many-lined string as lines that each keep its path."""
    if not text.strip():
        return [(steps, escape(json.dumps(text, ensure_ascii=False)))]
    more = len(text) - MAX_STRING
    if more > 0:
        text = text[:MAX_STRING]
    out = []
    for piece in NEWLINE.split(text):
        out += [(steps, bit) for bit in wrap(escape(piece))]
    if more > 0:
        out[-1] = (steps, out[-1][1] + f" … ({more} more characters)")
    return out


def flat(node: object, steps: Steps, depth: int) -> list[Line]:
    """Every value under `node`, with its path."""
    if is_box(node):
        if not children(node):
            return [(steps, "{}" if isinstance(node, Obj) else "[]")]
        if depth >= MAX_DEPTH:
            return text_lines(steps, compact(node))
        out = []
        for step, child in children(node):
            out += flat(child, steps + (step,), depth + 1)
        return out
    if isinstance(node, Num):
        return [(steps, str(node))]
    if isinstance(node, str):
        return text_lines(steps, node)
    return [(steps, json.dumps(node))]


def size(head: Steps | None, lines: list[Line]) -> int:
    """At most the characters the kernel counts for a passage: each line with
    its full path, never shorter than what is written."""
    out = len(render(head)) + 1 if head else 0
    return out + sum(len(render(steps)) + len(value) + 3 for steps, value in lines)


def pack(
    head: Steps | None, units: list[list[Line]], rec: Steps | None
) -> list[Passage]:
    """`units` (each a value's lines) under `head`, in order, a passage filled
    while the next unit fits whole; a unit bigger than a passage is cut
    between its lines, and each piece has the same heading."""
    out: list[Passage] = []
    cur: list[Line] = []
    for unit in units:
        if cur and size(head, cur + unit) > kernel.MAX_CHUNK:
            out.append((head, cur, rec))
            cur = []
        for x in unit:
            if cur and size(head, cur + [x]) > kernel.MAX_CHUNK:
                out.append((head, cur, rec))
                cur = []
            cur.append(x)
    if cur:
        out.append((head, cur, rec))
    return out


def splits(node: object, depth: int) -> bool:
    """Whether `node` can be cut into the passages of its values."""
    return is_box(node) and bool(children(node)) and depth < MAX_DEPTH


def passages(
    node: object,
    steps: Steps,
    depth: int,
    outer: bool = False,
    top: bool = False,
    rec: Steps | None = None,
) -> list[Passage]:
    """`node` as passages, headed by its path: one when it fits (the top is
    always cut). Above the records (`outer`), an object's plain values run
    together and each of its arrays and objects is cut by this rule; an
    array's arrays and objects are records, a passage (or more) each. In a
    record, its values fill passages in order, each kept whole while it fits,
    and one too big for a passage is cut the same way. `rec` is the record
    a passage is part of (by default, its own heading)."""
    head = None if top else steps
    rec = head if rec is None else rec
    if not splits(node, depth):
        return pack(head, [flat(node, steps, depth)], rec)
    if not top:
        lines = flat(node, steps, depth)
        if size(steps, lines) <= kernel.MAX_CHUNK:
            return [(steps, lines, rec)]
    out: list[Passage] = []
    units: list[list[Line]] = []
    if outer:
        records = isinstance(node, list)
        for step, child in children(node):
            where = steps + (step,)
            if not splits(child, depth + 1):
                units.append(flat(child, where, depth + 1))
            elif records:
                out += passages(child, where, depth + 1, rec=where)
            else:
                out += passages(child, where, depth + 1, outer=True)
        return pack(head, units, rec) + out
    for step, child in children(node):
        where = steps + (step,)
        got = flat(child, where, depth + 1)
        if splits(child, depth + 1) and size(where, got) > kernel.MAX_CHUNK:
            out += pack(head, units, rec)
            units = []
            out += passages(child, where, depth + 1, rec=rec)
        else:
            units.append(got)
    return out + pack(head, units, rec)


def keys(p: Passage) -> set[str]:
    """The keys a passage would write: its heading's and its lines' own."""
    head, lines, _ = p
    cut = len(head) if head is not None else 0
    steps = list(head or ()) + [x for s, _ in lines for x in s[cut:]]
    return {x for x in steps if isinstance(x, str)}


def common(found: list[Passage]) -> frozenset:
    """Keys in more than half the records, or the passages, of a file (three
    at least): written there, a question pairing a word of one with a word
    the file doesn't hold would find a passage that doesn't answer it. A key
    that names its value (a file's path, a day) is in one record, and stays."""
    seen: dict[object, set[str]] = {}
    each = []
    for p in found:
        each.append(keys(p))
        seen.setdefault(p[2], set()).update(each[-1])
    out: set[str] = set()
    for groups in (list(seen.values()), each):
        count: dict[str, int] = {}
        for got in groups:
            for k in got:
                count[k] = count.get(k, 0) + 1
        out.update(k for k, n in count.items() if n >= 3 and n * 2 > len(groups))
    return frozenset(out)


def write(found: list[Passage]) -> str:
    """The passages as the mirror's text: a heading, then each line as
    `key: value` with its path below the heading. Keys in `common` are left
    out, and a line with no key left is its value alone."""
    drop = common(found)
    out = []
    for head, lines, _ in found:
        cut = len(head) if head is not None else 0
        text = [render(head, drop)] if head else []
        for steps, value in lines:
            kept = any(isinstance(x, str) and x not in drop for x in steps[cut:])
            text.append(f"{render(steps[cut:], drop)}: {value}" if kept else value)
        out.append("\n".join(x for x in text if x))
    return "\n\n".join(out) + "\n"


def convert_json(text: str) -> list[Passage] | None:
    node = loads(text)
    if is_box(node) and not children(node):
        return None
    return passages(node, (), 0, outer=True, top=True)


def convert_lines(text: str) -> tuple[list[Passage], list[int]] | None:
    out: list[Passage] = []
    bad: list[int] = []
    for n, raw in enumerate(NEWLINE.split(text), 1):
        if not raw.strip():
            continue
        try:
            node = loads(raw)
        except (ValueError, RecursionError):
            bad.append(n)
            continue
        if is_box(node) and not children(node):
            bad.append(n)
            continue
        out += passages(node, (LineNo(n),), 0, rec=(LineNo(n),))
    return (out, bad) if out else None


def convert(data: bytes, name: str = "x.json") -> str | None:
    """The mirror text of one file, or None when there is nothing to read."""
    text = data.decode("utf-8-sig")
    if not name.lower().endswith(LINES):
        found = convert_json(text)
        return write(found) if found else None
    got = convert_lines(text)
    if not got:
        return None
    found, bad = got
    out = write(found)
    if bad:  # its own passage, so no question about a record finds it
        shown = ", ".join(str(n) for n in bad[:20]) + (", …" if len(bad) > 20 else "")
        out += f"\nskipped {len(bad)}: {shown}\n"
    return out


def parts(text: str, limit: int = kernel.MAX_FILE) -> list[str]:
    """`text` cut between passages into pieces of at most `limit` bytes as
    UTF-8 (a passage is far smaller than that)."""
    out: list[str] = []
    piece: list[str] = []
    used = 0
    for block in text.rstrip("\n").split("\n\n"):
        raw = len(block.encode("utf-8")) + 2
        if piece and used + raw > limit:
            out.append("\n\n".join(piece) + "\n")
            piece, used = [], 0
        piece.append(block)
        used += raw
    if piece:
        out.append("\n\n".join(piece) + "\n")
    return out


def _part_name(name: str, n: int) -> str:
    return f"{name}.txt" if n == 1 else f"{name}.part{n}.txt"


def _sources(folder: Path) -> list[Path]:
    """Files under `folder` this reads, sorted by relative path. Hidden folders
    and files are skipped; symlinked folders are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            if not name.startswith(".") and name.lower().endswith(EXTS) and p.is_file():
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped)."""
    wrote = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
        try:
            if path.stat().st_size > MAX_READ:
                skipped += 1
                continue
            text = convert(path.read_bytes(), path.name)
            if text is None:
                skipped += 1
                continue
            folder = dst.joinpath(rel.parent)
            folder.mkdir(parents=True, exist_ok=True)
            found = parts(text)
            for n, piece in enumerate(found, 1):
                (folder / _part_name(rel.name, n)).write_bytes(piece.encode("utf-8"))
            n = len(found) + 1
            while (folder / _part_name(rel.name, n)).is_file():
                (folder / _part_name(rel.name, n)).unlink()
                n += 1
        except ERRORS:
            skipped += 1
            continue
        wrote += 1
    return wrote, skipped


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2])) if argv[:1] == ["mirror"] else {}
    if len(argv) != 5 or sorted(opts) != ["--from", "--to"]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    if not Path(opts["--from"]).is_dir():
        print(f"refused: not a folder: {opts['--from']}", file=sys.stderr)
        return kernel.REFUSED
    src = Path(opts["--from"]).resolve()
    dst = Path(opts["--to"]).resolve()
    if _within(dst, src) or _within(src, dst):
        print(
            "refused: MIRROR and FOLDER must not be inside one another", file=sys.stderr
        )
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
