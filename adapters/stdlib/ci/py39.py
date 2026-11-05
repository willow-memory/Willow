"""py39.py: what Python 3.10 and later added, found before CI's 3.9 run does. Python 3.9+.

    python adapters/stdlib/ci/py39.py check [PATH ...]

kernel.py and every stdlib add-on run on Python 3.9, and CI's tests run
there. ruff, held to 3.9, refuses 3.10's syntax (`match`) and, with FA102,
an `int | None` annotation in a file without `from __future__ import
annotations`; it can't see the standard library's newer names and
arguments, which load on 3.9 and fail only when they run: a keyword 3.9
doesn't take (`write_text(newline=...)` failed CI three times),
`itertools.pairwise`, `datetime.UTC`, `isinstance(x, A | B)`.

`check` reads every Python file git has (or the PATHs), less the deps
add-ons, which CI runs on 3.13 alone, and names each use by file and line
with the version that added it. Two ways a file uses a newer module on 3.9
pass: its import tried with ImportError caught, and a conftest.py above it
that puts the module in sys.modules (craft-assembly's gives pip's TOML
parser as tomllib). The list below is what it knows; a use it
doesn't know passes, and CI's 3.9 run still holds it.

Exit codes, the kernel's: 0 nothing newer than 3.9; 2 something is, or
refused.
"""

from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

USAGE = "usage: py39.py check [PATH ...]"
#: CI runs these on 3.13 alone, in the deps job
SKIP = ("adapters/deps/",)

#: (method or function name, keyword): the version that added the keyword
KEYWORDS = {
    ("write_text", "newline"): "3.10",
    ("read_text", "newline"): "3.13",
    ("zip", "strict"): "3.10",
    ("dataclass", "slots"): "3.10",
    ("dataclass", "kw_only"): "3.10",
    ("glob", "root_dir"): "3.10",
    ("glob", "include_hidden"): "3.11",
    ("rglob", "case_sensitive"): "3.12",
    ("glob", "case_sensitive"): "3.12",
    ("is_relative_to", "walk_up"): "3.12",
    ("relative_to", "walk_up"): "3.12",
    ("mkdtemp", "delete"): "3.12",
    ("TemporaryDirectory", "delete"): "3.12",
}
#: module.name: the version that added it
NAMES = {
    "itertools.pairwise": "3.10", "itertools.batched": "3.12",
    "datetime.UTC": "3.11", "contextlib.chdir": "3.11",
    "contextlib.aclosing": "3.10", "asyncio.TaskGroup": "3.11",
    "asyncio.timeout": "3.11", "math.cbrt": "3.11", "math.exp2": "3.11",
    "sys.orig_argv": "3.10", "sys.stdlib_module_names": "3.10",
    "typing.Self": "3.11", "typing.Never": "3.11", "typing.TypeAlias": "3.10",
    "typing.ParamSpec": "3.10", "typing.TypeGuard": "3.10",
    "typing.assert_never": "3.11", "typing.LiteralString": "3.11",
    "enum.StrEnum": "3.11", "hashlib.file_digest": "3.11",
    "operator.call": "3.11",
}  # fmt: skip
#: modules added after 3.9
MODULES = {"tomllib": "3.11"}
#: builtins added after 3.9
BUILTINS = {"aiter": "3.10", "anext": "3.10", "ExceptionGroup": "3.11",
            "BaseExceptionGroup": "3.11", "EncodingWarning": "3.10"}  # fmt: skip
#: methods only a newer object has, by a name no 3.9 object uses
METHODS = {"bit_count": "3.10", "hardlink_to": "3.10", "walk": None,
           "is_junction": "3.12", "full_match": "3.13"}  # fmt: skip


def _name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _dotted(node: ast.AST) -> str:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return ""


def shims(path: Path, root: Path) -> frozenset[str]:
    """The modules a conftest.py at or above `path` puts in sys.modules."""
    out, folder = set(), path.parent
    while True:
        conftest = folder / "conftest.py"
        if conftest.is_file():
            out |= set(
                re.findall(
                    r"sys\.modules\[[\"'](\w+)[\"']\]\s*=",
                    conftest.read_text(encoding="utf-8"),
                )
            )
        if folder == root or folder == folder.parent:
            return frozenset(out)
        folder = folder.parent


def newer(source: str, shimmed: frozenset[str] = frozenset()) -> list[tuple[int, str]]:
    """(line, what 3.9 lacks and the version that added it), in order."""
    out = []
    tree = ast.parse(source)
    imported = {}  # name it's bound to here -> module.name
    guarded = {  # imports tried, with 3.9's ImportError caught
        id(n)
        for t in ast.walk(tree)
        if isinstance(t, ast.Try)
        and any(
            _name(h.type) in ("ImportError", "ModuleNotFoundError")
            for h in t.handlers
            if h.type is not None
        )  # fmt: skip
        for n in t.body
    }
    for node in ast.walk(tree):
        if id(node) in guarded:
            continue
        if isinstance(node, ast.ImportFrom) and node.module:
            for a in node.names:
                imported[a.asname or a.name] = f"{node.module}.{a.name}"
                full = f"{node.module}.{a.name}"
                if full in NAMES:
                    out.append((node.lineno, f"{full} ({NAMES[full]})"))
            if (
                node.module.split(".")[0] in MODULES
                and node.module.split(".")[0] not in shimmed
            ):
                out.append(
                    (
                        node.lineno,
                        f"{node.module} ({MODULES[node.module.split('.')[0]]})",
                    )
                )
        elif isinstance(node, ast.Import):
            for a in node.names:
                top = a.name.split(".")[0]
                if top in MODULES and top not in shimmed:
                    out.append((node.lineno, f"{a.name} ({MODULES[top]})"))
        elif isinstance(node, ast.Attribute):
            d = _dotted(node)
            if d in NAMES:
                out.append((node.lineno, f"{d} ({NAMES[d]})"))
            elif (
                node.attr in METHODS
                and METHODS[node.attr]
                and isinstance(node.ctx, ast.Load)
            ):
                out.append((node.lineno, f".{node.attr}() ({METHODS[node.attr]})"))
        elif (
            isinstance(node, ast.Name)
            and node.id in BUILTINS
            and node.id not in imported
        ):
            out.append((node.lineno, f"{node.id} ({BUILTINS[node.id]})"))
        if isinstance(node, ast.Call):
            fn = _name(node.func)
            for kw in node.keywords:
                if (fn, kw.arg) in KEYWORDS:
                    out.append(
                        (node.lineno, f"{fn}({kw.arg}=...) ({KEYWORDS[fn, kw.arg]})")
                    )
            if fn == "isinstance" and len(node.args) == 2:
                if isinstance(node.args[1], ast.BinOp) and isinstance(
                    node.args[1].op, ast.BitOr
                ):
                    out.append((node.lineno, "isinstance(x, A | B) (3.10)"))
    return sorted(set(out))


def tracked(root: Path) -> list[str]:
    git = shutil.which("git")
    if git is None or not (root / ".git").exists():
        raise SystemExit("refused: run it in a clone, or name the files")
    out = subprocess.run([git, "ls-files", "*.py"], cwd=root, capture_output=True,
                         text=True, check=True).stdout  # fmt: skip
    return [
        p for p in out.splitlines() if not p.startswith(SKIP) and (root / p).is_file()
    ]


def main(argv: list[str]) -> int:
    if not argv or argv[0] != "check" or any(a.startswith("-") for a in argv[1:]):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    paths = argv[1:] or tracked(ROOT)
    found = 0
    for rel in paths:
        path = ROOT / rel if not Path(rel).is_absolute() else Path(rel)
        try:
            hits = newer(path.read_text(encoding="utf-8"), shims(path, ROOT))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue  # ruff says what won't parse
        for line, what in hits:
            print(f"{rel}:{line}: {what}, newer than 3.9")
            found += 1
    if found:
        print(f"{found} use(s) of what 3.9 lacks: CI's 3.9 run fails on each that runs")
        return kernel.REFUSED
    print(f"{len(paths)} files: nothing newer than 3.9")
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
