"""launcher.py: ask your folder from a launcher, answers with file and line.
Python 3.9+.

    python adapters/stdlib/launcher/launcher.py --box DIR [--format alfred|lines] [--limit N] "your question"

A launcher (Alfred, Raycast) runs a command each time you type and shows what it
prints. This prints the passages your folder holds for the question, ranked the
kernel's way, as the JSON that Alfred's Script Filter reads (Raycast reads
Alfred's workflows too):

    {"items": [{"uid": "...", "title": "Tomatoes want six hours of sun.",
                "subtitle": "notes/garden.md:3", "arg": "/home/ana/notes/garden.md",
                "quicklookurl": "file:///home/ana/notes/garden.md",
                "text": {"copy": "Tomatoes want six hours of sun.", "largetype": "..."},
                "variables": {"line": "3", "path": "notes/garden.md"}}]}

The title is the passage's first line, the subtitle its file and line, and
`arg` the file's full path, which is what "open file" acts on; the line is
passed as the workflow variable `line` for an editor that can go to it. Copying
the item puts the whole passage on the clipboard. With `--format lines` each
passage is one line of tab-separated title, subtitle and path, for a launcher
whose plugin runs a command and shows lines (KRunner's and PowerToys Run's
command plugins can be pointed at it; neither is wired here). `--limit` is how
many passages are shown (10 unless said, 1 to 50).

With no question the launcher is told to type one (an item that does nothing);
with none found, that nothing holds it. A question's words are looked up in the
box's words list when it has one, as the kernel's own bite does. Asking this way
writes nothing, not even a record row, reads no key, and opens, serves and sends
nothing: it prints.

Exit codes, the kernel's: 0 printed (even "type a question"); 42 `lines`
format only, when nothing holds the question; 2 refused (a bad command line, not
a box, a words list that doesn't read).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

TITLE = 100  # characters of a passage's first line shown


def short(text: str, n: int = TITLE) -> str:
    one = " ".join(text.split())
    return one if len(one) <= n else one[: n - 1] + "…"


def item(passage: dict, pile_dir: Path) -> dict:
    first = next(
        (x for x in passage["text"].splitlines() if x.strip()), passage["text"]
    )
    full = (pile_dir / passage["path"]).resolve()
    whole = " ".join(passage["text"].split())
    return {
        "uid": passage["id"],
        "title": short(first),
        "subtitle": f"{passage['path']}:{passage['line']}",
        "arg": str(full),
        "quicklookurl": full.as_uri(),
        "text": {"copy": whole, "largetype": whole},
        "variables": {"line": str(passage["line"]), "path": passage["path"]},
    }


def waiting(title: str, subtitle: str) -> dict:
    return {"title": title, "subtitle": subtitle, "valid": False}


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--format", "--limit"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    fmt, limit = opts.get("--format", "alfred"), opts.get("--limit", "10")
    if (
        not opts.get("--box")
        or len(args) > 1
        or (args and args[0].startswith("--"))
        or fmt not in ("alfred", "lines")
        or not limit.isdigit()
        or not 1 <= int(limit) <= 50
    ):
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    question = args[0].strip() if args else ""
    found: list[dict] = []
    pile_dir = Path(kernel.config(box)["pile"])
    if question:
        cfg = kernel.config(box)
        alias: dict = {}
        if "words" in cfg:
            alias, _, why = kernel.read_words(Path(cfg["words"]), box)
            if why is not None:
                print(f"refused: {why}", file=sys.stderr)
                return kernel.REFUSED
        found = kernel.rank(kernel.chunks(pile_dir), question, alias or {})[
            : int(limit)
        ]
    if fmt == "lines":
        for p in found:
            i = item(p, pile_dir)
            print(f"{i['title']}\t{i['subtitle']}\t{i['arg']}")
        return kernel.ALIVE if found else kernel.ESCALATE
    if found:
        items = [item(p, pile_dir) for p in found]
    elif question:
        items = [
            waiting(
                "No passage holds that", "your files don't say, so nothing is guessed"
            )
        ]
    else:
        items = [
            waiting(
                "Type a question", "the passages your folder holds for it appear here"
            )
        ]
    print(json.dumps({"items": items}, ensure_ascii=False))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
