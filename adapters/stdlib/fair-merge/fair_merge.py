"""fair_merge.py: each folder ranked on its own, the lists merged in turns.
Python 3.9+.

    python adapters/stdlib/fair-merge/fair_merge.py --box DIR [--top N] "question"
    python adapters/stdlib/fair-merge/fair_merge.py --from FOLDER [--from FOLDER...] [--top N] "question"
    python adapters/stdlib/fair-merge/fair_merge.py --index INDEX [--index INDEX...] [--words FILE] [--top N] "question"

One ranked list over a big pile lets a large corpus push a small one out on
volume alone: a thousand log lines hold "frost" more often than the one
gardening note that answers. Here every source is ranked by the kernel on its
own, and the lists are dealt out in turns, first of each, then second of each:

    1. notes/garden.md:3    [notes]    Frost is due the first week of November.
    2. logs/syslog:40       [logs]     frost-check cron ran at 03:00
    3. notes/diary.md:9     [notes]    The frost took the beans.
    logs: 1 more that held it, not shown
    archive: found nothing

A source is a folder: with --box, each folder at the top of the box's pile
(and the files loose at the top, as "."); with --from, each FOLDER given; with
--index, each INDEX the scan add-on made of a folder, read one at a time and
only where the question's words are, so a pile too big to read whole can be
one. --words FILE is a words list for the indexes, as scan takes one. Each
list is the kernel's `rank` of that source alone (a passage must hold half the
question's words), so the rarest words weigh most within a source and not
across them. Sources take turns in the order they are named, or by name for a
box, and a source with nothing to say says "found nothing" instead of
disappearing. A source that is an index says more: the words of the question
none of its passages hold, whether or not it found something. Half the words
is enough to be shown, so a passage can answer and still lack the subject:

    recipes: found nothing; no passage holds: frost
    logs: 1 more that held it, not shown; no passage holds: violin

A passage two sources hold word for word is one passage: it is shown once,
at the first source's place, with every source that holds it, `[notes, old]`.
The question asked back (a passage that only repeats it) is not
an answer and is left out. --top N shows N passages (6 unless said).

It asks without asking: nothing is written, not even a record row.

Exit codes, the kernel's: 0 at least one passage; 42 none held it; 2 refused.
"""

from __future__ import annotations

import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

TOP = 6


def scan_addon():
    """The scan add-on's module, from its source beside this one."""
    sys.path.insert(0, str(STDLIB / "scan"))
    import scan

    return scan


def from_index(at: Path, question: str, alias: dict) -> tuple[list[dict], list[str]]:
    """(an index's passages that answer, best first; the question's words no
    passage of it holds, each held the way the kernel holds a word)."""
    ix = scan_addon().Index(at)
    found = [
        c
        for c in ix.rank(question, alias, kernel.TOP)
        if not kernel.echo(question, c["text"])
    ]
    want = [
        w for w in dict.fromkeys(kernel.words(question)) if w not in kernel.FUNCTION
    ]
    return found, [w for w in want if not ix.near(w, alias)]


def joined(
    lists: list[tuple[str, list[dict]]],
) -> tuple[list[tuple[str, list[dict]]], dict[str, list[str]]]:
    """(the lists with a passage an earlier source also found left out of the
    later one, {a passage's id: every source that found it, in order})."""
    held: dict[str, list[str]] = {}
    out = []
    for name, found in lists:
        mine = []
        for c in found:
            if c["id"] not in held:
                mine.append(c)
            held.setdefault(c["id"], []).append(name)
        out.append((name, mine))
    return out, held


def sources_of_pile(pile: Path) -> list[tuple[str, Path | None]]:
    """(name, folder) for each folder at the top of the pile, by name, and
    "." for the files loose at the top (None: those files only)."""
    out: list[tuple[str, Path | None]] = []
    if any(p.is_file() and not p.name.startswith(".") for p in pile.iterdir()):
        out.append((".", None))
    out += [
        (p.name, p)
        for p in sorted(pile.iterdir())
        if p.is_dir() and not p.name.startswith(".")
    ]
    return out


def ranked(pile_chunks: list[dict], question: str, alias: dict) -> list[dict]:
    """A source's passages that answer, best first: the question asked back is not one."""
    return [
        c
        for c in kernel.rank(pile_chunks, question, alias, top=kernel.TOP)
        if not kernel.echo(question, c["text"])
    ]


def merge(
    lists: list[tuple[str, list[dict]]], top: int
) -> tuple[list[tuple[str, dict]], dict[str, int]]:
    """([(source, passage)] dealt in turns, how many more each source held)."""
    out: list[tuple[str, dict]] = []
    depth = max((len(c) for _, c in lists), default=0)
    for level in range(depth):
        for name, found in lists:
            if level < len(found) and len(out) < top:
                out.append((name, found[level]))
    shown = {name: 0 for name, _ in lists}
    for name, _ in out:
        shown[name] += 1
    return out, {
        name: len(found) - shown[name]
        for name, found in lists
        if len(found) > shown[name]
    }


def main(argv: list[str]) -> int:
    folders, indexes, opts, args, it = [], [], {}, [], iter(argv)
    for a in it:
        if a == "--from":
            folders.append(next(it, ""))
        elif a == "--index":
            indexes.append(next(it, ""))
        elif a in ("--box", "--top", "--words"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    top = opts.get("--top", str(TOP))
    ok = (
        len(args) == 1
        and not args[0].startswith("--")
        and top.isdigit()
        and int(top) > 0
    )
    if (
        not ok
        or (bool(opts.get("--box")) + bool(folders) + bool(indexes)) != 1
        or "" in folders + indexes
        or ("--box" in opts and not opts["--box"])
        or ("--words" in opts and (not indexes or not opts["--words"]))
    ):
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    alias: dict = {}
    absent: dict[str, list[str]] = {}
    if indexes:
        names = [Path(i).resolve().name for i in indexes]
        if len(set(names)) != len(names):
            print("refused: two indexes have the same folder name", file=sys.stderr)
            return kernel.REFUSED
        lists = []
        try:
            if "--words" in opts:
                alias, why = kernel.parse_words(
                    Path(opts["--words"]).read_text(encoding="utf-8")
                )
                if why:
                    raise ValueError(why)
            for name, i in zip(names, indexes):  # one whole index in memory at a time
                found, absent[name] = from_index(Path(i), args[0], alias)
                lists.append((name, [{**c, "path": f"{name}/{c['path']}"} for c in found]))  # fmt: skip
        except (OSError, ValueError) as e:
            print(f"refused: {e}", file=sys.stderr)
            return kernel.REFUSED
    elif opts.get("--box"):
        box = Path(opts["--box"])
        if not (box / "kernel.json").exists():
            print("refused: not a kernel box; init first", file=sys.stderr)
            return kernel.REFUSED
        cfg = kernel.config(box)
        if "words" in cfg:
            alias, _, why = kernel.read_words(Path(cfg["words"]), box)
            if why is not None:
                print(f"refused: {why}", file=sys.stderr)
                return kernel.REFUSED
        pile = Path(cfg["pile"])
        everything = kernel.chunks(pile)
        lists = []
        for name, folder in sources_of_pile(pile):
            mine = [
                c
                for c in everything
                if (c["path"].split("/")[0] == name if folder else "/" not in c["path"])
            ]
            lists.append((name, ranked(mine, args[0], alias or {})))
    else:
        lists = []
        for f in folders:
            if not Path(f).is_dir():
                print(f"refused: {f} isn't a folder", file=sys.stderr)
                return kernel.REFUSED
            name = Path(f).resolve().name
            tag = name if name not in [n for n, _ in lists] else f
            lists.append(
                (
                    tag,
                    [
                        {**c, "path": f"{tag}/{c['path']}"}
                        for c in ranked(kernel.chunks(Path(f)), args[0], {})
                    ],
                )
            )
    found_by = {name: bool(found) for name, found in lists}
    lists, held = joined(lists)
    out, more = merge(lists, int(top))
    for n, (_, c) in enumerate(out, 1):
        line = " ".join(c["text"].split())
        print(
            f"{n}. {c['path']}:{c['line']}    [{', '.join(held[c['id']])}]    {line if len(line) <= 90 else line[:89] + '…'}"
        )
    for name, _ in lists:
        said = []
        if not found_by[name]:
            said.append("found nothing")
        elif name in more:
            said.append(f"{more[name]} more that held it, not shown")
        if absent.get(name):
            said.append(f"no passage holds: {', '.join(absent[name])}")
        if said:
            print(f"{name}: {'; '.join(said)}")
    return kernel.ALIVE if out else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
