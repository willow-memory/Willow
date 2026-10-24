"""diverge.py: where two copies of a folder or a box part. Python 3.9+.

    python adapters/stdlib/diverge/diverge.py A B

A and B are each a folder or a .zip (a backup's, say). It narrows level by
level, stopping at the first difference it can name:

    record   when both hold a record.jsonl: the rows they share, then the
             first row where they part, or which one runs on past the other
    files    the files only one of them holds, and the files both hold
             that differ
    line     in the first file that differs, the first line that does

    records: the same for 41 rows, then part at row 41
    only in A:  written/dentist.md
    differ:     notes/todo.txt (first at line 3)
      A: Call the bank
      B: Call the bank on Monday

A key is never read. Files under a hidden folder are left out, as the kernel
leaves them out, and so is any file a box's kernel.json names as its key, if
it sits inside what's compared. The lines shown are your own files', on your
own screen; nothing is written. The idea is willow-bot's `diverge`, which
finds where two branches or two boxes' chains part.

Exit codes, the kernel's: 0 the same; 42 they differ; 2 refused.
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402


def load(where: Path) -> dict[str, bytes]:
    """{relative path: bytes} of a folder or a zip, less hidden folders and
    any key a kernel.json in it names."""
    if zipfile.is_zipfile(where):  # a folder isn't one
        with zipfile.ZipFile(where) as z:
            got = {n: z.read(n) for n in z.namelist() if not n.endswith("/")}
        keys: set[str] = set()
    else:
        got, keys = {}, set()
        for p in sorted(where.rglob("*")):
            rel = p.relative_to(where)
            if any(part.startswith(".") for part in rel.parts) or not p.is_file():
                continue
            if p.name == "kernel.json":
                try:
                    keys.add(str(Path(json.loads(p.read_text())["key"]).resolve()))
                except (OSError, ValueError, KeyError, TypeError):
                    pass
        for p in sorted(where.rglob("*")):
            rel = p.relative_to(where)
            if any(part.startswith(".") for part in rel.parts) or not p.is_file():
                continue
            if str(p.resolve()) in keys:
                continue  # never read a key
            got[rel.as_posix()] = p.read_bytes()
    return {
        k: v for k, v in got.items() if not any(s.startswith(".") for s in k.split("/"))
    }


def chains(a: bytes, b: bytes) -> str:
    """Where two records part, row by row: each row compared whole, so a row
    edited under an unchanged `hash` field still parts them."""
    ha = [x for x in a.decode("utf-8", "replace").splitlines() if x.strip()]
    hb = [x for x in b.decode("utf-8", "replace").splitlines() if x.strip()]
    same = 0
    while same < min(len(ha), len(hb)) and ha[same] == hb[same]:
        same += 1
    if len(ha) == len(hb) == same:
        return f"records: the same, {same} rows"
    if same == min(len(ha), len(hb)):
        longer, extra = (
            ("A", len(ha) - same) if len(ha) > len(hb) else ("B", len(hb) - same)
        )
        return f"records: the same for {same} rows, then {longer} runs on {extra} more"
    return f"records: the same for {same} rows, then part at row {same}"


def first_line(a: bytes, b: bytes) -> tuple[int, str, str] | None:
    """(line number, A's line, B's line) where two texts first differ, or
    None when either isn't text."""
    try:
        la, lb = a.decode("utf-8").splitlines(), b.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return None
    for i in range(max(len(la), len(lb))):
        x = la[i] if i < len(la) else "(the file ends)"
        y = lb[i] if i < len(lb) else "(the file ends)"
        if x != y:
            return i + 1, x, y
    return None  # the same lines, differing only in a final newline


def compare(a: dict[str, bytes], b: dict[str, bytes]) -> list[str]:
    """The lines that say where A and B part; empty when they're the same."""
    out = []
    if (
        "record.jsonl" in a
        and "record.jsonl" in b
        and a["record.jsonl"] != b["record.jsonl"]
    ):
        out.append(chains(a["record.jsonl"], b["record.jsonl"]))
    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    differ = sorted(k for k in set(a) & set(b) if a[k] != b[k] and k != "record.jsonl")
    out += [f"only in A:  {k}" for k in only_a] + [f"only in B:  {k}" for k in only_b]
    for i, k in enumerate(differ):
        where = first_line(a[k], b[k]) if i == 0 else None
        if where is None:
            out.append(f"differ:     {k}")
            continue
        n, x, y = where
        out += [
            f"differ:     {k} (first at line {n})",
            f"  A: {x[:120]}",
            f"  B: {y[:120]}",
        ]
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 2 or any(a.startswith("--") for a in argv):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    a, b = (Path(x) for x in argv)
    for p in (a, b):
        if not (p.is_dir() or (p.is_file() and zipfile.is_zipfile(p))):
            print(f"refused: {p} is neither a folder nor a zip", file=sys.stderr)
            return kernel.REFUSED
    said = compare(load(a), load(b))
    if not said:
        print("The same: every file, byte for byte.")
        return kernel.ALIVE
    print("\n".join(said))
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
