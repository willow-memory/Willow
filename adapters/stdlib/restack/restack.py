"""restack.py: main brought into your branches, with the conflicts this repo
knows how to settle settled by its own tools, and nothing else guessed.

    python adapters/stdlib/restack/restack.py --onto REF BRANCH [BRANCH ...]

REF is merged into each BRANCH (fetch it first: `git fetch origin main`,
then `--onto origin/main`) in a scratch worktree of its own, never in your
checkout, as one merge commit: nothing of the branch is rewritten, so
another session on the same branch keeps a checkout that still holds, and
the push is a plain one. When the merge conflicts, the files this repo makes
or only adds lines to are settled by a rule; any other conflict stops that
branch, and it is left exactly as it was:

    ADDONS.md, README.md     REF's, then made again: readme.py write
    BUGS.md                  REF's, then made again: ci/bugs.py write
    CHANGELOG.md             under ## Unreleased, the branch's entries above
                             REF's, newest first
    FILES.md                 both sides' folders, A to Z
    test_contract.py         both sides' COMMANDS lines; or, when a conflict
                             is more than those, the entries either side
                             added to COMMANDS, READERS or PILE_EXTRA, with
                             imports, whole (read with ast, from the base and
                             both sides: a branch that changed anything else
                             stops)
    adapters/planned.json    REF's list, less the ideas the branch built, plus
                             any it added
    any other .md file       both sides' lines, REF's first, when each side
                             only added lines where the base had none (a
                             paragraph each on an add-on's card); a side
                             that changed a line the base had stops

Once REF is merged in, test_docs.py runs in the scratch worktree: it is
the check that catches a merge settled wrong (a tree missing a file, a
count that is off). Only when it passes is the branch moved, forward, to the
merge commit; if the branch is checked out somewhere, that checkout is moved
too, and only when it has no changes of yours. Nothing is pushed: it says
the push to make.

Exit codes, the kernel's: 0 every branch moved, or already holds REF; 42 none
needed it, or pytest isn't installed to check; 2 refused, or a branch
stopped on a conflict it has no rule for, or failed its check.
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
USAGE = "usage: restack.py --onto REF BRANCH [BRANCH ...]"
HUNK = re.compile(
    r"<<<<<<< [^\n]*\n(.*?)(?:\|\|\|\|\|\|\| [^\n]*\n.*?)?=======\n(.*?)>>>>>>> [^\n]*\n",
    re.S,
)
MADE = {
    "ADDONS.md": "adapters/stdlib/readme/readme.py",
    "README.md": "adapters/stdlib/readme/readme.py",
    "BUGS.md": "adapters/stdlib/ci/bugs.py",
}
ENTRY = re.compile(r'^\s+(?:"[\w-]+": \(|\*\*\{)')  # a COMMANDS line
CONTRACT = "adapters/stdlib/ci/test_contract.py"
DICTS = ("COMMANDS", "READERS", "PILE_EXTRA")  # test_contract.py's, added to by add-ons
BRANCH = re.compile(r"^(?P<lead>[│ ]*)[├└]── (?P<name>\S+)")


class Stop(Exception):
    """A conflict with no rule: the branch is left as it was."""


# ── the rules: text in, text out, nothing written ────────────────────────────
def hunks(text: str, combine) -> str:
    """Each conflict in `text` settled by `combine(ref_side, branch_side, rest)`,
    `rest` being the text after it. The first side is REF's, the second the
    branch's (`swap` puts a merge's sides in that order)."""
    out, at = [], 0
    for m in HUNK.finditer(text):
        out += [text[at : m.start()], combine(m.group(1), m.group(2), text[m.end() :])]
        at = m.end()
    if not out:
        raise Stop("a conflict this can't read")
    return "".join(out) + text[at:]


def changelog(text: str) -> str:
    """The branch's entries above REF's, inside ## Unreleased only."""
    top = text.find("## Unreleased")
    end = text.find("\n## ", top + 1) if top >= 0 else -1

    def combine(ref, mine, rest):
        at = len(text) - len(rest)
        if top < 0 or at < top or (end >= 0 and at > end):
            raise Stop("CHANGELOG.md conflicts outside ## Unreleased")
        return mine + ref

    return hunks(text, combine)


def groups(side: str, lead: str) -> list[tuple[str, list[str]]]:
    """A side of FILES.md's tree as (name, its lines), one per entry at `lead`."""
    out: list[tuple[str, list[str]]] = []
    for line in side.splitlines(keepends=True):
        m = BRANCH.match(line)
        if m and m["lead"] == lead:
            out.append((m["name"], [line]))
        elif out and m and len(m["lead"]) > len(lead):
            out[-1][1].append(line)
        else:
            raise Stop("FILES.md conflicts in a way that isn't two sets of entries")
    return out


def files_tree(text: str) -> str:
    """Both sides' entries, A to Z. Each side's last entry may be open: its
    closing lines are shared, after the conflict, and go to the last one."""

    def combine(ref, mine, rest):
        first = BRANCH.match((ref or mine).splitlines()[0]) if (ref or mine) else None
        if first is None:
            raise Stop("FILES.md conflicts in a way that isn't two sets of entries")
        lead = first["lead"]
        both = dict(groups(ref, lead))
        for name, lines in groups(mine, lead):
            if name in both and both[name] != lines:
                raise Stop(f"FILES.md: both sides changed {name}")
            both[name] = lines
        tail = []
        for line in rest.splitlines(keepends=True):
            m = BRANCH.match(line)
            if not m or len(m["lead"]) <= len(lead):
                break
            tail.append(line)
        last = {groups(s, lead)[-1][0] for s in (ref, mine) if s.strip()}
        order = sorted(both, key=lambda n: n.rstrip("/").lower())
        out = []
        for name in order:
            out += both[name]
            if tail and name in last and name != order[-1]:
                out += tail  # an open entry, closed here as it is after the conflict
        return "".join(out)

    return hunks(text, combine)


def contract(text: str) -> str:
    """Both sides' COMMANDS lines, REF's first."""

    def combine(ref, mine, rest):
        lines = ref.splitlines(keepends=True) + mine.splitlines(keepends=True)
        if not lines or not all(ENTRY.match(x) for x in lines):
            raise Stop("test_contract.py conflicts outside COMMANDS' lines")
        return "".join(dict.fromkeys(lines))

    return hunks(text, combine)


def parsed(text: str, side: str) -> ast.Module:
    try:
        return ast.parse(text)
    except SyntaxError as e:
        raise Stop(f"test_contract.py doesn't parse {side}: {e.msg}") from e


def tables(tree: ast.Module) -> dict[str, ast.Dict]:
    """test_contract.py's module-level dicts an add-on adds to, by name."""
    out = {}
    for node in tree.body:
        if isinstance(node, ast.AnnAssign):
            target = node.target
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
        else:
            continue
        if isinstance(node.value, ast.Dict) and getattr(target, "id", "") in DICTS:
            out[target.id] = node.value
    return out


def keyed(text: str, table: ast.Dict) -> dict[str, ast.expr]:
    """A dict's entries by their key's source; a `**{...}` splat has none."""
    pairs = zip(table.keys, table.values)
    return {ast.get_source_segment(text, k): v for k, v in pairs if k is not None}


def comma(line: str, col: int) -> str:
    """`line` with a comma after its value, which ends at byte `col`, if it
    has none: an entry moved to the end of a dict must not be the last bare."""
    raw = line.encode("utf-8")
    if raw[col:].lstrip().startswith(b","):
        return line
    return (raw[:col] + b"," + raw[col:]).decode("utf-8")


def contract_entries(base: str, ref: str, mine: str) -> str:
    """REF's test_contract.py, plus the entries the branch added to COMMANDS,
    READERS or PILE_EXTRA, each whole at the end of its dict, and the imports
    it added. Two reader branches always conflict there with neither side
    holding a whole entry, so no rule on lines can settle it; this reads the
    three files instead. A branch that changed anything else stops."""
    b_tree, r_tree, m_tree = (parsed(text, side) for text, side in
                              ((base, "at the base"), (ref, "on REF"), (mine, "on the branch")))  # fmt: skip
    lines = mine.splitlines(keepends=True)
    kept = [True] * len(lines)  # the branch's lines, less what it added
    adds: dict[str, list[tuple[str, ast.expr, str]]] = {}
    b_tables, r_tables = tables(b_tree), tables(r_tree)
    for name, table in tables(m_tree).items():
        old = keyed(base, b_tables[name]) if name in b_tables else {}
        pairs = list(zip(table.keys, table.values))
        for i, (k, v) in enumerate(pairs):
            key = None if k is None else ast.get_source_segment(mine, k)
            if key is None or key in old:
                continue
            nxt = (pairs[i + 1][0] or pairs[i + 1][1]) if i + 1 < len(pairs) else None
            stop = nxt.lineno if nxt is not None else table.end_lineno
            before = pairs[i - 1][1].end_lineno if i else table.lineno
            if k.lineno <= before or v.end_lineno >= stop:
                raise Stop(f"test_contract.py: {name}'s {key} shares a line")
            first = k.lineno - 1  # 0-based, as `lines` is
            while first > before and lines[first - 1].lstrip().startswith("#"):
                first -= 1  # the comment written over it goes with it
            entry = lines[first : v.end_lineno]
            entry[-1] = comma(entry[-1], v.end_col_offset)
            kept[first : v.end_lineno] = [False] * (v.end_lineno - first)
            adds.setdefault(name, []).append((key, v, "".join(entry)))
    b_imports = {ast.get_source_segment(base, n) for n in b_tree.body
                 if isinstance(n, (ast.Import, ast.ImportFrom))}  # fmt: skip
    imports = []
    for n in m_tree.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)) and ast.get_source_segment(mine, n) not in b_imports:  # fmt: skip
            imports.append("".join(lines[n.lineno - 1 : n.end_lineno]))
            kept[n.lineno - 1 : n.end_lineno] = [False] * (n.end_lineno - n.lineno + 1)  # fmt: skip
    rest, was = [x for x, k in zip(lines, kept) if k], base.splitlines(keepends=True)
    if rest != was:
        at = next((i for i, (x, y) in enumerate(zip(rest, was)) if x != y),
                  min(len(rest), len(was)))  # fmt: skip
        raise Stop(
            f"test_contract.py: the branch changes its line {at + 1} at the base, "
            "not only adds entries; settle it by hand"
        )
    out = ref.splitlines(keepends=True)
    for name in adds:
        if name not in r_tables:
            raise Stop(f"test_contract.py: REF has no {name} to add to")
    for name in sorted(adds, key=lambda n: -r_tables[n].end_lineno):  # bottom first
        table, have = r_tables[name], keyed(ref, r_tables[name])
        close = table.end_lineno - 1  # 0-based: the line of the closing brace
        last = table.values[-1] if table.values else None
        if last is None or last.end_lineno > close or not out[close].lstrip().startswith("}"):  # fmt: skip
            raise Stop(f"test_contract.py: REF's {name} doesn't close on a line of its own")  # fmt: skip
        new = []
        for key, value, entry in adds[name]:
            if key not in have:
                new.append(entry)
            elif ast.dump(have[key]) != ast.dump(value):
                raise Stop(f"test_contract.py: both sides added {key} to {name}, differently")  # fmt: skip
        if new:
            out[last.end_lineno - 1] = comma(out[last.end_lineno - 1], last.end_col_offset)  # fmt: skip
            out[close:close] = new
    r_imports = [n for n in r_tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    have_imports = {"".join(out[n.lineno - 1 : n.end_lineno]) for n in r_imports}
    new = [x for x in dict.fromkeys(imports) if x not in have_imports]
    if new:
        if not r_imports:
            raise Stop("test_contract.py: REF has no import to put the branch's after")
        out[r_imports[-1].end_lineno : r_imports[-1].end_lineno] = new
    text = "".join(out)
    parsed(text, "once settled")
    return text


def planned(base: str, ref: str, mine: str) -> str:
    """REF's ideas, less those the branch took off the list (built), plus those
    it put on; in REF's order, the new ones after, as the file is written."""
    try:
        b, r, m = (json.loads(x) for x in (base, ref, mine))
    except ValueError as e:
        raise Stop(f"adapters/planned.json isn't JSON on one side: {e}") from e
    names = lambda xs: {x["name"] for x in xs}  # noqa: E731
    gone, added = names(b) - names(m), [x for x in m if x["name"] not in names(b)]
    out = [x for x in r if x["name"] not in gone]
    out += [x for x in added if x["name"] not in names(out)]
    return json.dumps(out, indent=1, ensure_ascii=False) + "\n"


DIFF3 = re.compile(
    r"<<<<<<< [^\n]*\n(.*?)\|\|\|\|\|\|\| [^\n]*\n(.*?)=======\n(.*?)>>>>>>> [^\n]*\n",
    re.S,
)


def added_both(name: str, base: str, ref: str, mine: str) -> str:
    """A Markdown file where both sides only added lines at the same place:
    REF's lines, then the branch's, a blank line between them when what
    follows is a blank line (paragraphs, not a list). Stops on any conflict
    where the base had lines there."""
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for side, text in (("ref", ref), ("base", base), ("mine", mine)):
            path = Path(tmp) / side
            path.write_text(text, encoding="utf-8")
            paths.append(str(path))
        merged = subprocess.run(["git", "merge-file", "-p", "--diff3", *paths],
                                capture_output=True, text=True).stdout  # fmt: skip
    out, at = [], 0
    for m in DIFF3.finditer(merged):
        theirs, was, ours = m.group(1), m.group(2), m.group(3)
        if was.strip():
            raise Stop(f"{name}: a side changed lines the base had; settle it by hand")
        rest = merged[m.end() :]
        gap = "\n" if rest.startswith("\n") and not theirs.endswith("\n\n") else ""
        out += [merged[at : m.start()], theirs + gap + ours]
        at = m.end()
    if not out:
        raise Stop(f"{name}: a conflict this can't read")
    return "".join(out) + merged[at:]


SETTLE = {
    "CHANGELOG.md": changelog,
    "FILES.md": files_tree,
    CONTRACT: contract,
}


# ── git, in a scratch worktree ───────────────────────────────────────────────
def git(*argv: str, cwd: Path = ROOT, ok=(0,)) -> subprocess.CompletedProcess:
    got = subprocess.run(["git", *argv], cwd=cwd, capture_output=True, text=True,
                         env={**os.environ, "GIT_EDITOR": "true"})  # fmt: skip
    if got.returncode not in ok:
        raise Stop(
            f"git {' '.join(argv[:2])}: {(got.stderr or got.stdout).strip()[:300]}"
        )
    return got


def sha(ref: str, cwd: Path = ROOT) -> str:
    """The commit `ref` names, or "" when git knows no such commit."""
    got = git(
        "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", cwd=cwd, ok=(0, 1, 128)
    )
    return got.stdout.strip() if got.returncode == 0 else ""


def swap(text: str) -> str:
    """In a merge the branch's side comes first; the rules take REF's first."""
    return HUNK.sub(
        lambda m: f"<<<<<<< REF\n{m.group(2)}=======\n{m.group(1)}>>>>>>> branch\n",
        text,
    )


def stages(work: Path, name: str) -> tuple[str, str, str]:
    """A conflicted file at the base, on REF and on the branch. In a merge the
    branch is ours (stage 2) and REF theirs (stage 3)."""
    base, mine, ref = (git("show", f":{i}:{name}", cwd=work).stdout for i in (1, 2, 3))  # fmt: skip
    return base, ref, mine


def settle(work: Path) -> list[str]:
    """Settle the merge's conflicts by the rules; the files settled. In a merge
    the branch is ours and REF theirs."""
    names = git("diff", "--name-only", "--diff-filter=U", cwd=work).stdout.split()
    unknown = [
        n
        for n in names
        if n not in MADE
        and n not in SETTLE
        and n != "adapters/planned.json"
        and not n.endswith(".md")
    ]
    if unknown:
        raise Stop(
            f"a conflict with no rule, in {', '.join(unknown)}; settle it by hand"
        )
    for n in names:
        p = work / n
        if n in MADE:
            git("checkout", "--theirs", "--", n, cwd=work)
        elif n == "adapters/planned.json":
            p.write_text(planned(*stages(work, n)), encoding="utf-8")
        elif n == CONTRACT:
            text = swap(p.read_text(encoding="utf-8"))
            try:  # both sides' COMMANDS lines, when that is all they are
                text = contract(text)
                parsed(text, "once its lines are settled")
            except Stop:  # else what each side added, each entry read whole
                text = contract_entries(*stages(work, n))
            p.write_text(text, encoding="utf-8")
        elif n in SETTLE:
            text = swap(p.read_text(encoding="utf-8"))
            p.write_text(SETTLE[n](text), encoding="utf-8")
        else:
            p.write_text(added_both(n, *stages(work, n)), encoding="utf-8")
    return names


def remake(work: Path) -> None:
    """The files the repo makes, made again from the cards and the tests."""
    for script in dict.fromkeys(MADE.values()):
        got = subprocess.run([sys.executable, script, "write"], cwd=work,
                             capture_output=True, text=True)  # fmt: skip
        if got.returncode != 0:
            raise Stop(f"{script} write: {(got.stderr or got.stdout).strip()[:300]}")


def checkouts() -> dict[str, Path]:
    """Each branch checked out somewhere: its worktree."""
    out, path = {}, None
    for line in git("worktree", "list", "--porcelain").stdout.splitlines():
        if line.startswith("worktree "):
            path = Path(line[9:])
        elif line.startswith("branch refs/heads/") and path is not None:
            out[line[18:]] = path
    return out


def restack(branch: str, onto: str) -> tuple[int, list[str]]:
    old, base = sha(branch), sha(onto)
    if not old or not base:
        raise Stop(f"git doesn't know {branch if not old else onto}")
    if git("merge-base", "--is-ancestor", base, old, ok=(0, 1)).returncode == 0:
        return kernel.ESCALATE, [f"{branch}: already holds {onto}"]
    there = checkouts().get(branch)
    if there is not None and git("status", "--porcelain", cwd=there).stdout.strip():
        raise Stop(
            f"{there} has it checked out, with changes of yours; commit or put them away first"
        )
    scratch = Path(tempfile.mkdtemp(prefix="restack-"))
    work = scratch / "work"
    git("worktree", "add", "--detach", str(work), old)
    try:
        settled: list[str] = []
        step = git(
            "merge",
            "--no-ff",
            "-m",
            f"Merge {onto} into {branch}",
            base,
            cwd=work,
            ok=(0, 1),
        )
        if step.returncode != 0:
            if not git(
                "diff", "--name-only", "--diff-filter=U", cwd=work
            ).stdout.strip():
                raise Stop(
                    f"merge stopped without a conflict: {step.stdout.strip()[-300:]}"
                )
            settled += settle(work)
            remake(work)
            git("add", "-A", cwd=work)
            git("commit", "-q", "--no-edit", cwd=work)
        remake(work)
        if git("status", "--porcelain", cwd=work).stdout.strip():
            git("add", "-A", cwd=work)
            git("commit", "-q", "--amend", "--no-edit", cwd=work)
            settled.append("the made files, made again")  # the merge commit is new
        check = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                                "test_docs.py"], cwd=work, capture_output=True, text=True)  # fmt: skip
        if check.returncode != 0:
            said = (check.stdout.strip().splitlines() or ["no output"])[-1]
            if "No module named pytest" in check.stderr:
                return kernel.ESCALATE, [f"{branch}: merged, not moved: pytest isn't installed to check it"]  # fmt: skip
            raise Stop(f"merged, but test_docs.py fails ({said}); not moved")
        new = sha("HEAD", cwd=work)
    except Stop:
        git("merge", "--abort", cwd=work, ok=(0, 1, 128))
        raise
    finally:
        git("worktree", "remove", "--force", str(work), ok=(0, 128))
        shutil.rmtree(scratch, ignore_errors=True)
    if there is not None:  # clean when asked; --ff-only refuses anything but forward
        git("merge", "-q", "--ff-only", new, cwd=there)
    else:  # new holds old, so this only moves it forward
        git("update-ref", f"refs/heads/{branch}", new, old)
    said = f"; settled {', '.join(dict.fromkeys(settled))}" if settled else ""
    return kernel.ALIVE, [
        f"{branch}: {old[:8]} -> {new[:8]}, {onto} merged in{said}",
        f"  push: git push origin {branch}",
    ]


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[0] != "--onto" or any(a.startswith("-") for a in argv[2:]):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    onto, codes = argv[1], []
    for branch in dict.fromkeys(argv[2:]):
        try:
            code, lines = restack(branch, onto)
        except Stop as why:
            code, lines = kernel.REFUSED, [f"{branch}: stopped, left as it was: {why}"]
        codes.append(code)
        print("\n".join(lines), flush=True)
    if kernel.REFUSED in codes:
        return kernel.REFUSED
    return kernel.ALIVE if kernel.ALIVE in codes else kernel.ESCALATE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
