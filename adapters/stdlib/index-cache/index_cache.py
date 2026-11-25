"""index_cache.py: keep a folder's scan index between runs, rebuilt only when
the folder changed. Python 3.9+.

    python adapters/stdlib/index-cache/index_cache.py --from FOLDER --to INDEX
    python adapters/stdlib/index-cache/index_cache.py --from @LIST --to INDEX

`scan index` reads the whole folder to build an index; on a big folder that is
the slow step. But a folder usually hasn't changed since last time, and then
the index already on disk is still the right one. This keeps a small manifest
beside the index -- each read file's path and the SHA-256 of its text -- and on
each run hashes the folder's files and compares:

- **unchanged** -- every file the index was built from is still there with the
  same hash, and no new file was added: the index is current, so nothing is
  rebuilt and no passage is re-read. Ask it with `scan`.
- **changed** -- a file was added, edited or removed: it rebuilds the index
  (through `scan`), writes the new manifest, and says what moved.

So the index is kept between runs and a question doesn't re-read the folder
unless the folder changed. The files it hashes are exactly the ones the kernel
would read into the index (text, UTF-8, not hidden, under the size cap); a
binary or a dotfile changing never forces a rebuild.

`--from @LIST` keeps the index of a list's files where they are kept, as a
box laid with `kernel.py init --from NAME=@LIST` reads them (CONST-VI-9):
one path a line, each named by its path from the folder the files share,
the kernel's own `list_chunks`. A listed file that is gone is read as
nothing, as a deleted one is, and counts as removed.

It reads the folder and writes only under `--to` (the index and its manifest);
it writes no box, reads no key, and reaches no network. An index made by
another kernel.py is rebuilt, since its passages were the other kernel's. Exit
codes, the kernel's: 0 the index is current or was rebuilt; 42 the folder has
nothing to read; 2 refused (a bad command line, or a `--from` that is not a
folder, or a `--from @LIST` that is not a list of files).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "batch-ask"))
import kernel  # noqa: E402
import scan  # noqa: E402

FORMAT = "willow-index-cache/1"
CACHE = "cache.json"  # the manifest, beside scan's own index files


def manifest(folder: Path) -> dict[str, str]:
    """{relative path: SHA-256 of its text} for the files the kernel reads into
    an index -- the same filter as kernel.chunks, file by file, hashing the
    text so a rebuild follows exactly the changes the index would see."""
    out: dict[str, str] = {}
    for p in sorted(folder.rglob("*")):
        rel = p.relative_to(folder)
        if not p.is_file() or any(part.startswith(".") for part in rel.parts):
            continue
        try:
            raw = p.read_bytes()
            if len(raw) > kernel.MAX_FILE or b"\0" in raw[: kernel.SNIFF]:
                continue
            out[str(rel)] = kernel.h256(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
    return out


def listed_manifest(lst: Path) -> dict[str, str]:
    """`manifest` for a list's files, named as the kernel's `list_chunks`
    names them: by path from the folder the listed files share."""
    files = kernel.listed(lst)
    if not files:
        return {}
    root = Path(os.path.commonpath([str(f.parent) for f in files]))
    out: dict[str, str] = {}
    for f in files:
        rel = f.relative_to(root)
        if any(part.startswith(".") for part in rel.parts):
            continue
        try:
            raw = f.read_bytes()
            if len(raw) > kernel.MAX_FILE or b"\0" in raw[: kernel.SNIFF]:
                continue
            out[str(rel)] = kernel.h256(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
    return out


def cached(index: Path) -> dict[str, str] | None:
    """The manifest a past run wrote for `index`, or None when there is none,
    it is of another kind, it was made by another kernel.py, or the index it
    describes is not whole. Then the index is treated as stale."""
    try:
        head = json.loads((index / CACHE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if head.get("format") != FORMAT or head.get("kernel") != kernel.VERSION:
        return None
    try:
        scan.passages(index)  # the scan index is present and this kernel's
    except (ValueError, OSError):
        return None
    return head.get("files", {})


def moved(old: dict[str, str], new: dict[str, str]) -> str:
    """How the folder changed, oldest manifest to newest, in one line."""
    added = len(set(new) - set(old))
    removed = len(set(old) - set(new))
    changed = sum(1 for p in set(old) & set(new) if old[p] != new[p])
    return f"+{added} new, ~{changed} changed, -{removed} removed"


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    it = iter(argv)
    for a in it:
        if a in ("--from", "--to"):
            opts[a] = next(it, "")
        else:
            opts["bad"] = a
    if opts.get("bad") or "--from" not in opts or "--to" not in opts:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    given, index = opts["--from"], Path(opts["--to"]).resolve()
    lst = Path(given[1:]).resolve() if given.startswith("@") else None
    if lst is not None:
        if not lst.is_file():
            print(f"refused: {given[1:]} is not a list of files", file=sys.stderr)
            return kernel.REFUSED
        files = kernel.listed(lst)
        # only the listed files are read, so an index beside them is fine;
        # one that would hold the list, or a listed file, is not
        held = any(p.is_relative_to(index) for p in [lst, *files])
    else:
        folder = Path(given).resolve()
        if not folder.is_dir():
            print(f"refused: {given} is not a folder", file=sys.stderr)
            return kernel.REFUSED
        held = index.is_relative_to(folder) or folder.is_relative_to(index)
    if held:
        print("refused: the index and what it reads can't hold each other",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    if not index.parent.is_dir():
        print(f"refused: {index.parent} is not a folder; make it first",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED

    now = manifest(folder) if lst is None else listed_manifest(lst)
    before = cached(index)
    if before is not None and before == now:
        print(f"current: {len(now)} files unchanged; the index at {opts['--to']} "
              f"still answers. Ask it with scan.")  # fmt: skip
        return kernel.ALIVE

    n = (
        scan.build(folder, index)
        if lst is None
        else scan.build_from(kernel.list_chunks(lst), index)
    )
    (index / CACHE).write_text(
        kernel.canon({"format": FORMAT, "kernel": kernel.VERSION, "files": now}) + "\n",
        encoding="utf-8",
    )
    how = moved(before, now) if before is not None else f"+{len(now)} new"
    print(f"rebuilt {n} passage{'' if n == 1 else 's'} to {opts['--to']} ({how})")
    return kernel.ALIVE if n else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
