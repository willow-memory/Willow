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
    test_contract.py         both sides' COMMANDS lines
    adapters/planned.json    REF's list, less the ideas the branch built, plus
                             any it added

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


SETTLE = {
    "CHANGELOG.md": changelog,
    "FILES.md": files_tree,
    "adapters/stdlib/ci/test_contract.py": contract,
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


def settle(work: Path) -> list[str]:
    """Settle the merge's conflicts by the rules; the files settled. In a merge
    the branch is ours and REF theirs."""
    names = git("diff", "--name-only", "--diff-filter=U", cwd=work).stdout.split()
    unknown = [
        n
        for n in names
        if n not in MADE and n not in SETTLE and n != "adapters/planned.json"
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
            base, mine, ref = (git("show", f":{i}:{n}", cwd=work).stdout for i in (1, 2, 3))  # fmt: skip
            p.write_text(planned(base, ref, mine), encoding="utf-8")
        else:
            text = swap(p.read_text(encoding="utf-8"))
            p.write_text(SETTLE[n](text), encoding="utf-8")
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
