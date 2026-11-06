"""copies.py: the functions add-ons keep their own copy of, and the copies that drifted. Python 3.9+.

    python adapters/stdlib/ci/copies.py survey [--json]
    python adapters/stdlib/ci/copies.py diff NAME
    python adapters/stdlib/ci/copies.py new --base REF

An add-on holds alone and shares only the kernel, so the same function lives
in many of them: a reader's `_sources`, a report's `report_text`, a model
add-on's `on_this_machine`. A copy that drifts from the others does so
silently. sort-ask's `ask_model` did: it kept its own seed and timeout, and a
setting added to openai-compatible's had to be put into both by hand.

`survey` reads every add-on's top-level functions (adapters/stdlib and
adapters/deps, tests left out), groups them by name, and finds each group's
common version: the one most copies hold, read as Python reads it, so
formatting, comments and the docstring aside. A copy that isn't it but still
holds most of its lines is a copy that drifted; one that holds less is
another function that happens to share the name (each add-on's `main`), and
is counted, not reported. It prints a report (README.md beside this file,
the report contract), a group for each function with a drifted copy:

    copies: populated, 4 functions kept in 3 or more add-ons have a copy that drifted, 6 copies in all
    ## ask_model: 2 of 3 the same, as openai-compatible has it
      sort-ask/sort_ask.py:122  3 lines differ

`diff NAME` prints, for each drifted copy of NAME, the lines it differs by
from the common version, as a unified diff, the common one first.

**A copy that differs on purpose says why**, in a comment on the line above
its `def`: `# differs on purpose: its report shows the kernel's refusal`.
Its row says so, and a survey whose every drift says why exits 0.

`new --base REF` is for a pull request: the copies that drifted in it and
don't say why, each with its diff, as Markdown for the run's summary, read
from REF's files by git without touching the checkout. A suggestion, never
a gate: it exits 0 whatever it finds.

A group needs three copies to have a common version, and two of them the
same; on a tie, the common version is the one the first add-on, A to Z,
keeps. Which copy is right is a person's call: the common one is only the
most kept, and a drift can be the fix the others lack.

Exit codes, the kernel's: survey, 0 no copy drifted but on purpose, 42 one
did; diff, 0 the copies of NAME are all the same, 42 one isn't; new, 0; 2
refused (a bad command line, a NAME no three add-ons keep, a REF git
doesn't know).
"""

from __future__ import annotations

import ast
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

NAME = "copies"
USAGE = (
    "usage: copies.py survey [--json] | copies.py diff NAME | copies.py new --base REF"
)
KINDS = ("stdlib", "deps")
#: the fewest copies a function needs for a common version, and the fewest
#: of them that must be the same
FEWEST, SAME = 3, 2
#: the share of the common version's lines a drifted copy still holds; under
#: it, a copy is another function that shares the name
NEAR = 0.6
#: the comment above a copy's def that says why it differs
WHY = re.compile(r"#\s*differs on purpose:\s*(\S.*?)\s*$")


# ── the report: the shape every report add-on prints (ci/README.md) ─────────
def report(addon: str, state: str, said: str, groups: list) -> dict:
    """A report: its state, one line said, and each group's rows (where,
    what); a group named None comes first and has no heading."""
    return {"addon": addon, "state": state, "said": said,
            "groups": [{"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
                       for g, rows in groups if rows]}  # fmt: skip


def report_text(doc: dict) -> str:
    rows = [r for g in doc["groups"] for r in g["rows"]]
    w = min(max((len(r["where"]) for r in rows), default=0), 60)
    out = [f"{doc['addon']}: {doc['state']}, {doc['said']}"]
    for g in doc["groups"]:
        if g["name"] is not None:
            out.append(f"## {g['name']}")
        out += [f"  {r['where']:<{w}}  {r['what']}".rstrip() for r in g["rows"]]
    return "\n".join(out)


def say(doc: dict, as_json: bool) -> None:
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))


def body(node: ast.FunctionDef) -> str:
    """A function as Python reads it, its docstring left out: the text two
    copies are compared by, whatever their formatting and comments."""
    node = ast.parse(ast.unparse(node)).body[0]
    first = node.body[0] if node.body else None
    if isinstance(first, ast.Expr) and isinstance(
        getattr(first, "value", None), ast.Constant
    ):
        if isinstance(first.value.value, str):
            node.body = node.body[1:] or [ast.Pass()]
    return ast.unparse(node) + "\n"


def sources(root: Path = ROOT) -> list[tuple[str, str]]:
    """(the add-on's file, its text) for each add-on script in the checkout,
    tests left out."""
    out = []
    for kind in KINDS:
        for path in sorted((root / "adapters" / kind).glob("*/*.py")):
            if not path.name.startswith("test_"):
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                out.append(
                    (path.relative_to(root / "adapters" / kind).as_posix(), text)
                )
    return out


def sources_at(ref: str, root: Path = ROOT) -> list[tuple[str, str]] | None:
    """The same, as REF has them, read by git; None when git doesn't know REF."""

    def git(*argv: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *argv], cwd=root, capture_output=True)

    got = git(
        "ls-tree", "-r", "--name-only", ref, "--", *(f"adapters/{k}" for k in KINDS)
    )
    if got.returncode != 0:
        return None
    out = []
    for path in sorted(got.stdout.decode().splitlines()):
        parts = path.split("/")
        if (
            len(parts) == 4
            and parts[3].endswith(".py")
            and not parts[3].startswith("test_")
        ):
            blob = git("show", f"{ref}:{path}")
            if blob.returncode == 0:
                out.append(
                    ("/".join(parts[2:]), blob.stdout.decode("utf-8", "replace"))
                )
    return out


def functions(
    root: Path = ROOT, found: list | None = None
) -> dict[str, list[tuple[str, int, str, str]]]:
    """{function name: [(add-on's file, line, body, why it differs)]}, one per
    add-on that defines it at the top level of a script, tests left out; why
    is what the comment above its def says, or nothing."""
    out: dict[str, list[tuple[str, int, str, str]]] = {}
    for rel, text in sources(root) if found is None else found:
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        lines, seen = text.splitlines(), set()
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name not in seen:
                seen.add(node.name)
                above = lines[node.lineno - 2] if node.lineno >= 2 else ""
                why = WHY.search(above)
                out.setdefault(node.name, []).append(
                    (rel, node.lineno, body(node), why.group(1) if why else "")
                )
    return out


def near(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.splitlines(), b.splitlines()).ratio()


def drift(copies: list[tuple[str, int, str, str]]) -> dict | None:
    """A group's common version, the copies holding it, the drifted ones and
    how many others share only the name; None when it has no common version
    (fewer than FEWEST copies, or none held by SAME of them)."""
    if len({c[0].split("/")[0] for c in copies}) < FEWEST:
        return None
    held: dict[str, list] = {}
    for c in copies:
        held.setdefault(c[2], []).append(c)
    common, keep = sorted(held.items(), key=lambda kv: (-len(kv[1]), kv[1][0][0]))[0]
    if len(keep) < SAME:
        return None
    rest = [c for c in copies if c[2] != common]
    drifted = [c for c in rest if near(common, c[2]) >= NEAR]
    return {"common": common, "same": keep, "drifted": drifted,
            "others": len(rest) - len(drifted)}  # fmt: skip


def differ(common: str, copy: str) -> int:
    """How many lines a copy differs from the common version by: those it
    adds or takes away."""
    return sum(
        1
        for d in difflib.ndiff(common.splitlines(), copy.splitlines())
        if d[:1] in "+-"
    )


def survey(root: Path = ROOT) -> tuple[dict, int]:
    groups, copies, unsaid = [], 0, 0
    for name, found in sorted(functions(root).items()):
        got = drift(found)
        if not got or not got["drifted"]:
            continue
        at = got["same"][0][0].split("/")[0]
        head = f"{name}: {len(got['same'])} of {len(found)} the same, as {at} has it"
        rows = [(f"{rel}:{line}", f"{differ(got['common'], text)} lines differ"
                 + (f"; on purpose: {why}" if why else ""))
                for rel, line, text, why in got["drifted"]]  # fmt: skip
        unsaid += sum(1 for c in got["drifted"] if not c[3])
        groups.append((head, rows))
        copies += len(rows)
    if not groups:
        doc = report(
            NAME, "empty", "no copy of a function kept in 3 or more add-ons drifted", []
        )
        return doc, kernel.ALIVE
    said = (f"{len(groups)} function{'s' * (len(groups) != 1)} kept in {FEWEST} or more add-ons"
            f" {'have' if len(groups) != 1 else 'has'} a copy that drifted,"
            f" {copies} cop{'ies' if copies != 1 else 'y'} in all")  # fmt: skip
    if unsaid != copies:
        said += f", {copies - unsaid} of them on purpose"
    return report(
        NAME, "populated", said, groups
    ), kernel.ESCALATE if unsaid else kernel.ALIVE


def diff(name: str, root: Path = ROOT) -> int:
    got = drift(functions(root).get(name, []))
    if got is None:
        print(f"refused: {name} isn't a function {FEWEST} or more add-ons keep the same", file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    if not got["drifted"]:
        print(f"{name}: every copy is the common version, {len(got['same'])} of them")
        return kernel.ALIVE
    at, line = got["same"][0][:2]
    for rel, n, text, _ in got["drifted"]:
        sys.stdout.writelines(difflib.unified_diff(
            got["common"].splitlines(keepends=True), text.splitlines(keepends=True),
            f"{at}:{line} (the common version, {len(got['same'])} copies)", f"{rel}:{n}"))  # fmt: skip
    return kernel.ESCALATE


def new(ref: str, root: Path = ROOT) -> int:
    """The copies that drifted since REF and don't say why, as Markdown."""
    then = sources_at(ref, root)
    if then is None:
        print(f"refused: git doesn't know {ref}", file=sys.stderr)
        return kernel.REFUSED
    before = set()
    for name, found in functions(root, then).items():
        got = drift(found)
        before |= {(name, c[0]) for c in (got["drifted"] if got else [])}
    out = []
    for name, found in sorted(functions(root).items()):
        got = drift(found)
        for rel, n, text, why in got["drifted"] if got else []:
            if why or (name, rel) in before:
                continue
            at, line = got["same"][0][:2]
            patch = "".join(difflib.unified_diff(
                got["common"].splitlines(keepends=True), text.splitlines(keepends=True),
                f"{at}:{line}", f"{rel}:{n}"))  # fmt: skip
            out.append(f"- `{name}` in `{rel}:{n}` differs from the {len(got['same'])} copies"
                       f" the others keep, as `{at}` has it:\n\n```diff\n{patch}```\n")  # fmt: skip
    print("### Copies that drifted in this pull request\n")
    if out:
        print("A function more add-ons keep the same now differs here, and doesn't say why."
              " If it's on purpose, say so above its def (`# differs on purpose: ...`);"
              " if not, it may be the fix the other copies need, or a copy to bring back.\n")  # fmt: skip
        print("\n".join(out))
    else:
        print(
            "None: every copy this pull request leaves drifted was drifted already, or says why."
        )
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    if argv == ["survey"]:
        doc, code = survey()
        say(doc, as_json)
        return code
    if len(argv) == 2 and argv[0] == "diff" and not as_json and argv[1].isidentifier():
        return diff(argv[1])
    if len(argv) == 3 and argv[:2] == ["new", "--base"] and not as_json and argv[2]:
        return new(argv[2])
    print(USAGE, file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
