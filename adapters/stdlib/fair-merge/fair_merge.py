"""fair_merge.py: each folder ranked on its own, the lists merged in turns.
Python 3.9+.

    python adapters/stdlib/fair-merge/fair_merge.py --box DIR [--top N] "question"
    python adapters/stdlib/fair-merge/fair_merge.py --from FOLDER [--from FOLDER...] [--top N] "question"

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
(and the files loose at the top, as "."); with --from, each FOLDER given. Each
list is the kernel's `rank` of that source alone (a passage must hold half the
question's words), so the rarest words weigh most within a source and not
across them. Sources take turns in the order they are named, or by name for a
box, and a source with nothing to say says "found nothing" instead of
disappearing. The question asked back (a passage that only repeats it) is not
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
    folders, opts, args, it = [], {}, [], iter(argv)
    for a in it:
        if a == "--from":
            folders.append(next(it, ""))
        elif a in ("--box", "--top"):
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
        or bool(opts.get("--box")) == bool(folders)
        or "" in folders
        or ("--box" in opts and not opts["--box"])
    ):
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    alias: dict = {}
    if opts.get("--box"):
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
    out, more = merge(lists, int(top))
    for n, (name, c) in enumerate(out, 1):
        line = " ".join(c["text"].split())
        print(
            f"{n}. {c['path']}:{c['line']}    [{name}]    {line if len(line) <= 90 else line[:89] + '…'}"
        )
    for name, found in lists:
        if not found:
            print(f"{name}: found nothing")
        elif name in more:
            print(f"{name}: {more[name]} more that held it, not shown")
    return kernel.ALIVE if out else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
