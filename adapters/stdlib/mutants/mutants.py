"""mutants.py: can an add-on's tests fail? Break its code on purpose and see.

    python adapters/stdlib/mutants/mutants.py run [NAME ...] [--per N]
    python adapters/stdlib/mutants/mutants.py list NAME

A mutant is the add-on's code with one small thing broken: a comparison
turned around (`==` to `!=`, `<` to `>=`, `in` to `not in`), an `and` made an
`or` (or the reverse), or a whole number made one larger. `run` makes up to
N of them per add-on (6 unless `--per` says), one at a time, in a copy of the
repo (never the repo itself), and runs that add-on's tests against each, with
its share of the checks every add-on keeps (ci/test_contract.py). A
mutant the tests fail on is killed. One they pass on survived: the tests
can't tell that code from the broken one.

Which mutants: every place one can be made has an id, the SHA-256 of the
file, the kind, the code there and which time that code repeats, so it
stays the same when lines move. The N with the lowest ids are made. Anyone
can redo the choice, and nobody picks the easy ones.

Some survivors break nothing a person would notice: a usage message cut a
different way, an import path the test layout hides. Each is listed in
accepted.json, by id, with the reason in a sentence. `run` fails an add-on
when a mutant survives that isn't listed there, and when a listed one is no
longer made or no longer survives, so the list can't go stale. A check that
can't fail is no check (CONST-IV-9).

Only adapters/stdlib: a deps add-on's tests need its own installs (the deps
part of ci.py makes those).

A run of the tests that ends any other way than passing or failing (no tests
found, a collection error) killed nothing: it is said, and fails the add-on,
never counted as a kill. The script's entry guard, `if __name__ ==
"__main__"`, is never broken: broken, it runs the add-on's main as its tests
import it, which stops pytest outright, and ci/test_contract.py already runs
every add-on as a script.

Exit codes, the kernel's: 0 every mutant killed or accepted; 42 the tests
couldn't run (pytest isn't installed); 2 a survivor not accepted, a stale
acceptance, a run that ended some other way, or a bad command line.
"""

from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

STDLIB = ROOT / "adapters" / "stdlib"
ACCEPTED = Path(__file__).resolve().parent / "accepted.json"
#: what every add-on promises alike; run for this add-on alone (WILLOW_ONLY)
CONTRACT = "adapters/stdlib/ci/test_contract.py"
PER = 6
SWAP = {
    ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Lt: ast.GtE, ast.GtE: ast.Lt,
    ast.Gt: ast.LtE, ast.LtE: ast.Gt, ast.In: ast.NotIn, ast.NotIn: ast.In,
    ast.Is: ast.IsNot, ast.IsNot: ast.Is,
}  # fmt: skip
USAGE = "usage: mutants.py run [NAME ...] [--per N] | mutants.py list NAME"


def code_files(name: str) -> list[Path]:
    """An add-on's own code: its .py files, not its tests."""
    here = STDLIB / name
    return sorted(
        p for p in here.rglob("*.py")
        if not p.name.startswith(("test_", "conftest")) and "__pycache__" not in p.parts
    )  # fmt: skip


def points(tree: ast.AST) -> list[tuple[str, ast.AST]]:
    """Every place in a parsed file a mutant can be made, in walk order."""
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Compare) and type(n.ops[0]) in SWAP:
            if isinstance(n.left, ast.Name) and n.left.id == "__name__":
                continue  # the script's entry guard: ci/test_contract.py runs each add-on as a script
            out.append(("compare", n))
        elif isinstance(n, ast.BoolOp):
            out.append(("and-or", n))
        elif (
            isinstance(n, ast.Constant)
            and type(n.value) is int
            and not isinstance(n.value, bool)
        ):
            out.append(("number", n))
    return out


def mutants(name: str) -> list[dict]:
    """Every mutant of an add-on, each with its id, sorted by id."""
    out = []
    for path in code_files(name):
        source = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT).as_posix()
        seen: dict[tuple, int] = {}
        for i, (kind, node) in enumerate(points(ast.parse(source))):
            code = ast.get_source_segment(source, node) or ""
            nth = seen[(kind, code)] = seen.get((kind, code), -1) + 1
            mid = kernel.h256(f"{rel}\x1f{kind}\x1f{code}\x1f{nth}")[:12]
            out.append({"id": mid, "file": rel, "line": node.lineno,
                        "kind": kind, "code": code, "point": i})  # fmt: skip
    return sorted(out, key=lambda m: m["id"])


def broken(source: str, point: int) -> str:
    """The file's source with the mutant at `point` made."""
    tree = ast.parse(source)
    kind, node = points(tree)[point]
    if kind == "compare":
        node.ops[0] = SWAP[type(node.ops[0])]()
    elif kind == "and-or":
        node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
    else:
        node.value += 1
    return ast.unparse(tree) + "\n"


def addons(names: list[str]) -> list[str]:
    every = sorted(
        p.name for p in STDLIB.iterdir()
        if p.is_dir() and not p.name.startswith(("_", ".")) and p.name != "mutants"
    )  # fmt: skip
    return names or every


def run(names: list[str], per: int) -> int:
    if subprocess.run([sys.executable, "-c", "import pytest"],
                      capture_output=True).returncode != 0:  # fmt: skip
        print("unreachable: pytest isn't installed")
        return kernel.ESCALATE
    accepted = json.loads(ACCEPTED.read_text(encoding="utf-8"))
    bad = 0
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "repo"
        shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(
            ".git", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules",
            ".ci-record", "life", "obj", "bin", "dist", "out"))  # fmt: skip
        for name in names:
            chosen = mutants(name)[:per]
            survived, couldnt = [], []
            for m in chosen:
                target = copy / m["file"]
                original = target.read_text(encoding="utf-8")
                target.write_text(broken(original, m["point"]), encoding="utf-8")
                try:
                    targets = [copy / "adapters" / "stdlib" / name]
                    if (copy / CONTRACT).is_file():
                        targets.append(copy / CONTRACT)
                    got = subprocess.run(
                        [sys.executable, "-m", "pytest", "-q", "-x", "-p",
                         "no:cacheprovider", *map(str, targets)],
                        capture_output=True, text=True, timeout=600,
                        # no bytecode cache: a mutant the same size as the last
                        # one, written in the same second, would otherwise run
                        # the last one's cached code, and pass as a survivor
                        env={**os.environ, "WILLOW_ONLY": name, "PYTHONDONTWRITEBYTECODE": "1"},
                    )  # fmt: skip
                    # 1 is a test failing on the mutant: killed. 0 is every test
                    # passing: survived. Anything else (no tests, a collection
                    # error) killed nothing, and is said, never counted as a kill.
                    if got.returncode == 0:
                        survived.append(m)
                    elif got.returncode != 1:
                        couldnt.append(f"{m['id']}: pytest exited {got.returncode}")
                finally:
                    target.write_text(original, encoding="utf-8")
            mine = accepted.get(name, {})
            wrong = [m for m in survived if m["id"] not in mine]
            stale = sorted(set(mine) - {m["id"] for m in survived})
            killed = len(chosen) - len(survived) - len(couldnt)
            print(f"{name}: {killed} of {len(chosen)} killed, "
                  f"{len(survived) - len(wrong)} accepted")  # fmt: skip
            for m in wrong:
                print(
                    f"  survived {m['id']}  {m['file']}:{m['line']}  {m['kind']}: {m['code']}"
                )
            for why in couldnt:
                print(f"  couldn't run {why}")
            for mid in stale:
                print(f"  stale {mid}: accepted, but no longer made or no longer surviving; take it out of accepted.json")  # fmt: skip
            bad += len(wrong) + len(stale) + len(couldnt)
    return kernel.REFUSED if bad else kernel.ALIVE


def main(argv: list[str]) -> int:
    if argv[:1] == ["list"] and len(argv) == 2:
        for m in mutants(argv[1]):
            print(f"{m['id']}  {m['file']}:{m['line']}  {m['kind']}: {m['code']}")
        return kernel.ALIVE
    if argv[:1] != ["run"]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    rest, per = argv[1:], PER
    if "--per" in rest:
        i = rest.index("--per")
        if i + 1 >= len(rest) or not rest[i + 1].isdigit():
            print(USAGE, file=sys.stderr)
            return kernel.REFUSED
        per, rest = int(rest[i + 1]), rest[:i] + rest[i + 2 :]
    unknown = [n for n in rest if not (STDLIB / n).is_dir()]
    if unknown:
        print(
            f"refused: no add-on {', '.join(unknown)} in adapters/stdlib",
            file=sys.stderr,
        )
        return kernel.REFUSED
    return run(addons(rest), per)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
