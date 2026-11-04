"""order.py: the lists people add to by hand, kept A to Z by a script. Python 3.9+.

    python adapters/stdlib/ci/order.py check
    python adapters/stdlib/ci/order.py write

A list nothing reads in order still gets read by people, and added to: a
new line goes at its end, and two pull requests that each add one there
collide on the same line. Kept A to Z, each goes in its own place.

The lists:

- the tables in test_contract.py that people add an add-on to (COMMANDS,
  READERS, PILE_EXTRA, REPORT_COMMANDS), by name, each entry with the
  comment lines above it, a `**` spread kept at the end;
- adapters/planned.json, by name, written as it always is;
- FILES.md's folders kept A to Z, with a slip or two by hand
  (files.py's rule), each entry with its notes and what's under it; a
  folder in an order of its own is left as it is.

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
TABLES = {CONTRACT: ("PILE_EXTRA", "READERS", "COMMANDS", "REPORT_COMMANDS")}
PLANNED = "adapters/planned.json"


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
def _table(tree: ast.Module, name: str) -> ast.Dict:
    for node in tree.body:
        target = (
            node.targets[0] if isinstance(node, ast.Assign) else
            node.target if isinstance(node, ast.AnnAssign) else None
        )  # fmt: skip
        if getattr(target, "id", None) == name and isinstance(node.value, ast.Dict):
            return node.value
    raise Refused(f"{name} isn't a table at the top of the file")


def sort_table(src: str, name: str) -> str:
    """The source with table `name`'s entries A to Z; the same source when
    they are already."""
    table = _table(ast.parse(src), name)
    lines = src.splitlines(keepends=True)
    entries = list(zip(table.keys, table.values))
    named = [(k, v) for k, v in entries if k is not None]
    if any(k is not None for k, _ in entries[len(named) :]):
        raise Refused(f"{name}: a ** spread in the middle")
    if not all(
        isinstance(k, ast.Constant) and isinstance(k.value, str) for k, _ in named
    ):
        raise Refused(f"{name}: a key that isn't a string")
    keys = [k.value for k, _ in named]
    if len(set(keys)) < len(keys):
        raise Refused(f"{name}: a name twice, where the order says which one counts")
    blocks, start = [], table.lineno  # 0-based: the line after the {
    for k, v in named:
        if k.lineno <= start:
            raise Refused(f"{name}: {k.value!r} shares a line with the entry before it")
        block = lines[start : v.end_lineno]
        last = block[-1]
        at = v.end_col_offset - (len(lines[v.end_lineno - 1]) - len(last))
        after = last[at:].lstrip()
        if not after.startswith(","):
            if after.strip() and not after.startswith("#"):
                raise Refused(f"{name}: {k.value!r} is followed on its line by more")
            ahead = "".join(lines[v.end_lineno :]).lstrip()
            if ahead.startswith(","):
                raise Refused(f"{name}: {k.value!r} has its comma on a line of its own")
            block[-1] = last[:at] + "," + last[at:]
        blocks.append((k.value, block))
        start = v.end_lineno
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
    moved = [f for f in ["", *sorted(tree.folders())] if tree.sort(f)]
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
