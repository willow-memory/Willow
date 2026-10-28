"""pile_store.py: a folder's passages read once into one SQLite file, each
repeat stored once, and opened read-only only while it still matches the
folder, the limits and the kernel that read it. Python 3.9+.

    python adapters/stdlib/pile-store/pile_store.py --from FOLDER --to STORE [--check]

The kernel reads a folder into passages each time it is asked; the other pile
add-ons (a rank, a server, a sweep) want those passages once, kept. This keeps
them in one file:

- **current** -- the store was made from this folder, by this kernel.py, under
  the same limits, and every file it read still has the same SHA-256 with
  none added: it is left as it is.
- **built** -- otherwise the folder is read again and the store replaced
  whole, never edited in place, so a reader never meets half of one.

A text the folder holds in several places (a memo pasted every month) is
stored once and named from each place. `--check` only says which it is and
writes nothing.

From Python, `load(STORE, FOLDER)` gives the passages in the kernel's order,
each with its date, or None while the store doesn't match; `stale` says why.
It opens the store read-only.

It reads the folder and writes only `--to` (the store; while building, a
scratch file beside it made with tempfile); it writes no box, reads no key,
and reaches no network. Exit codes, the kernel's: 0 current or built; 42 the
folder has nothing to read, or with --check, the store is stale; 2 refused (a
bad command line, a `--from` that is not a folder, or a `--to` that is not a
store and would be overwritten).
"""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "index-cache"))
import index_cache  # noqa: E402
import kernel  # noqa: E402

FORMAT = "willow-pile-store/1"
MAGIC = b"SQLite format 3\0"
SCHEMA = """
CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT NOT NULL);
CREATE TABLE files (path TEXT PRIMARY KEY, sha256 TEXT NOT NULL);
CREATE TABLE texts (id TEXT PRIMARY KEY, text TEXT NOT NULL);
CREATE TABLE passages (n INTEGER PRIMARY KEY, path TEXT NOT NULL,
    line INTEGER NOT NULL, id TEXT NOT NULL REFERENCES texts, date INTEGER NOT NULL);
"""


def limits() -> dict[str, str]:
    """What the store must have been made under to be used: its kind, the
    kernel.py that read the folder, and that kernel's reading limits."""
    return {
        "format": FORMAT,
        "kernel": kernel.VERSION,
        "max_file": str(kernel.MAX_FILE),
        "max_chunk": str(kernel.MAX_CHUNK),
        "sniff": str(kernel.SNIFF),
    }


def opened(store: Path) -> sqlite3.Connection | None:
    """The store opened read-only, or None when it is no SQLite file."""
    try:
        with open(store, "rb") as f:
            if f.read(len(MAGIC)) != MAGIC:
                return None
        return sqlite3.connect(store.resolve().as_uri() + "?mode=ro", uri=True)
    except (OSError, sqlite3.Error):
        return None


def head(db: sqlite3.Connection) -> dict[str, str] | None:
    try:
        meta = dict(db.execute("SELECT k, v FROM meta"))
    except sqlite3.Error:
        return None
    return meta if meta.get("format") == FORMAT else None


def stale(store: Path, folder: Path) -> str | None:
    """Why the store can't answer for `folder` now, or None when it can."""
    db = opened(store)
    if db is None:
        return "no store yet"
    try:
        meta = head(db)
        if meta is None:
            return "not a pile store"
        if meta.get("folder") != str(folder.resolve()):
            return "made from another folder"
        for k, v in limits().items():
            if meta.get(k) != v:
                return (
                    "made with another kernel.py" if k == "kernel" else f"{k} changed"
                )
        then = dict(db.execute("SELECT path, sha256 FROM files"))
    finally:
        db.close()
    now = index_cache.manifest(folder)
    return None if then == now else index_cache.moved(then, now)


def load(store: Path, folder: Path) -> list[dict] | None:
    """The folder's passages as the kernel reads them, in its order, each with
    its date (`kernel.dates`), from the store; None while it is `stale`."""
    if stale(store, folder) is not None:
        return None
    db = opened(store)
    if db is None:
        return None
    try:
        rows = db.execute(
            "SELECT p.path, p.line, t.text, p.id, p.date FROM passages p"
            " JOIN texts t ON t.id = p.id ORDER BY p.n"
        ).fetchall()
    finally:
        db.close()
    keys = ("path", "line", "text", "id", "date")
    return [dict(zip(keys, r)) for r in rows]


def build(folder: Path, store: Path) -> tuple[int, int]:
    """Read `folder` and replace `store` with it whole; (passages, texts)."""
    files = index_cache.manifest(folder)  # first: an edit made while reading
    pile = kernel.chunks(folder)  # leaves the store stale, never wrongly current
    days = kernel.dates(pile)
    fd, tmp = tempfile.mkstemp(dir=store.parent, prefix=".pile-store-")
    os.close(fd)
    try:
        db = sqlite3.connect(tmp)
        try:
            db.executescript(SCHEMA)
            meta = {**limits(), "folder": str(folder.resolve())}
            db.executemany("INSERT INTO meta VALUES (?, ?)", sorted(meta.items()))
            db.executemany("INSERT INTO files VALUES (?, ?)", sorted(files.items()))
            db.executemany(
                "INSERT OR IGNORE INTO texts VALUES (?, ?)",
                ((c["id"], c["text"]) for c in pile),
            )
            db.executemany(
                "INSERT INTO passages VALUES (?, ?, ?, ?, ?)",
                ((n, c["path"], c["line"], c["id"], d)
                 for n, (c, d) in enumerate(zip(pile, days))),
            )  # fmt: skip
            db.commit()
        finally:
            db.close()
        os.replace(tmp, store)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    return len(pile), len({c["id"] for c in pile})


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    it = iter(argv)
    for a in it:
        if a in ("--from", "--to"):
            opts[a] = next(it, "")
        elif a == "--check":
            opts[a] = ""
        else:
            opts["bad"] = a
    if opts.get("bad") or not opts.get("--from") or not opts.get("--to"):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    folder, store = Path(opts["--from"]).resolve(), Path(opts["--to"]).resolve()
    if not folder.is_dir():
        print(f"refused: {opts['--from']} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    if store.is_relative_to(folder):
        print("refused: the store can't live inside the folder it reads",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    if not store.parent.is_dir():
        print(f"refused: {store.parent} is not a folder; make it first",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    why = stale(store, folder)
    if store.exists() and why in ("no store yet", "not a pile store"):
        print(f"refused: {opts['--to']} is there and is not a pile store; "
              "it is left as it is", file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    if why is None:
        print(f"current: the store at {opts['--to']} still matches {opts['--from']}")
        return kernel.ALIVE
    if "--check" in opts:
        print(f"stale: {why}")
        return kernel.ESCALATE
    n, texts = build(folder, store)
    print(f"built {n} passage{'' if n == 1 else 's'} ({texts} text"
          f"{'' if texts == 1 else 's'}, each stored once) to {opts['--to']} "
          f"({why})")  # fmt: skip
    return kernel.ALIVE if n else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
