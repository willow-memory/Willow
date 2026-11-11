"""pieces.py: your folder's passages a folder at a time, the same as the
kernel reads them, so a big folder is never held in memory all at once.
Python 3.9+.

    python adapters/stdlib/pieces/pieces.py --box DIR

`kernel.chunks(pile)` reads every file under the pile into one list. On a
pile of a few gigabytes that list is more than the machine's memory. This
hands out the same passages, in the same order and with the same paths, one
folder's own files at a time: each folder's files are read by
`kernel.chunks` itself, through a scratch folder of links to just those
files, so a passage is cut exactly as the kernel cuts it, and the next
folder is read only when the last one is done with.

    folders(pile)       each folder's passages, a list at a time
    passages(pile)      the same, one passage at a time
    of_file(pile, rel)  one file's passages, and nothing else read

The command line reads the box's pile that way and says how much it held,
and the most passages it held at once:

    pieces: 218714 passages from 4130 files in 640 pieces; at most 9120 at once (read/mail)

It writes nothing but its scratch links, and never the box or the key.
Exit codes: 0 read; 2 refused (not a box, a bad command line).
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

NAME = "pieces"


def _follows_links() -> bool:
    """Whether the kernel's reader goes into a folder that is a link, on
    this Python (its rglob did before 3.13 on some, and doesn't since)."""
    with tempfile.TemporaryDirectory() as t:
        real, pile = Path(t, "real"), Path(t, "pile")
        real.mkdir()
        pile.mkdir()
        (real / "a.txt").write_text("a\n", encoding="utf-8")
        try:
            (pile / "in").symlink_to(real, target_is_directory=True)
        except OSError:
            return False  # no links here: nothing to follow
        return bool(kernel.chunks(pile))


FOLLOWS = _follows_links()


def _read(files: list[Path], rel: Path) -> list[dict]:
    """These files' passages as the kernel reads them, each path under rel."""
    if not files:
        return []
    with tempfile.TemporaryDirectory() as t:
        for f in files:
            os.symlink(f, Path(t, f.name))
        got = kernel.chunks(Path(t))
    if rel.parts:
        for c in got:
            c["path"] = str(rel / c["path"])
    return got


def _walk(pile: Path, rel: Path):
    try:
        entries = sorted(Path(pile, rel).iterdir(), key=lambda p: p.name)
    except OSError:
        return
    files: list[Path] = []
    for p in entries:
        if p.name.startswith("."):
            continue  # the kernel leaves out anything under a hidden name
        if p.is_dir():
            if p.is_symlink() and not FOLLOWS:
                continue
            if files:  # a folder's files before it, in the kernel's order
                yield _read(files, rel)
                files = []
            yield from _walk(pile, rel / p.name)
        elif p.is_file():
            files.append(p)
    if files:
        yield _read(files, rel)


def folders(pile: Path):
    """kernel.chunks(pile), a folder's own files at a time: each a list, in
    the kernel's order, its paths under the pile. None is empty."""
    for got in _walk(Path(pile), Path()):
        if got:
            yield got


def passages(pile: Path):
    """kernel.chunks(pile), one passage at a time."""
    for got in folders(pile):
        yield from got


def of_file(pile: Path, rel: str) -> list[dict]:
    """The passages of the one file at rel under the pile, and nothing else
    read; [] for a file that isn't there or that the kernel leaves out."""
    r = Path(rel)
    if r.is_absolute() or ".." in r.parts or any(x.startswith(".") for x in r.parts):
        return []
    f = Path(pile, r)
    if not f.is_file():
        return []
    for part in list(r.parents)[:-1]:  # a linked folder the kernel wouldn't enter
        if Path(pile, part).is_symlink() and not FOLLOWS:
            return []
    return _read([f], r.parent)


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a == "--box":
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or args:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    n, files, most, where, k = 0, set(), 0, "", 0
    for got in folders(Path(kernel.config(box)["pile"])):
        k += 1
        n += len(got)
        files.update(c["path"] for c in got)
        if len(got) > most:
            most, where = len(got), str(Path(got[0]["path"]).parent)
    if not n:
        print(f"{NAME}: nothing in the pile the kernel reads")
        return kernel.ALIVE
    print(f"{NAME}: {n} passages from {len(files)} files in {k} pieces; "
          f"at most {most} at once ({where})")  # fmt: skip
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
