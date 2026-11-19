"""removed.py: a file you are about to delete or archive, written on the record first. Python 3.9+.

    python adapters/stdlib/removed/removed.py --box DIR --root DIR [--how deleted|archived] [--to ARCHIVE] [--what TEXT] [--now TS] NAME [NAME ...]

Each NAME is a file inside --root. It is fingerprinted by the SHA-256 of
its bytes, and one `removed` row goes on the record through the kernel's
own `append`: every name, its size and its fingerprint, how they went, and
the archive they went into when there is one (its file name and its own
SHA-256). Never what a file says, and no path of your machine: a name is
written as it was given, under --root.

It only reads and records. Taking the files away is yours, after it: run
it first, while they are still there to fingerprint.

Exit codes, the kernel's: 0 the row is written; 2 refused.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KIND = "removed"
HOW = ("deleted", "archived")
WHAT = 80  # characters of the person's own word for what these were


def fingerprint(p: Path) -> tuple[str, int]:
    """(SHA-256, size in bytes), read a mebibyte at a time."""
    h, size = hashlib.sha256(), 0
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
            size += len(block)
    return h.hexdigest(), size


def refuse(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def main(argv: list[str]) -> int:
    opts, names, stray, it = {}, [], False, iter(argv)
    for a in it:
        if a in ("--box", "--root", "--how", "--to", "--what", "--now"):
            opts[a] = next(it, "")
        elif a.startswith("--"):  # an option this doesn't have, never a file's name
            stray = True
        else:
            names.append(a)
    how = opts.get("--how", "deleted")
    if (
        stray
        or not opts.get("--box")
        or not opts.get("--root")
        or not names
        or how not in HOW
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box, root = Path(opts["--box"]), Path(opts["--root"])
    if not (box / "kernel.json").exists():
        return refuse("not a kernel box; init first")
    if not root.is_dir():
        return refuse(f"{root} is not a folder")
    if root.resolve().is_relative_to(box.resolve()):
        return refuse(
            "--root is the box or inside it; the box's own files are never named"
        )
    if len(set(names)) != len(names):
        return refuse("a name given twice")
    what = opts.get("--what", "")
    if len(what) > WHAT or "\n" in what:
        return refuse(f"--what is one line of at most {WHAT} characters")
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print(
            "refused: the record doesn't verify:", *breaks, sep="\n  ", file=sys.stderr
        )
        return kernel.REFUSED
    files = {}
    for name in names:
        p = root / name
        inside = p.resolve().is_relative_to(root.resolve())
        if not inside or p.is_symlink() or not p.is_file() or Path(name).is_absolute():
            return refuse(f"{name} is not a file inside --root")
        try:
            sha, size = fingerprint(p)
        except OSError as e:
            return refuse(f"could not read {name}: {type(e).__name__}")
        files[Path(name).as_posix()] = {"sha256": sha, "size": size}
    to = None
    if opts.get("--to"):
        archive = Path(opts["--to"])
        try:
            sha, size = fingerprint(archive)
        except OSError as e:
            return refuse(f"could not read the archive {archive}: {type(e).__name__}")
        to = {"name": archive.name, "sha256": sha, "size": size}
    ts = opts.get("--now") or kernel.now()
    row = kernel.append(box, ts, KIND, who=KIND, how=how, files=files, to=to, what=what)
    for name, f in files.items():
        print(f"removed  {name}  {f['size']} bytes  {f['sha256'][:12]}…")
    said = f"{len(files)} file{'s' if len(files) != 1 else ''}, {how}"
    print(f"row {row['n']}: {said}" + (f" to {to['name']}" if to else ""))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
