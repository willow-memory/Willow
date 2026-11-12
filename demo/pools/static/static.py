"""static.py: what each built add-on's code says it takes and gives, read and not run.

    python demo/pools/static/static.py say [--json]

For every add-on under adapters/stdlib with a card, from its code (tests
left out), by `ast`: the kinds of row it writes to the record (the kind
given to `kernel.append`), the kinds of row it tells apart (a string a
row's `kind` is compared with), whether it reads the record at all, and
the file suffixes it names in a string. Then who makes each kind of row
and who takes it.

It is rough, and says so: a suffix is any string like `.abc`, so a
number's format leaks in; a kind is any string compared with `kind`, so
a few are not row kinds. It runs nothing and writes nothing. `--json`
prints one entry an add-on, which is what static.json keeps.

Exit codes, the kernel's: 0 said; 2 refused (a bad command line).
"""

from __future__ import annotations

import ast
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

USAGE = __doc__.split("\n\n")[1]
STDLIB = Path(__file__).resolve().parents[3] / "adapters" / "stdlib"
CARD = re.compile(r"<!-- willow-addon\n(.*?)-->", re.S)
SUFFIX = re.compile(r"\.[a-z0-9]{2,6}")
RECORD_READS = ("read", "verify", "rows")


def card_of(folder: Path) -> dict:
    """The fields of an add-on's card, or {} when its README holds none."""
    readme = folder / "README.md"
    found = CARD.search(readme.read_text(encoding="utf-8")) if readme.exists() else None
    out = {}
    for line in found.group(1).splitlines() if found else []:
        key, _, value = line.partition(":")
        if value.strip():
            out[key.strip()] = value.strip()
    return out


def names(tree: ast.Module) -> dict[str, str]:
    """The module's names that are set to a string, alone or in a tuple."""
    out = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        pairs = [(t, node.value) for t in node.targets]
        if isinstance(node.value, ast.Tuple) and isinstance(node.targets[0], ast.Tuple):
            pairs = list(zip(node.targets[0].elts, node.value.elts))
        for target, value in pairs:
            if isinstance(target, ast.Name) and isinstance(value, ast.Constant) and isinstance(value.value, str):  # fmt: skip
                out[target.id] = value.value
    return out


def strings(node: ast.AST, known: dict[str, str]) -> list[str]:
    """The strings a node comes to: itself, a name set to one, or each of a
    tuple, list or set."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.Name) and node.id in known:
        return [known[node.id]]
    if isinstance(node, (ast.Tuple, ast.Set, ast.List)):
        return [s for e in node.elts for s in strings(e, known)]
    return []


def is_kind(node: ast.AST) -> bool:
    """Whether a node is a row's kind: `row["kind"]` or `row.get("kind")`."""
    if isinstance(node, ast.Subscript):
        return isinstance(node.slice, ast.Constant) and node.slice.value == "kind"
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get":  # fmt: skip
        return bool(node.args) and isinstance(node.args[0], ast.Constant) and node.args[0].value == "kind"  # fmt: skip
    return False


def of_kernel(node: ast.AST) -> str | None:
    """The kernel function a call calls, or None."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if isinstance(node.func.value, ast.Name) and node.func.value.id == "kernel":
            return node.func.attr
    return None


def read(folder: Path) -> dict:
    """What one add-on's code says, over its files that are not tests."""
    writes, takes, files = set(), set(), set()
    unread, reads_record = 0, False
    for file in sorted(folder.glob("*.py")):
        if file.name.startswith("test_"):
            continue
        try:
            tree = ast.parse(file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        known = names(tree)
        for node in ast.walk(tree):
            called = of_kernel(node)
            if called == "append":
                got = strings(node.args[2], known) if len(node.args) > 2 else []
                writes.update(got)
                unread += not got
            reads_record = reads_record or called in RECORD_READS
            if isinstance(node, ast.Compare):
                sides = [node.left, *node.comparators]
                if any(is_kind(s) for s in sides):
                    takes.update(s for side in sides for s in strings(side, known))
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if SUFFIX.fullmatch(node.value):
                    files.add(node.value)
    return {"writes": sorted(writes), "writes_unread": unread, "takes": sorted(takes),
            "reads_record": reads_record, "files": sorted(files)}  # fmt: skip


def every() -> dict[str, dict]:
    out = {}
    for folder in sorted(p for p in STDLIB.iterdir() if p.is_dir()):
        card = card_of(folder)
        if card:
            kept = {
                k: card.get(k)
                for k in ("section", "role", "output", "writes", "uses", "reads")
            }
            out[folder.name] = {"card": kept, **read(folder)}
    return out


def say(found: dict[str, dict]) -> str:
    makers, takers, named = defaultdict(set), defaultdict(set), defaultdict(set)
    for name, got in found.items():
        for kind in got["writes"]:
            makers[kind].add(name)
        for kind in got["takes"]:
            takers[kind].add(name)
        for suffix in got["files"]:
            named[suffix].add(name)
    kinds = sorted(set(makers) | set(takers))
    own = [k for k in kinds if makers[k] and takers[k] and takers[k] <= makers[k]]
    untaken = [k for k in kinds if makers[k] and not takers[k]]
    across = {k: sorted(takers[k] - makers[k]) for k in kinds if makers[k] and takers[k] - makers[k]}  # fmt: skip
    links = {(m, t) for k, ts in across.items() for m in makers[k] for t in ts}
    touches = [g["writes"] or g["writes_unread"] or g["takes"] or g["reads_record"] or g["files"]
               for g in found.values()]  # fmt: skip
    out = [
        f"{len(found)} add-ons with a card under adapters/stdlib",
        f"write a row to the record: {sum(bool(g['writes']) or g['writes_unread'] > 0 for g in found.values())}",  # fmt: skip
        f"tell rows apart by kind: {sum(bool(g['takes']) for g in found.values())}",
        f"read the record at all: {sum(g['reads_record'] for g in found.values())}",
        f"name a file suffix: {sum(bool(g['files']) for g in found.values())}",
        f"none of those: {sum(not t for t in touches)}",
        f"kinds of row seen: {len(kinds)}",
        f"made and taken only by their maker: {len(own)}",
        f"made and taken by nothing: {len(untaken)} ({', '.join(untaken)})",
        f"made by one add-on and taken by another: {len(across)}",
    ]
    for kind, by in sorted(across.items(), key=lambda x: -len(x[1])):
        out.append(
            f"  {kind}: made by {', '.join(sorted(makers[kind]))}; taken by {', '.join(by)}"
        )
    out.append(f"links from a maker to another add-on that takes: {len(links)}, "
               f"over {len({x for link in links for x in link})} add-ons")  # fmt: skip
    most = sorted(named, key=lambda s: (-len(named[s]), s))[:8]
    out.append(
        "suffixes most named: " + ", ".join(f"{s} {len(named[s])}" for s in most)
    )
    out.append(f"suffixes named by one add-on only: {sum(len(v) == 1 for v in named.values())} of {len(named)}")  # fmt: skip
    out.append(
        f"name `.places`: {len(named['.places'])} ({', '.join(sorted(named['.places']))})"
    )
    return "\n".join(out)


def main(argv: list[str]) -> int:
    if argv not in (["say"], ["say", "--json"]):
        print(USAGE, file=sys.stderr)
        return 2
    found = every()
    print(
        json.dumps(found, indent=1, sort_keys=True) if "--json" in argv else say(found)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
