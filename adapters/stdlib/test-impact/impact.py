"""impact.py: which of this repo's checks a change can reach, fast ones first.

    python adapters/stdlib/test-impact/impact.py plan [--base REF [--head REF]] [PATH ...]
    python adapters/stdlib/test-impact/impact.py run  [--base REF [--head REF]] [PATH ...]

The change is the paths git says differ from REF (`--base`; to `--head` when
given, else to the files as they are now, edits and new files included), and
the PATHs on the command line. `--head` must be what is checked out: the
graph and the rules read the files on disk, so another head is refused, never
planned from the wrong files. Git is asked with `git merge-base REF HEAD`
first, so a branch is compared with where it left REF, not with REF's later
commits. A PATH given by hand must exist, or be one git knew at HEAD (a file
you deleted).

`plan` says what would run, in ci.py's own terms (its gate names), and why.
`run` says the plan, then runs it in order and stops at the first gate that
fails. Neither replaces the full run: both end by saying it still runs after,
and how.

How a path is placed:

  - the import graph: every .py file of the repo is parsed with `ast`; an edge
    is an `import`, or a string naming a .py file (`HERE / "stale.py"`, how the
    tests load an add-on's script). A test file that can reach a changed file
    through those edges runs. test_contract.py names every add-on's script, so
    it is left out of the graph and placed by the rules below instead.
  - a few rules for what the graph cannot see:
      add-on folder            its tests; test_contract.py narrowed to it
                               (WILLOW_ONLY=name); its mutants when its code
                               changed; ruff on its changed .py files
      test_contract.py         the whole of it
      any change at all        test_docs.py (FILES.md, README counts, the
                               generated lists, the law's citations);
                               test_docs_fires.py too when a docs test changed
      kernel.py, ruff.toml     everything
      constitution/            its tests and the coverage report
      vectors/                 its tests, and every port
      ports/NAME/              ports:NAME
      demo/NAME/               demo:NAME
      adapters/deps/NAME/      deps:NAME and deps:NAME@floor
      adapters/stdlib/github/, .github/ (not workflows)
                               tests:strip
      *.md, LICENSE, CITATION.cff, adapters/planned.json
                               test_docs.py, which is always there
  - anything else (a workflow, .gitignore, a test file in no gate): it says
    "couldn't place PATH: running everything", and everything is every gate
    of ci.py, in memory, with no record written. It never shrinks silently.

What it leaves to the full run, always: test_strip.py (minutes; named only when
GitHub's files or the strip test changed), the other add-ons' mutants, and
tests that only a change somewhere else could break and no import shows.

Exit codes, the kernel's: 0 a plan printed, or every gate it ran satisfied;
42 nothing changed, or a gate it needed is unreachable here (a tool isn't
installed) and none failed; 2 refused (no change given, a ref git doesn't
know, a path outside the repo), or a gate failed.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

spec = importlib.util.spec_from_file_location("willow_ci", HERE.parent / "ci" / "ci.py")
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)

USAGE = (
    "usage: impact.py plan|run [--base REF [--head REF]] [PATH ...]"
    "  (give --base, a PATH, or both)"
)
STDLIB = "adapters/stdlib/"
CONTRACT = "adapters/stdlib/ci/test_contract.py"
#: the tests of the one gate that has several files and one narrow form
DOCS = ("test_docs.py", "test_docs_fires.py")
EVERYTHING = "everything"
FULL = "python adapters/stdlib/ci/ci.py run --box /tmp/ci-record"


# ── the change ───────────────────────────────────────────────────────────────
class Refused(Exception):
    pass


def git(*argv: str) -> str:
    got = subprocess.run(["git", *argv], cwd=ROOT, capture_output=True, text=True)
    if got.returncode != 0:
        raise Refused(f"git {' '.join(argv[:2])}: {got.stderr.strip()[:200]}")
    return got.stdout


def changed_by_git(base: str, head: str | None) -> list[str]:
    """Paths that differ from `base` (where this branch left it), to `head`, or
    to the files on disk when there is no head. New files are in; so are both
    ends of a rename. The graph and the rules read the files checked out here,
    so a head that isn't HEAD would be planned from the wrong files: an add-on
    only that head has would read as removed, and its tests left out."""
    if head and git("rev-parse", f"{head}^{{commit}}") != git("rev-parse", "HEAD"):
        raise Refused(
            f"--head {head} isn't what is checked out here; the checks are read from"
            f" the files on disk, so plan it from a checkout of {head}"
        )
    start = git("merge-base", base, head or "HEAD").strip()
    names = git(
        "diff", "--name-only", "--no-renames", "-z", start, *([head] if head else [])
    )
    out = set(names.split("\0"))
    if not head:
        out |= set(git("ls-files", "--others", "--exclude-standard", "-z").split("\0"))
    return sorted(n for n in out if n)


def by_hand(arg: str) -> str:
    """A PATH as the repo names it (slashes, relative to the root)."""
    path = Path(arg)
    path = path if path.is_absolute() else Path.cwd() / path
    try:
        rel = Path(os.path.normpath(path)).relative_to(ROOT)
    except ValueError:
        raise Refused(f"{arg} is outside the repo") from None
    rel = rel.as_posix()
    known = subprocess.run(["git", "cat-file", "-e", f"HEAD:{rel}"], cwd=ROOT,
                           capture_output=True).returncode == 0  # fmt: skip
    if not (ROOT / rel).exists() and not known:
        raise Refused(f"{arg} is not a file here, and git never knew it")
    if (ROOT / rel).is_dir():
        raise Refused(f"{arg} is a folder; name the files that changed")
    return rel


# ── the import graph ─────────────────────────────────────────────────────────
STDLIB_NAMES = getattr(sys, "stdlib_module_names", frozenset())


def repo_pythons() -> list[str]:
    """Every .py file git tracks or would, relative to the root, sorted."""
    names = git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    return sorted(
        n for n in names.split("\0") if n.endswith(".py") and (ROOT / n).is_file()
    )


class Graph:
    """`needs[a]` is the set of repo files `a` imports or names; `names[a]` is
    every module name and .py file name it mentions, resolved or not (so a
    file that was deleted is still found by what pointed at it)."""

    def __init__(self, files: list[str]):
        self.files = set(files)
        self.by_name: dict[str, list[str]] = {}
        for f in files:
            self.by_name.setdefault(Path(f).name, []).append(f)
        self.needs: dict[str, set[str]] = {}
        self.names: dict[str, set[str]] = {}
        for f in files:
            self.needs[f], self.names[f] = self.scan(f)
        # test_contract.py names every add-on's script, so a path through it
        # would join them all: it has no edges, and the rules place it
        self.needs[CONTRACT] = set()
        self.users: dict[str, set[str]] = {f: set() for f in files}
        for f, deps in self.needs.items():
            for d in deps:
                self.users[d].add(f)

    def exists(self, *parts: str) -> list[str]:
        """The repo file for a dotted path: a/b.py, or a/b/__init__.py."""
        base = "/".join(parts)
        return [c for c in (f"{base}.py", f"{base}/__init__.py") if c in self.files]

    def module(self, src: str, level: int, mod: str, asked: list[str]) -> set[str]:
        parts = mod.split(".") if mod else []
        here = Path(src).parent
        out: set[str] = set()
        if level:
            up = here
            for _ in range(level - 1):
                up = up.parent
            bases = [up.as_posix()]
        else:
            bases = [""]  # from the root: adapters.stdlib.x
        for b in bases:
            pre = [b] if b not in ("", ".") else []
            out.update(self.exists(*pre, *parts))
            for n in asked:
                out.update(self.exists(*pre, *parts, n))
        if not level and len(parts) == 1:
            # `import x` with a folder put on sys.path: the file's own folder
            # first, else any file by that name (but never a stdlib module's name)
            near = self.exists(
                *([here.as_posix()] if str(here) != "." else []), parts[0]
            )
            if near:
                out.update(near)
            elif parts[0] not in STDLIB_NAMES:
                out.update(self.by_name.get(f"{parts[0]}.py", []))
        return out

    def named(self, src: str, text: str) -> set[str]:
        """The repo files a string like "stale.py" or "ci/ci.py" points at."""
        name = Path(text).name
        if "/" in text:
            return {
                f
                for f in self.by_name.get(name, [])
                if ("/" + f).endswith("/" + text.lstrip("/"))
            }
        near = (Path(src).parent / name).as_posix()
        if near in self.files:
            return {near}
        return set(self.by_name.get(name, []))

    def scan(self, src: str) -> tuple[set[str], set[str]]:
        try:
            tree = ast.parse((ROOT / src).read_text(encoding="utf-8"))
        except (SyntaxError, ValueError, UnicodeDecodeError):
            return set(), set()  # ruff reports a file that doesn't parse
        needs, names = set(), set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    names.add(a.name.split(".")[-1])
                    needs |= self.module(src, 0, a.name, [])
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                asked = [a.name for a in node.names]
                names.update(mod.split(".")[-1:] + asked)
                needs |= self.module(src, node.level, mod, asked)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                text = node.value
                if (
                    text.endswith(".py")
                    and len(text) < 120
                    and not set(" \n\t") & set(text)
                ):
                    names.add(Path(text).stem)
                    needs |= self.named(src, text)
        needs.discard(src)
        return needs, names

    def reach(self, seeds: set[str]) -> set[str]:
        """Every file that, through imports and named files, comes to a seed."""
        out, todo = set(seeds), sorted(seeds)
        while todo:
            f = todo.pop()
            for u in self.users.get(f, ()):
                if u not in out:
                    out.add(u)
                    todo.append(u)
        return out

    def seeds_for(self, path: str) -> set[str]:
        """The graph's start for a changed .py: itself if it is here, and, if it
        is gone, every file that named it."""
        if path in self.files:
            return {path}
        stem = Path(path).stem
        return {f for f, n in self.names.items() if stem in n}


def is_test(path: str) -> bool:
    name = Path(path).name
    return name.startswith("test_") and name.endswith(".py")


# ── the plan ─────────────────────────────────────────────────────────────────
def addon_of(path: str) -> str | None:
    if path.startswith(STDLIB) and path.count("/") >= 3:
        return path.split("/")[2]
    return None


def deps_of(path: str) -> str | None:
    if path.startswith("adapters/deps/") and path.count("/") >= 3:
        return path.split("/")[2]
    return None


def under(path: str, folder: str) -> str | None:
    """NAME for folder/NAME/... (a file straight in `folder` has no name)."""
    if path.startswith(folder) and path.count("/") > folder.count("/"):
        return path[len(folder) :].split("/")[0]
    return None


class Plan:
    """What to run, by ci.py gate, and why. `steps` is built by `make`."""

    def __init__(self, changed: list[str]):
        self.changed = changed
        self.why: dict[str, list[str]] = {p: [] for p in changed}
        self.widen: list[str] = []
        self.lint: list[str] = []
        self.own: set[str] = set()  # test files for tests:adapters
        self.narrow: list[str] = []  # add-ons, for test_contract.py narrowed
        self.contract_whole = False
        self.docs_fire = False
        self.gates: list[str] = []  # whole ci gates, by name
        self.mutants: list[str] = []
        self.dependents: dict[str, list[str]] = {}

    def gate(self, name: str, path: str, why: str) -> None:
        """Whole gate `name`; `path` is the changed path that asked for it, or a
        test the graph reached (which is said once, not under a path)."""
        if name not in self.gates:
            self.gates.append(name)
        if path in self.why:
            self.say(path, why)

    def say(self, path: str, why: str) -> None:
        if why not in self.why[path]:
            self.why[path].append(why)


def place(changed: list[str], graph: Graph) -> Plan:
    plan = Plan(changed)
    stdlib_dirs = {
        p.name for p in (ROOT / "adapters" / "stdlib").iterdir() if p.is_dir()
    }
    targets = set(ci.mutant_targets())
    seeds: set[str] = set()
    for p in changed:
        py = p.endswith(".py")
        if py and (ROOT / p).is_file():
            plan.lint.append(p)
        name = addon_of(p)
        if p == "kernel.py" or p == "ruff.toml":
            plan.widen.append(f"{p} is imported by, or sets the rules for, everything")
            plan.say(p, "everything")
            continue
        if p.startswith(".github/workflows/") or p in (
            ".gitignore", ".gitattributes", ".editorconfig",
        ):  # fmt: skip
            plan.widen.append(f"couldn't place {p}")
            plan.say(p, "couldn't place it")
            continue
        if p == CONTRACT:
            plan.contract_whole = True
            plan.say(p, "test_contract.py, whole")
        if name:
            gone = name not in stdlib_dirs
            if name not in plan.narrow:
                plan.narrow.append(name)
            plan.say(p, f"add-on {name}" + (" (removed)" if gone else ""))
            if not gone:
                folder = ROOT / "adapters" / "stdlib" / name
                plan.own.update(
                    t.relative_to(ROOT).as_posix() for t in folder.rglob("test_*.py")
                )
                plan.own.discard(CONTRACT)  # narrowed below, or whole if it changed
            if py and not is_test(p) and name in targets and name not in plan.mutants:
                plan.mutants.append(name)
        elif dep := deps_of(p):
            plan.gate(f"deps:{dep}", p, f"add-on {dep} (deps)")
            plan.gate(f"deps:{dep}@floor", p, f"add-on {dep} (deps)")
        elif p.startswith("constitution/"):
            plan.gate("tests:constitution", p, "constitution/")
            plan.gate("tests:coverage", p, "constitution/")
        elif p.startswith("vectors/"):
            plan.gate("tests:vectors", p, "vectors/")
            for port in ci.PORTS:
                plan.gate(f"ports:{port}", p, "vectors/")
        elif port := under(p, "ports/"):
            plan.gate(f"ports:{port}", p, f"ports/{port}")
        elif person := under(p, "demo/"):
            if person == "php2shell":
                plan.gate("demo:php2shell", p, "demo/php2shell")
            else:
                plan.gate(f"demo:{person}", p, f"demo/{person}")
        elif p.startswith(".github/"):
            plan.gate("tests:strip", p, ".github/ (strip removes it)")
        elif p in ("test_kernel.py",):
            plan.gate("tests:kernel", p, "its own tests")
        elif p == "test_strip.py":
            plan.gate("tests:strip", p, "its own tests")
        elif p in DOCS:
            plan.docs_fire = True
            plan.say(p, "a docs test")
        elif p.endswith(".md") or p in (
            "LICENSE",
            "CITATION.cff",
            "adapters/planned.json",
        ):
            plan.say(p, "docs")
        else:
            plan.widen.append(f"couldn't place {p}")
            plan.say(p, "couldn't place it")
        if name == "github":
            plan.gate("tests:strip", p, "the strip test removes GitHub's files")
        if py:
            seeds |= graph.seeds_for(p)
    # the graph: every test that comes to a changed file
    reached = graph.reach(seeds)
    for t in sorted(f for f in reached if is_test(f) and f != CONTRACT):
        if t.startswith(STDLIB):
            plan.own.add(t)
        elif t == "test_kernel.py":
            plan.gate("tests:kernel", t, "reached by import")
        elif t in DOCS:
            plan.docs_fire = plan.docs_fire or t == "test_docs_fires.py"
        elif t == "test_strip.py":
            plan.gate("tests:strip", t, "reached by import")
        elif t.startswith("constitution/"):
            plan.gate("tests:constitution", t, "reached by import")
        elif t.startswith("vectors/"):
            plan.gate("tests:vectors", t, "reached by import")
        elif t.startswith("demo/php2shell"):
            plan.gate("demo:php2shell", t, "reached by import")
        elif t.startswith("adapters/deps/"):
            dep = deps_of(t)
            plan.gate(f"deps:{dep}", t, "reached by import")
            plan.gate(f"deps:{dep}@floor", t, "reached by import")
        else:
            plan.widen.append(f"couldn't place the test {t}")
    for p in changed:
        if p.endswith(".py") and not is_test(p):
            users = sorted(
                u
                for u in graph.reach(graph.seeds_for(p))
                if is_test(u) and u != CONTRACT
            )
            plan.dependents[p] = users
    return plan


#: ci.py's gates, in its order, for sorting the plan the way ci would
def steps(plan: Plan, gates: list):
    """[(gate, what, how-to-say-it, callable)] for a plan that is not wide.
    Cheap and close to the change first; the gates ci.py runs whole last.
    `gates` is ci.gates(), asked for once."""
    every = {g: how for _, g, how in gates}
    out = []
    if plan.lint:
        files = sorted(plan.lint)
        for gate, argv in (
            ("lint:check", ("check", *files)),
            ("lint:format", ("format", "--check", *files)),
        ):
            how = ci.command(
                ci.PY, "-m", "ruff", *argv, needs=lambda: ci.missing_module("ruff")
            )
            out.append((gate, f"ruff on {len(files)} changed .py file(s)",
                        " ".join(("ruff", *argv)), how))  # fmt: skip
    for name in plan.narrow:
        out.append(("tests:adapters", f"test_contract.py narrowed to {name}",
                    f"WILLOW_ONLY={name} pytest {CONTRACT}", pytest_under_guard([CONTRACT], name)))  # fmt: skip
    own = sorted(plan.own)
    if own:
        out.append(("tests:adapters", f"{len(own)} test file(s) of the add-ons reached",
                    "pytest " + " ".join(own), pytest_under_guard(own, None)))  # fmt: skip
    if plan.contract_whole:
        out.append(("tests:adapters", "test_contract.py, whole (it changed)",
                    f"pytest {CONTRACT}", pytest_under_guard([CONTRACT], None)))  # fmt: skip
    docs = list(DOCS if plan.docs_fire else DOCS[:1])
    out.append(("tests:docs", "FILES.md, README counts, generated lists, citations"
                + ("; each check shown to fail" if plan.docs_fire else ""),
                "pytest " + " ".join(docs),
                ci.command(*ci.PYTEST, *docs, needs=lambda: ci.missing_module("pytest"))))  # fmt: skip
    order = [g for _, g, _ in gates]
    for gate in sorted(plan.gates, key=lambda g: order.index(g) if g in order else 99):
        if gate in every:
            out.append((gate, "whole gate, as ci.py runs it", f"ci.py run: {gate}", every[gate]))  # fmt: skip
        else:
            out.append((gate, "no such gate in ci.py", "", unreachable_gate(gate)))
    for name in plan.mutants:
        out.append((f"mutants:{name}", "break its code a few ways; its tests must notice",
                    f"mutants.py run {name}", every[f"mutants:{name}"]))  # fmt: skip
    return out


def unreachable_gate(gate: str):
    def how():
        return ci.UNREACHABLE, "", f"ci.py has no gate {gate}"

    return how


def pytest_under_guard(files: list[str], only: str | None):
    """pytest over `files` as tests:adapters runs them: under the guard, failing
    on a breach of a card's promises. `only` is WILLOW_ONLY for test_contract.py."""

    def gate():
        why = ci.missing_module("pytest")
        if why:
            return ci.UNREACHABLE, "", why
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "guard.log"
            env = ci.guarded(log)
            if only is not None:
                env["WILLOW_ONLY"] = only
            code, said = ci.run((*ci.PYTEST, *files), env=env)
            broke = ci.breaches(log)
        if broke:
            return ci.FAILING, said, f"broke its card's promises: {broke}"
        if code != 0:
            return ci.FAILING, said, f"exit {code}"
        return ci.SATISFIED, said, None

    return gate


def show(plan: Plan, source: str, gates: list) -> list[str]:
    lines = [f"{len(plan.changed)} path(s) changed ({source}):"]
    lines += [f"  {p}" for p in plan.changed]
    if plan.widen:
        lines.append("")
        lines += [f"{why}: running everything" for why in plan.widen]
        lines.append(f"  everything = every gate of ci.py ({len(gates)} of them), in memory, no record")  # fmt: skip
        return lines
    lines += ["", "Plan, in ci.py's gate names, cheapest and closest first:"]
    for i, (gate, what, cmd, _) in enumerate(steps(plan, gates), 1):
        lines.append(f"  {i}. {gate}: {what}")
        if cmd:
            lines.append(f"       {cmd}")
    lines += ["", "Why:"]
    for p in plan.changed:
        said = "; ".join(plan.why[p]) or "only by import"
        lines.append(f"  {p}: {said}")
        users = plan.dependents.get(p)
        if users:
            lines.append(f"      reached by {len(users)} test file(s)")
    return lines


def closing(whole: bool) -> list[str]:
    if whole:
        return [
            "",
            "That was every gate of ci.py, with no record. For the record:",
            f"  {FULL}",
        ]
    return [
        "",
        "This does not replace the full run: it still runs after, in CI, and here:",
        f"  {FULL}",
    ]


# ── running it ───────────────────────────────────────────────────────────────
def run_plan(plan: Plan, gates: list) -> int:
    if plan.widen:
        todo = [(g, "", "", how) for _, g, how in gates]
    else:
        todo = steps(plan, gates)
    states: list[tuple[str, str, str | None]] = []
    for i, (gate, what, _cmd, how) in enumerate(todo):
        print(f"\n── {gate}" + (f": {what}" if what else ""), flush=True)
        state, _said, why = how()
        states.append((gate, state, why))
        if state == ci.FAILING:
            states += [(g, "not run", None) for g, *_ in todo[i + 1 :]]
            break
    print()
    for gate, state, why in states:
        print(f"{gate:<22} {state}" + (f"  ({why})" if why else ""))
    return ci.code_of([s for _, s, _ in states if s != "not run"])


def main(argv: list[str]) -> int:
    verb, rest = (argv[0], argv[1:]) if argv else ("", [])
    base = head = None
    paths: list[str] = []
    it = iter(rest)
    for a in it:
        if a in ("--base", "--head"):
            value = next(it, "")
            if not value or value.startswith("-"):
                print(USAGE, file=sys.stderr)
                return kernel.REFUSED
            if a == "--base":
                base = value
            else:
                head = value
        elif a.startswith("-"):
            print(USAGE, file=sys.stderr)
            return kernel.REFUSED
        else:
            paths.append(a)
    if verb not in ("plan", "run") or (head and not base) or not (base or paths):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    try:
        changed = set(by_hand(p) for p in paths)
        if base:
            changed |= set(changed_by_git(base, head))
        plan = place(sorted(changed), Graph(repo_pythons())) if changed else None
    except Refused as why:
        print(f"refused: {why}", file=sys.stderr)
        return kernel.REFUSED
    source = " and ".join(
        s for s in ((f"git diff from {base}" + (f" to {head}" if head else " to now")) if base else "",
                    f"{len(paths)} by hand" if paths else "") if s)  # fmt: skip
    if not changed:
        print(f"nothing changed ({source}): nothing to run")
        print(*closing(False), sep="\n")
        return kernel.ESCALATE
    gates = ci.gates()
    print(*show(plan, source, gates), sep="\n")
    code = kernel.ALIVE
    if verb == "run":
        code = run_plan(plan, gates)
    print(*closing(bool(plan.widen) and verb == "run"), sep="\n")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
