"""bugs.py: BUGS.md is the repo's known bugs, and each one is a test.

    python adapters/stdlib/ci/bugs.py write
    python adapters/stdlib/ci/bugs.py check

A known bug is a test that shows it, marked as expected to fail:

    @pytest.mark.xfail(strict=True, reason="bug #12: what goes wrong, in a sentence")

`#12` is the bug's issue. The test fails today, as the bug says it does.
When someone fixes the bug, the test passes, and because the mark is
strict, a test that passes when it was expected to fail fails the run. So
the fix has to take the mark off, and BUGS.md loses the bug only then;
changelog.py then asks for a line under `### Fixed` naming it. A bug can't
be listed without a test, or leave the list without a fix (CONST-VI-7).

Every expected-to-fail mark in the repo's tests has to be one of these:
strict, with a `bug #N:` reason. Any other is refused, since a mark that
isn't strict lets a fixed bug pass unnoticed.

`write` makes BUGS.md from the tests; `check` says whether it is current.
BUGS.md is a view of the tests, recomputed, never kept by hand (CONST-VI-6).
Exit codes, the kernel's: 0 written, or current; 2 not current, a mark
refused, or a bad command line.
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

USAGE = "usage: bugs.py write | bugs.py check"
REASON = re.compile(r"bug #(\d+): (\S.*)", re.S)
HEAD = """# Known bugs

Each one is a test that shows it, marked as expected to fail, so the list
can't hold a bug nobody can show, or lose one nobody fixed. This file is
made from those tests by `python adapters/stdlib/ci/bugs.py write`, and
`test_docs.py` fails if it's out of date. How to add one, and what fixing
one takes, is in [CONTRIBUTING.md](CONTRIBUTING.md).

"""


class Refused(Exception):
    pass


def test_files() -> list[Path]:
    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "*test_*.py"],
        cwd=ROOT, capture_output=True, text=True,
    ).stdout.split()  # fmt: skip
    return sorted(ROOT / f for f in listed if (ROOT / f).is_file())


def is_xfail(node: ast.AST) -> bool:
    """`pytest.mark.xfail`, however it's reached."""
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "xfail"
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "mark"
    )


def marks(path: Path) -> list[tuple[int, str, str, ast.AST]]:
    """(line, test, how, mark) for every expected-to-fail mark in one file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    owner: dict[int, str] = {}  # each node's innermost function, decorators included
    for t in ast.walk(tree):
        if isinstance(t, ast.FunctionDef):
            for n in ast.walk(t):
                owner[id(n)] = t.name
    called = {id(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and is_xfail(n.func):
            how = "call"
        elif is_xfail(n) and id(n) not in called:
            how = "bare"
        else:
            continue
        out.append((n.lineno, owner.get(id(n), "(the whole file)"), how, n))
    return out


def bugs() -> list[dict]:
    """Every known bug, by number; refuses any mark that isn't one."""
    found, refused = [], []
    for path in test_files():
        rel = path.relative_to(ROOT).as_posix()
        for line, test, how, node in marks(path):
            where = f"{rel}:{line}"
            kw = {k.arg: k.value for k in node.keywords} if how == "call" else {}
            strict = kw.get("strict")
            reason = kw.get("reason")
            if not (isinstance(strict, ast.Constant) and strict.value is True):
                refused.append(f"{where}: an expected failure has to be strict=True")
                continue
            m = (
                REASON.fullmatch(reason.value)
                if isinstance(reason, ast.Constant) and isinstance(reason.value, str)
                else None
            )
            if not m:
                refused.append(f'{where}: its reason has to read "bug #N: what goes wrong"')  # fmt: skip
                continue
            found.append({"n": int(m.group(1)), "what": " ".join(m.group(2).split()),
                          "test": f"{rel}::{test}"})  # fmt: skip
    if refused:
        raise Refused("\n  ".join(refused))
    return sorted(found, key=lambda b: (b["n"], b["test"]))


def render(found: list[dict]) -> str:
    if not found:
        return HEAD + "None known: no test in the repo is marked as a known bug.\n"
    rows = "\n".join(f"| #{b['n']} | {b['what']} | `{b['test']}` |" for b in found)
    return HEAD + "| Bug | What goes wrong | The test that shows it |\n|---|---|---|\n" + rows + "\n"  # fmt: skip


def numbers(text: str) -> set[int]:
    """The bug numbers a BUGS.md lists."""
    return {int(n) for n in re.findall(r"^\| #(\d+) \|", text, re.M)}


def main(argv: list[str]) -> int:
    if argv not in (["write"], ["check"]):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    try:
        new = render(bugs())
    except Refused as e:
        print(f"refused:\n  {e}", file=sys.stderr)
        return kernel.REFUSED
    out = ROOT / "BUGS.md"
    if argv == ["write"]:
        out.write_text(new, encoding="utf-8")
        print(f"BUGS.md: {len(numbers(new))} known bugs written")
        return kernel.ALIVE
    if not out.is_file() or out.read_text(encoding="utf-8") != new:
        print("BUGS.md isn't current: run python adapters/stdlib/ci/bugs.py write")
        return kernel.REFUSED
    print(f"BUGS.md is current: {len(numbers(new))} known bugs")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
