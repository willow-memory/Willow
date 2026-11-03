"""against: this pull request held to the other open ones.

    python adapters/stdlib/against/against.py check --base REF HEAD OTHER [OTHER ...]

HEAD is this pull request's head, each OTHER another open pull request's head
(any git refs), REF what they branch from (`origin/main`). Run it in the
repository. For each OTHER, from where each of the two left REF
(`git merge-base`), it says:

  duplicate:  a name both add: an add-on folder, an idea on planned.json, a
              `COMMANDS` key, a path in FILES.md. Fails the run (exit 2).
  collides:   a file the two change in ways git cannot merge, other than the
              ones restack settles. A warning; the exit stays 0.
  settled:    the same, in a file restack settles by rule. Said, not warned.
  near:       an idea or add-on yours adds that is near one the other adds,
              by similar.py's search. A suggestion.

Exit codes, the kernel's: 0 nothing duplicated; 2 a duplicate, or a bad command
line; 42 nothing to check (no OTHER, or one that is not a ref or shares no
history with REF: the report says which). It never goes online and writes
nothing: the trial merge's objects go to a scratch folder.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "similar"))
import kernel  # noqa: E402
import similar  # noqa: E402

USAGE = "usage: against.py check --base REF HEAD OTHER [OTHER ...]"
CONTRACT = "adapters/stdlib/ci/test_contract.py"
PLANNED = "adapters/planned.json"
#: the files restack settles by rule when two branches both change them
SETTLED = frozenset({"ADDONS.md", "README.md", "BUGS.md", "CHANGELOG.md", "FILES.md", CONTRACT, PLANNED})  # fmt: skip
CARD = re.compile(r"^adapters/(?:stdlib|deps)/([^/]+)/README\.md$")
BRANCH = re.compile(r"^(?P<lead>(?:│   |    )*)[├└]── (?P<name>\S+)")
PULL = re.compile(r"(?:^|/)(?:pr|pull)/(\d+)(?:/head)?$")


class Unchecked(Exception):
    """A ref that cannot be held to REF; the report says why."""


def git(*argv: str) -> str:
    got = subprocess.run(["git", *argv], capture_output=True, text=True)
    if got.returncode != 0:
        why = got.stderr.strip().splitlines()
        raise Unchecked(why[-1] if why else "git failed")
    return got.stdout


def commit(ref: str) -> str | None:
    got = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
                         capture_output=True, text=True)  # fmt: skip
    return got.stdout.strip() if got.returncode == 0 else None


def left(ref: str, rev: str) -> str:
    """Where `rev` left `ref`: their merge base."""
    got = subprocess.run(
        ["git", "merge-base", ref, rev], capture_output=True, text=True
    )
    if got.returncode != 0:
        why = got.stderr.strip().splitlines()
        raise Unchecked(why[-1] if why else "shares no history with the base")
    return got.stdout.strip()


def label(ref: str) -> str:
    """`#12` for a pull request's ref (`pr/12`, `refs/pull/12/head`), else the ref."""
    m = PULL.search(ref)
    return f"#{m[1]}" if m else ref


def show(rev: str, path: str) -> str | None:
    got = subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True,
                         text=True)  # fmt: skip
    return got.stdout if got.returncode == 0 else None


def card_line(text: str) -> str:
    """The `line:` of a card's header (`<!-- willow-addon ... -->`), if it has one."""
    if not text.startswith("<!-- willow-addon"):
        return ""
    for line in text.split("-->")[0].splitlines():
        if line.startswith("line:"):
            return line.split(":", 1)[1].strip()
    return ""


def planned_at(rev: str) -> dict[str, str]:
    text = show(rev, PLANNED)
    try:
        return {e["name"]: e.get("line", "") for e in json.loads(text)} if text else {}
    except (ValueError, KeyError, TypeError):
        return {}


def command_keys(text: str) -> set[str]:
    """The keys of `COMMANDS` in test_contract.py's text, read with `ast`."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()
    for node in tree.body:
        if isinstance(node, ast.AnnAssign):
            target = node.target
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
        else:
            continue
        if getattr(target, "id", "") == "COMMANDS" and isinstance(node.value, ast.Dict):
            return {k.value for k in node.value.keys
                    if isinstance(k, ast.Constant) and isinstance(k.value, str)}  # fmt: skip
    return set()


def tree_paths_of(text: str) -> set[str]:
    """Every path FILES.md's tree names, from the nesting."""
    out, stack = set(), []
    for line in text.splitlines():
        m = BRANCH.match(line)
        if not m:
            continue
        del stack[len(m["lead"]) // 4 :]
        stack.append(m["name"].rstrip("/"))
        out.add("/".join(stack))
    return out


class Adds:
    """What one pull request introduces, against where it left REF."""

    def __init__(self, ref: str, base: str):
        self.addons: dict[str, str] = {}  # name -> its card's line
        diff = git("diff", "--name-status", "--no-renames", "-z", base, ref,
                   "--", "adapters/stdlib", "adapters/deps").split("\0")  # fmt: skip
        for status, path in zip(diff[0::2], diff[1::2]):
            m = CARD.match(path)
            if status == "A" and m:
                self.addons[m[1]] = card_line(show(ref, path) or "")
        before = planned_at(base)
        self.ideas = {n: line for n, line in planned_at(ref).items() if n not in before}
        at = lambda rev, path: show(rev, path) or ""  # noqa: E731
        self.commands = command_keys(at(ref, CONTRACT)) - command_keys(
            at(base, CONTRACT)
        )
        self.paths = tree_paths_of(at(ref, "FILES.md")) - tree_paths_of(
            at(base, "FILES.md")
        )

    def without(self, shared: "Adds") -> "Adds":
        """These additions less the ones `shared` holds too: what the two pull
        requests brought in together, before they parted, is nobody's
        duplicate."""
        out = Adds.__new__(Adds)
        out.addons = {n: v for n, v in self.addons.items() if n not in shared.addons}
        out.ideas = {n: v for n, v in self.ideas.items() if n not in shared.ideas}
        out.commands = self.commands - shared.commands
        out.paths = self.paths - shared.paths
        return out

    def names(self) -> dict[str, tuple[str, str]]:
        """name -> (what it is, its line); an add-on beats an idea of its name."""
        out = {n: ("idea", line) for n, line in self.ideas.items()}
        out.update({n: ("add-on", line) for n, line in self.addons.items()})
        return out


def duplicates(mine: Adds, theirs: Adds, who: str) -> list[str]:
    out, a, b = [], mine.names(), theirs.names()
    both = sorted(set(a) & set(b))
    for name in both:
        kind = (
            a[name][0] if a[name][0] == b[name][0] else f"{a[name][0]} / {b[name][0]}"
        )
        out.append(f"duplicate: both add {kind} {name} ({who})")
    for key in sorted(mine.commands & theirs.commands):
        out.append(f"duplicate: both add COMMANDS key {key} ({who})")
    # FILES.md: the top of a shared path, unless its add-on's folder is said already
    shared = mine.paths & theirs.paths
    for path in sorted(shared):
        parts = path.split("/")
        said = parts[:2] in (["adapters", "stdlib"], ["adapters", "deps"]) and parts[2:3] and parts[2] in both  # fmt: skip
        if not said and path.rpartition("/")[0] not in shared:
            out.append(f"duplicate: both add {path} to FILES.md ({who})")
    return out


def merge_conflicts(mine: str, other: str) -> list[str]:
    """The paths a trial merge of the two conflicts in. The merge's objects go to
    a scratch folder, with the repository's own beside them to read."""
    real = git("rev-parse", "--path-format=absolute", "--git-path", "objects").strip()
    with tempfile.TemporaryDirectory() as scratch:
        env = {**os.environ, "GIT_OBJECT_DIRECTORY": scratch,
               "GIT_ALTERNATE_OBJECT_DIRECTORIES": real}  # fmt: skip
        got = subprocess.run(
            ["git", "merge-tree", "--write-tree", "--name-only", "--no-messages", "-z", mine, other],
            capture_output=True, text=True, env=env)  # fmt: skip
    if got.returncode == 0:
        return []
    if got.returncode != 1:
        why = got.stderr.strip().splitlines()
        raise Unchecked(why[-1] if why else "git merge-tree failed")
    return sorted({p for p in got.stdout.split("\0")[1:] if p})


def collisions(mine: str, other: str, who: str) -> list[str]:
    out = []
    for path in merge_conflicts(mine, other):
        if path in SETTLED:
            out.append(f"settled: {path} with {who}; restack settles it")
        else:
            out.append(
                f"collides: {path} with {who}; merge its branch first and base on it"
            )
    return out


def nears(mine: Adds, theirs: Adds, who: str) -> list[str]:
    """Each thing yours adds that the search over what theirs adds finds near."""
    pile = [{"name": n, "line": line, "built": False, "path": n}
            for n, (_, line) in sorted(theirs.names().items())]  # fmt: skip
    out = []
    for name, (kind, line) in sorted(mine.names().items()):
        if name in theirs.names():
            continue  # a duplicate, said
        for found, _ in similar.near(pile, f"{name.replace('-', ' ')}. {line}"):
            out.append(f"near: your {kind} {name} is near {who}'s {found['name']}")
    return out


def check(base: str, head: str, others: list[str]) -> tuple[int, list[str]]:
    ref, mine = commit(base), commit(head)
    if not ref or not mine:
        raise Unchecked(f"{base if not ref else head} is not a ref")
    mine_adds = Adds(mine, left(ref, mine))
    lines, done, skipped = [], [], []
    tally = {"duplicate": 0, "collides": 0, "near": 0}
    for other in others:
        who = label(other)
        sha = commit(other)
        try:
            if not sha:
                raise Unchecked("not a ref")
            there = Adds(sha, left(ref, sha))
            # one stacked on the other: what they share from before they
            # parted (the base's additions, carried by both) is no duplicate
            parted = left(mine, sha)
            shared = Adds(parted, left(ref, parted))
            found = (duplicates(mine_adds.without(shared), there.without(shared), who)
                     + collisions(mine, sha, who) + nears(mine_adds, there, who))  # fmt: skip
        except Unchecked as why:
            skipped.append(f"not checked: {who}: {why}")
            continue
        lines += found
        done.append(f"checked: {who} {sha[:7]}")
        for kind in tally:
            tally[kind] += sum(x.startswith(f"{kind}:") for x in found)
    lines += done + skipped
    lines.append(f"{len(done)} checked, {tally['duplicate']} duplicated, {tally['collides']}"
                 f" collided, {tally['near']} near, {len(skipped)} not checked")  # fmt: skip
    if tally["duplicate"]:
        return kernel.REFUSED, lines
    return (kernel.ESCALATE if skipped else kernel.ALIVE), lines


def main(argv: list[str]) -> int:
    args = argv[1:]
    if (argv[:1] != ["check"] or len(args) < 3 or args[0] != "--base"
            or any(a.startswith("-") for a in args[1:])):  # fmt: skip
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    base, head, others = args[1], args[2], list(dict.fromkeys(args[3:]))
    if not others:
        print("nothing to check: no other pull request given")
        return kernel.ESCALATE
    try:
        code, lines = check(base, head, others)
    except Unchecked as why:
        print(f"against.py: {why}", file=sys.stderr)
        return kernel.REFUSED
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
