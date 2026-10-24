"""timeline.py: one matter's lines from your folder, by date, every line cited.

    python adapters/stdlib/timeline/timeline.py --box DIR --to FILE "your words"

The matter is chosen by words, as a question is: "mould landlord", "knee
physio", "council tax". Every passage of your folder that holds them, by the
kernel's own rule for what holds a question (its `HOLD`, its words list, and
a folder's name counting as a word), gives every one of its lines, each with
its file and line, oldest first, written to FILE:

    2026-03-01  tenancy/log.md:3         2026-03-01 Reported the mould in the back bedroom.
    2026-03-01  tenancy/log.md:4         The landlord said someone would come.  (date from line 3)
    2026-03-09  letters/2026-03-10.md:1  2026-03-09 Wrote to the landlord about the mould.  (filed 2026-03-10)
    2026-04-02  tenancy/2026-04-02.md:1  Still no visit from the landlord; mould spreading.  (date from file name)
    undated     tenancy/misc.md:1        The landlord's number is in the blue book. Mould spray under the sink.

A line's date is the one it says (the kernel's `newest`, which never reads
11/03/2026 either way round): the one it starts with, or else the latest it
names, saying so when it names several; a line that says none takes the nearest date written above it in
its file, and says which line that was; a line with neither takes its file's name, and says so. A
line's own date and its file's are two facts: when they differ, both are
shown, and it is placed by its own. Undated lines come after the dated ones,
by file and line. Nothing is merged, shortened or reworded: a passage that
appears twice is listed twice, at both places.

It never changes your files, and writes only FILE: never inside your folder
or the box, never over a file that exists, and readable only by you.

Exit codes, the kernel's: 0 written; 42 nothing holds the words, nothing
written; 2 refused.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402


def day(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}" if d else "undated"


def held(pile: list[dict], matter: str, alias: dict) -> set[int]:
    """The passages holding the matter's words, by the kernel's rule (`rank`'s
    `HOLD` of the content words, in the text or the path), every one of them:
    no top three, and a passage repeated in two places is held in both."""
    want = set(kernel.words(matter)) - kernel.FUNCTION
    out = set()
    for i, c in enumerate(pile):
        toks = kernel.toks(c)
        if sum(kernel.held_by(w, toks, alias) for w in want) >= kernel.HOLD * len(want):
            out.add(i)
    return out


def said_of(text: str) -> tuple[str, str]:
    """(the date a line is placed at, a note when it names several). A line
    that starts with a date was written then: "2026-03-05 Hearing set for
    2026-12-01" is March. Any other line is placed at the latest it names,
    the kernel's `newest`, and says so when there is more than one."""
    ws = text.split()
    named = {d for w in ws if (d := kernel.newest(w))}
    lead = kernel.newest(ws[0]) if ws else ""
    if len(named) < 2:
        return lead or kernel.newest(text), ""
    if lead:
        return lead, "names several dates; placed at the one it starts with"
    return kernel.newest(text), "names several dates; placed at the latest"


def lines(pile: list[dict], keep: set[int]) -> list[dict]:
    """Every line of the kept passages, each with the date it says, the
    nearest date written above it in its file and where that was, and the date
    its file is named for. The nearest, not the latest the kernel's `dates`
    ranks by: after "hearing set for 2026-12-01", the next line was still
    written in March."""
    out, path, above, src = [], None, "", None
    for i, c in enumerate(pile):
        if c["path"] != path:
            path, above = c["path"], ""
        filed = kernel.newest(c["path"])
        for j, text in enumerate(c["text"].splitlines()):
            n = c["line"] + j
            said, several = said_of(text)
            if i in keep:
                out.append({"said": said, "above": above, "from": src,
                            "filed": filed, "path": c["path"], "line": n,
                            "several": several, "text": text.strip()})  # fmt: skip
            if said:
                above, src = said, n
    for r in out:
        r["when"] = r["said"] or r["above"] or r["filed"]
    # dated first, oldest first; then undated; within each, by file and line
    return sorted(out, key=lambda r: (r["when"] == "", r["when"], r["path"], r["line"]))


def show(r: dict, width: int) -> str:
    notes = []
    if r["several"]:
        notes.append(r["several"])
    if not r["said"] and r["above"]:
        notes.append(f"date from line {r['from']}")
    elif not r["said"] and r["filed"]:
        notes.append("date from file name")
    if r["filed"] and r["when"] and r["filed"] != r["when"]:
        notes.append(f"filed {day(r['filed'])}")
    tail = f"  ({'; '.join(notes)})" if notes else ""
    where = f"{r['path']}:{r['line']}"
    return f"{day(r['when']):<10}  {where:<{width}}  {r['text']}{tail}"


def page(matter: str, found: list[dict]) -> str:
    undated = sum(r["when"] == "" for r in found)
    width = max(len(f"{r['path']}:{r['line']}") for r in found)
    head = [
        f"Timeline: {matter}",
        "",
        f"{len(found)} lines, oldest first: {len(found) - undated} dated, {undated} undated.",
        "Every line of each passage in the folder that holds these words, as",
        "written, with its file and line. A line's own date and the date its",
        "file is named for are both shown when they differ.",
        "",
    ]
    return "\n".join(head + [show(r, width) for r in found]) + "\n"


def refuse(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--to"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or not opts.get("--to") or len(args) != 1:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box, to = Path(opts["--box"]), Path(opts["--to"])
    if not (box / "kernel.json").exists():
        return refuse("not a kernel box; init first")
    cfg = kernel.config(box)
    pile = Path(cfg["pile"])
    for name, root in (("your folder", pile), ("the box", box)):
        if to.resolve().is_relative_to(root.resolve()):
            return refuse(f"FILE is inside {name}; this never writes there")
    if to.exists():
        return refuse(f"{to} exists; this never overwrites")
    alias = {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            return refuse(why)
    if not set(kernel.words(args[0])) - kernel.FUNCTION:
        print(f'"{args[0]}" is only common words, held by everything; say more.')
        return kernel.ESCALATE
    chunks = kernel.chunks(pile)
    found = lines(chunks, held(chunks, args[0], alias))
    if not found:
        print(f'Nothing in your folder holds "{args[0]}". Nothing written.')
        return kernel.ESCALATE
    try:
        fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as e:
        return refuse(f"could not write {to}: {type(e).__name__}")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(page(args[0], found))
    undated = sum(r["when"] == "" for r in found)
    print(f"wrote {len(found)} lines to {opts['--to']}; {undated} undated")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
