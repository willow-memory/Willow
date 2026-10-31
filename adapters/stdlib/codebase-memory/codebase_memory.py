"""codebase_memory.py: a code-graph SQLite file as passages. Python 3.9+.

    python adapters/stdlib/codebase-memory/codebase_memory.py \\
        mirror --from FOLDER --to MIRROR

Walks FOLDER for `.db` files that hold a code graph (the `symbols` and
`edges` tables codebase-memory-mcp writes, or a copy of them). Each
function or method becomes one paragraph: its name, its file and line, and
what it calls or imports.

    vendor_sync_check (function)
    file: tools/vendor_sync_check.py:129
    imports: tools.vendor_sync_check.CheckResult

Each graph is written to MIRROR at the same relative path with `.txt`
added. A file that is not a graph is skipped and counted. Hidden folders
and files are skipped. The original is only read.

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

USAGE = "usage: codebase_memory.py mirror --from FOLDER --to MIRROR"


def _one_line(value) -> str:
    return " ".join(str(value).split()) if value is not None else ""


def graph_text(path: Path) -> str | None:
    """The mirror text for a graph database, or None if it isn't one."""
    try:
        con = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    try:
        tables = {
            r[0]
            for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if not {"symbols", "edges"} <= tables:
            return None
        symbols = con.execute(
            "SELECT fqn, name, kind, file_path, start_line FROM symbols "
            "WHERE kind IN ('function', 'method') ORDER BY fqn"
        ).fetchall()
        outs: dict[str, list[str]] = {}
        for src, tgt, kind in con.execute(
            "SELECT source_fqn, target_fqn, edge_type FROM edges "
            "ORDER BY source_fqn, target_fqn"
        ):
            outs.setdefault(src, []).append(f"{kind} {_one_line(tgt)}")
    except sqlite3.Error:
        return None
    finally:
        con.close()
    paras = []
    for fqn, name, kind, file_path, start in symbols:
        lines = [f"{_one_line(name) or _one_line(fqn)} ({_one_line(kind)})"]
        where = _one_line(file_path)
        if where:
            loc = f"{where}:{int(start)}" if start else where
            lines.append(f"file: {loc}")
        if _one_line(fqn) and _one_line(fqn) != _one_line(name):
            lines.append(f"name: {_one_line(fqn)}")
        called = outs.get(fqn) or []
        if called:
            lines.append("edges: " + "; ".join(called))
        paras.append("\n".join(lines) + "\n")
    n = len(paras)
    head = f"code graph: {n} function{'s' if n != 1 else ''}\n\n"
    return head + ("\n".join(paras) if paras else "")


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
            text = graph_text(path)
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
