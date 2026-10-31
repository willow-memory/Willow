"""fixity.py: your folder's files hashed again now and then. Python 3.9+.

    python adapters/stdlib/fixity/fixity.py --box DIR [--now TS]

Each file of your folder (not in a hidden folder) is hashed, and the check
goes on the record as one `fixity` row, through the kernel's own `append`:
paths, SHA-256, size and mtime, never what a file says.

    the first check   every file hashed
    each later one    the same files again, compared with the last check

A hash that changed with a newer mtime is an edit of yours. A hash that
changed with the same or an older mtime is rot: the bytes moved and no
edit did. `changed` says what is new or gone; this one says which of those
edits never happened.

    Fixity needs you:
      rot      care/log.txt
      edited   notes.txt
      gone     old/scan.pdf
      new      letters/bank.txt

Exit codes, the kernel's: 0 the first check, or every file matches; 42
something changed; 2 refused (a record that doesn't verify).
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KIND = "fixity"


def fingerprints(pile: Path) -> dict[str, dict]:
    """{path: {hash, size, mtime}} for every file not under a hidden folder."""
    out = {}
    for p in sorted(pile.rglob("*")):
        rel = p.relative_to(pile)
        if not p.is_file() or any(part.startswith(".") for part in rel.parts):
            continue
        h = hashlib.sha256()
        try:
            with p.open("rb") as f:
                for block in iter(lambda: f.read(1 << 20), b""):
                    h.update(block)
            st = p.stat()
        except OSError:
            continue
        out[rel.as_posix()] = {
            "hash": h.hexdigest(),
            "size": st.st_size,
            "mtime": st.st_mtime_ns,
        }
    return out


def last_files(rows: list[dict]) -> tuple[dict[str, dict] | None, str]:
    """The folder as the last fixity check left it, and when that was."""
    state, when = None, ""
    for r in rows:
        if r["kind"] != KIND:
            continue
        state = dict(r.get("files") or {})
        when = str(r.get("ts", ""))
    return state, when


def diff(before: dict[str, dict], now: dict[str, dict]) -> dict[str, list[str]]:
    """rot / edited / gone / new, each a sorted list of paths."""
    rot, edited, gone, new = [], [], [], []
    for path, was in before.items():
        got = now.get(path)
        if got is None:
            gone.append(path)
            continue
        if got.get("hash") == was.get("hash"):
            continue
        if int(got.get("mtime") or 0) > int(was.get("mtime") or 0):
            edited.append(path)
        else:
            rot.append(path)
    for path in now:
        if path not in before:
            new.append(path)
    return {
        "rot": sorted(rot),
        "edited": sorted(edited),
        "gone": sorted(gone),
        "new": sorted(new),
    }


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
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
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print(
            "refused: the record doesn't verify:", *breaks, sep="\n  ", file=sys.stderr
        )
        return kernel.REFUSED
    ts = opts.get("--now") or kernel.now()
    now = fingerprints(Path(kernel.config(box)["pile"]))
    before, when = last_files(rows)
    kernel.append(box, ts, KIND, who=KIND, files=now)
    if before is None:
        print(
            f"First fixity check: {len(now)} file"
            f"{'' if len(now) == 1 else 's'} hashed. "
            "The next check says which changed without an edit."
        )
        return kernel.ALIVE
    d = diff(before, now)
    stamp = f"{when[:10]} {when[11:16]}".strip()
    if not any(d.values()):
        print(f"Fixity holds: {len(now)} files match the last check ({stamp}).")
        return kernel.ALIVE
    print("Fixity needs you:")
    for label in ("rot", "edited", "gone", "new"):
        for path in d[label]:
            print(f"  {label:<8} {path}")
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
