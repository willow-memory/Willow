"""nestor.py: answers a person has checked, from a copy of Nestor's store.

    python adapters/stdlib/nestor/nestor.py mirror --from FOLDER --to MIRROR

Walks FOLDER for `.db` files that hold Nestor's `tm_pairs` table. Each pair
a person has checked (a verifier named, not a draft) becomes one paragraph:
the source, who checked it, and when. Signatures and keys are never copied.

    tomatoes want sun
    checked by: ada
    when: 2026-10-01
    status: sealed

Each store is written to MIRROR at the same relative path with `.txt`
added. A file that is not a Nestor store, or that holds no checked pair,
is skipped and counted. Hidden folders and files are skipped.

    wrote 1 files to MIRROR; skipped 0

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused.
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: nestor.py mirror --from FOLDER --to MIRROR"


def _one_line(value) -> str:
    return " ".join(str(value).split()) if value is not None else ""


def store_text(path: Path) -> str | None:
    try:
        con = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    try:
        tables = {
            r[0]
            for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if "tm_pairs" not in tables:
            return None
        cols = {r[1] for r in con.execute("PRAGMA table_info(tm_pairs)")}
        need = {"source_text", "verifier", "status", "created_at"}
        if not need <= cols:
            return None
        extra = ", target_text" if "target_text" in cols else ""
        rows = con.execute(
            "SELECT source_text, verifier, status, created_at"
            + extra
            + " FROM tm_pairs WHERE verifier != '' AND status NOT IN "
            "('draft', 'pending') ORDER BY created_at, source_text"
        ).fetchall()
    except sqlite3.Error:
        return None
    finally:
        con.close()
    if not rows:
        return None
    paras = []
    for row in rows:
        source, verifier, status, when = row[0], row[1], row[2], row[3]
        lines = [_one_line(source) or "(no source)"]
        if len(row) > 4 and _one_line(row[4]):
            lines.append(_one_line(row[4]))
        lines.append(f"checked by: {_one_line(verifier)}")
        if _one_line(when):
            lines.append(f"when: {_one_line(when)[:10]}")
        lines.append(f"status: {_one_line(status)}")
        paras.append("\n".join(lines) + "\n")
    n = len(paras)
    head = f"nestor: {n} checked pair{'s' if n != 1 else ''}\n\n"
    return head + "\n".join(paras)


def _sources(folder: Path) -> list[Path]:
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            if name.startswith(".") or not name.endswith(".db"):
                continue
            p = Path(dirpath) / name
            if p.is_file():
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    wrote = skipped = 0
    for path in _sources(src):
        try:
            text = store_text(path)
            if text is None:
                skipped += 1
                continue
            rel = path.relative_to(src)
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except OSError:
            skipped += 1
            continue
        wrote += 1
    return wrote, skipped


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2])) if argv[:1] == ["mirror"] else {}
    if len(argv) != 5 or sorted(opts) != ["--from", "--to"]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    if not Path(opts["--from"]).is_dir():
        print(f"refused: not a folder: {opts['--from']}", file=sys.stderr)
        return kernel.REFUSED
    src, dst = Path(opts["--from"]).resolve(), Path(opts["--to"]).resolve()
    if _within(dst, src) or _within(src, dst):
        print(
            "refused: MIRROR and FOLDER must not be inside one another",
            file=sys.stderr,
        )
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
