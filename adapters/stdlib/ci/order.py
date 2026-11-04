"""order.py: the lists people add to by hand, kept A to Z by a script. Python 3.9+.

    python adapters/stdlib/ci/order.py check
    python adapters/stdlib/ci/order.py write

A list nothing reads in order still gets read by people, and added to: a
new line goes at its end, and two pull requests that each add one there
collide on the same line. Kept A to Z, each goes in its own place.

The lists:

- the tables in test_contract.py that people add an add-on to (COMMANDS,
  READERS, PILE_EXTRA, REPORT_COMMANDS), by name, and ci.py's DEMO_TESTS,
  by gate: each entry with the comment lines above it, a `**` spread kept
  at the end;
- adapters/planned.json, by name, written as it always is;
- FILES.md's folders kept A to Z, with a slip or two by hand
  (files.py's rule), and demo/ always, each entry with its notes and
  what's under it; a folder in an order of its own is left as it is.

`check` names each list out of order; `write` puts it in order and moves
nothing else. A table it can't take apart line by line (two entries on one
line, a spread in the middle) is refused, by name, and left as it is.

Exit codes, the kernel's: 0 every list is A to Z (write: it is now); 2
check: one isn't, or refused.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

USAGE = "usage: order.py check | order.py write"
CONTRACT = "adapters/stdlib/ci/test_contract.py"
TABLES = {
    "adapters/stdlib/ci/ci.py": ("DEMO_TESTS",),
    CONTRACT: ("PILE_EXTRA", "READERS", "COMMANDS", "REPORT_COMMANDS"),
}
PLANNED = "adapters/planned.json"
#: FILES.md's folders sorted even when they look kept in an order of their own
ALWAYS = ("demo",)


class Refused(Exception):
    pass


def _files_mod(root: Path):
    spec = importlib.util.spec_from_file_location(
        "willow_files_for_order", root / "adapters/stdlib/ci/files.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── a Python table ───────────────────────────────────────────────────────────
def _table(tree: ast.Module, name: str) -> ast.expr:
    for node in tree.body:
        target = (
            node.targets[0] if isinstance(node, ast.Assign) else
            node.target if isinstance(node, ast.AnnAssign) else None
        )  # fmt: skip
        if getattr(target, "id", None) == name and isinstance(
            node.value, (ast.Dict, ast.Tuple, ast.List)
        ):
            return node.value
    raise Refused(f"{name} isn't a table at the top of the file")


def _entries(table: ast.expr, name: str) -> list[tuple[object, ast.AST, ast.AST]]:
    """(name, its first node, its last node) for each entry: a dict's key
    and value, or a row of a tuple or list named by its first item. A dict's
    ** spreads, at its end, aren't entries."""
    if isinstance(table, ast.Dict):
        pairs = list(zip(table.keys, table.values))
        named = [(k, v) for k, v in pairs if k is not None]
        if any(k is not None for k, _ in pairs[len(named) :]):
            raise Refused(f"{name}: a ** spread in the middle")
        return [(getattr(k, "value", None), k, v) for k, v in named]
    rows = []
    for row in table.elts:
        if not isinstance(row, (ast.Tuple, ast.List)) or not row.elts:
            raise Refused(f"{name}: a row that isn't a tuple named by its first item")
        rows.append((getattr(row.elts[0], "value", None), row, row))
    return rows


def _col(line: str, offset: int) -> int:
    """ast's column, counted in UTF-8 bytes, as a column in the line."""
    return len(line.encode("utf-8")[:offset].decode("utf-8"))


def sort_table(src: str, name: str) -> str:
    """The source with table `name`'s entries A to Z; the same source when
    they are already."""
    table = _table(ast.parse(src), name)
    lines = src.splitlines(keepends=True)
    entries = _entries(table, name)
    if not all(isinstance(key, str) for key, _, _ in entries):
        raise Refused(f"{name}: a key that isn't a string")
    keys = [key for key, _, _ in entries]
    if len(set(keys)) < len(keys):
        raise Refused(f"{name}: a name twice, where the order says which one counts")
    blocks, start = [], table.lineno  # 0-based: the line after the opening one
    for key, first, last_node in entries:
        if first.lineno <= start:
            raise Refused(f"{name}: {key!r} shares a line with the entry before it")
        end = last_node.end_lineno
        block = lines[start:end]
        last = block[-1]
        at = _col(last, last_node.end_col_offset)
        after = last[at:].lstrip()
        if not after.startswith(","):
            if after.strip() and not after.startswith("#"):
                raise Refused(f"{name}: {key!r} is followed on its line by more")
            if "".join(lines[end:]).lstrip().startswith(","):
                raise Refused(f"{name}: {key!r} has its comma on a line of its own")
            block[-1] = last[:at] + "," + last[at:]
        blocks.append((key, block))
        start = end
    if keys == sorted(keys, key=str.lower):
        return src
    ordered = sorted(blocks, key=lambda b: b[0].lower())
    body = [line for _, block in ordered for line in block]
    return "".join(lines[: table.lineno] + body + lines[start:])


# ── every list ───────────────────────────────────────────────────────────────
def run(root: Path, write: bool) -> list[str]:
    """The lists out of order (put in order when `write`)."""
    out = []
    for rel, names in TABLES.items():
        path = root / rel
        src = before = path.read_text(encoding="utf-8")
        for name in names:
            sorted_src = sort_table(src, name)
            if sorted_src != src:
                out.append(f"{rel}: {name}")
                src = sorted_src
        if write and src != before:
            path.write_text(src, encoding="utf-8")
    planned = root / PLANNED
    entries = json.loads(planned.read_text(encoding="utf-8"))
    if [e["name"] for e in entries] != sorted(e["name"] for e in entries):
        out.append(PLANNED)
        if write:
            entries.sort(key=lambda e: e["name"])
            planned.write_text(
                json.dumps(entries, indent=1, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
    files = _files_mod(root)
    doc = root / "FILES.md"
    tree = files.Tree(doc.read_text(encoding="utf-8"))
    folders = ["", *sorted(tree.folders())]
    moved = [f for f in folders if tree.sort(f, always=f in ALWAYS)]
    out += [f"FILES.md: {f or 'willow'}/" for f in moved]
    if write and moved:
        doc.write_text(tree.text(), encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    if argv not in (["check"], ["write"]):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    write = argv == ["write"]
    try:
        out = run(ROOT, write)
    except Refused as why:
        print(f"refused: {why}", file=sys.stderr)
        return kernel.REFUSED
    for item in out:
        print(f"{'put A to Z' if write else 'out of order'}: {item}")
    if out and not write:
        print("python adapters/stdlib/ci/order.py write puts them in order")
        return kernel.REFUSED
    print("every list is A to Z" + (" now" if out else ""))
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
