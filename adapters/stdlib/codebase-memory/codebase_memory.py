"""codebase_memory.py: a code-graph SQLite file as passages. Python 3.9+.

    python adapters/stdlib/codebase-memory/codebase_memory.py \\
        mirror --from FOLDER --to MIRROR

Walks FOLDER for `.db` files that hold a code graph (the tables
codebase-memory-mcp writes, or a copy of them: `nodes` and `edges` as it
writes them now, `symbols` and `edges` as it did). Each function or method
becomes one paragraph: its name, its file and line, and what it calls or
imports. A name the graph has for a language's own built-ins, which have no
file, is left out.

    vendor_sync_check (function)
    file: tools/vendor_sync_check.py:129
    imports: tools.vendor_sync_check.CheckResult

Each graph is written to MIRROR at the same relative path with `.txt`
added. One too long for the kernel to read as a single file (its cap is a
megabyte) is cut between functions into `.1.txt`, `.2.txt` and so on. A file that is not a graph is skipped and counted. Hidden folders
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
        if {"nodes", "edges"} <= tables:
            symbols, outs = _nodes(con)
        elif not {"symbols", "edges"} <= tables:
            return None
        else:
            symbols, outs = _symbols(con)
    except sqlite3.Error:
        return None
    finally:
        con.close()
    return _paragraphs(symbols, outs)


#: the edges of the graph as it is written now that say what a function
#: reaches for, and the word each is said with
REACHES = {"CALLS": "call", "IMPORTS": "import", "INHERITS": "inherit"}


def _nodes(con) -> tuple[list, dict[str, list[str]]]:
    """The functions and methods of a graph kept as `nodes` and `edges`, in
    the shape of the older tables: (fqn, name, kind, file, line) rows, and
    what each reaches."""
    symbols = con.execute(
        "SELECT qualified_name, name, lower(label), file_path, start_line FROM nodes "
        "WHERE label IN ('Function', 'Method') AND file_path NOT LIKE '<%' "
        "ORDER BY qualified_name"
    ).fetchall()
    outs: dict[str, list[str]] = {}
    marks = ", ".join("?" * len(REACHES))
    for src, tgt, kind in con.execute(
        "SELECT s.qualified_name, t.qualified_name, e.type FROM edges e "
        "JOIN nodes s ON s.id = e.source_id JOIN nodes t ON t.id = e.target_id "
        f"WHERE e.type IN ({marks}) ORDER BY s.qualified_name, t.qualified_name",
        sorted(REACHES),
    ):
        said = f"{REACHES[kind]} {_one_line(tgt)}"
        if said not in outs.setdefault(src, []):
            outs[src].append(said)
    return symbols, outs


def _symbols(con) -> tuple[list, dict[str, list[str]]]:
    """The same from a graph kept as `symbols` and `edges`."""
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
    return symbols, outs


def _paragraphs(symbols: list, outs: dict[str, list[str]]) -> str:
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


def parts(text: str, most: int = kernel.MAX_FILE) -> list[str]:
    """A graph's text as the files it is written to: one, when the kernel
    will read a file that long; else cut between functions into parts that
    each fit, every part saying which it is. The kernel leaves out a file
    over its size cap without a word, so a whole graph in one file is a
    mirror nothing can ask."""
    if len(text.encode("utf-8")) <= most:
        return [text]
    head, _, body = text.partition("\n\n")
    room = most - len(head.encode("utf-8")) - 64
    out: list[list[str]] = [[]]
    size = 0
    for para in body.split("\n\n"):
        n = len(para.encode("utf-8")) + 2
        if out[-1] and size + n > room:
            out.append([])
            size = 0
        out[-1].append(para)
        size += n
    return [
        f"{head}, part {i} of {len(out)}\n\n" + "\n\n".join(ps).rstrip("\n") + "\n"
        for i, ps in enumerate(out, 1)
    ]


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


# differs on purpose: graph_text skips what isn't a graph, so only OSError is left to catch
def mirror(src: Path, dst: Path) -> tuple[int, int]:
    wrote = skipped = 0
    for path in _sources(src):
        try:
            text = graph_text(path)
            if text is None:
                skipped += 1
                continue
            rel = path.relative_to(src)
            cut = parts(text)
            for i, part in enumerate(cut, 1):
                name = f"{rel.name}.txt" if len(cut) == 1 else f"{rel.name}.{i}.txt"
                target = dst.joinpath(rel.parent, name)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(part.encode("utf-8"))
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
