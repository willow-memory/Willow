"""three_two_one.py: how many verified copies of your record exist. Python 3.9+.

    python adapters/stdlib/three-two-one/three_two_one.py --box DIR \\
        [--copy KIND:PATH ...]

The box is the first copy, kind `disk`. Each `--copy` names another: a
folder that is a box, or a zip `backup` wrote. A copy counts when its
record's chain holds, read by the kernel. Kinds of storage are the words
you give (`disk`, `usb`, `away`); `away`, `offsite` and `remote` count as
the one away from home.

Held to three copies, on two kinds of storage, one away from home.

    3-2-1 holds: 3 copies on 2 kinds of storage, one away from home
      disk  the box                         holds (4 rows)
      usb   willow-backup-20261024-093000.zip holds (4 rows)
      away  box                             holds (4 rows)

A copy that isn't a box, or whose chain doesn't hold, is said and not
counted. Exit codes, the kernel's: 0 the rule holds; 42 it doesn't, or a
copy failed; 2 refused (the box isn't one, or a bad command line).
"""

from __future__ import annotations

import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

AWAY = frozenset({"away", "offsite", "remote"})


def record_of(path: Path) -> Path | None:
    """Where this copy's record.jsonl is, or None if it isn't a box or zip."""
    if path.is_file() and zipfile.is_zipfile(path):
        return path
    if path.is_dir() and (path / "kernel.json").is_file():
        return path / "record.jsonl"
    return None


def check_folder(record: Path) -> tuple[bool, str]:
    rows, breaks = kernel.read(record)
    if breaks:
        return False, "the record doesn't verify: " + "; ".join(breaks)
    n = len(rows)
    return True, f"holds ({n} row{'' if n == 1 else 's'})"


def check_zip(path: Path) -> tuple[bool, str]:
    try:
        with zipfile.ZipFile(path) as z:
            if "record.jsonl" not in z.namelist():
                return False, "nothing there: not a willow backup"
            raw = z.read("record.jsonl")
    except (OSError, zipfile.BadZipFile) as e:
        return False, f"couldn't read it: {type(e).__name__}"
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "record.jsonl"
        copy.write_bytes(raw)
        return check_folder(copy)


def check(path: Path) -> tuple[bool, str]:
    where = record_of(path)
    if where is None:
        return False, "nothing there: not a box or a backup zip"
    if where == path:
        return check_zip(path)
    return check_folder(where)


def parse(argv: list[str]) -> tuple[dict[str, str], list[str], list[str]]:
    opts, copies, args, it = {}, [], [], iter(argv)
    for a in it:
        if a in ("--box", "--copy"):
            val = next(it, "")
            if a == "--copy":
                copies.append(val)
            else:
                opts[a] = val
        else:
            args.append(a)
    return opts, copies, args


def copies_from(box: Path, raw: list[str]) -> list[tuple[str, str, Path]] | str:
    """[(kind, label, path), ...] or a refusal."""
    out = [("disk", "the box", box)]
    for item in raw:
        if ":" not in item:
            return f"refused: --copy wants KIND:PATH, not {item!r}"
        kind, loc = item.split(":", 1)
        if not kind or not loc:
            return f"refused: --copy wants KIND:PATH, not {item!r}"
        path = Path(loc)
        out.append((kind, path.name or loc, path))
    return out


def rule(held: list[tuple[str, str, str]]) -> tuple[bool, str]:
    kinds = {k for k, _, _ in held}
    away = any(k in AWAY for k, _, _ in held)
    n, k = len(held), len(kinds)
    ok = n >= 3 and k >= 2 and away
    away_said = "one away from home" if away else "none away from home"
    verb = "holds" if ok else "needs you"
    return ok, (
        f"3-2-1 {verb}: {n} cop{'y' if n == 1 else 'ies'} on "
        f"{k} kind{'' if k == 1 else 's'} of storage, {away_said}"
    )


def main(argv: list[str]) -> int:
    opts, raw, args = parse(argv)
    if not opts.get("--box") or args:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    parsed = copies_from(box, raw)
    if isinstance(parsed, str):
        print(parsed, file=sys.stderr)
        return kernel.REFUSED
    lines, held = [], []
    for kind, label, path in parsed:
        ok, said = check(path)
        lines.append((kind, label, said))
        if ok:
            held.append((kind, label, said))
    ok, head = rule(held)
    if len(held) != len(parsed):
        ok = False
        failed = len(parsed) - len(held)
        n_kinds = len({k for k, _, _ in held})
        head = (
            f"3-2-1 needs you: {len(held)} verified cop"
            f"{'y' if len(held) == 1 else 'ies'} on "
            f"{n_kinds} kind{'' if n_kinds == 1 else 's'}; "
            f"{failed} cop{'y' if failed == 1 else 'ies'} failed"
        )
    print(head)
    width = max(len(k) for k, _, _ in lines)
    for kind, label, said in lines:
        print(f"  {kind:<{width}}  {label}  {said}")
    return kernel.ALIVE if ok else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
