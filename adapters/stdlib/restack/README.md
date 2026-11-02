<!-- willow-addon
section: For maintainers
line: Main merged into your branches, with the conflicts in the files the repo makes or only adds to settled by its own tools, and every other one left to you.
source: new
added: 2026-10-24
writes: nothing
network: none
tags: git
-->
# restack

When main moves, every branch waiting to merge conflicts in the same few
files: the add-on list, the changelog, the file tree. This merges REF into
each one, settling those by the rules the repo already follows, and stops on
anything else.

    python adapters/stdlib/restack/restack.py --onto REF BRANCH [BRANCH ...]

    claude/addon-timeline: deb56e83 -> cf502d3c, origin/main merged in; settled CHANGELOG.md
      push: git push origin claude/addon-timeline

Fetch first (`git fetch origin main`, then `--onto origin/main`): it never
goes online.

**What it settles, and how.** REF is merged into each branch in a scratch
worktree of its own, never in your checkout, as one merge commit. When the
merge conflicts:

| File | Settled as |
|---|---|
| ADDONS.md, README.md | REF's, then made again by `adapters/stdlib/readme/readme.py write` |
| BUGS.md | REF's, then made again by `adapters/stdlib/ci/bugs.py write` |
| CHANGELOG.md | under `## Unreleased`, the branch's entries above REF's |
| FILES.md | both sides' folders, A to Z |
| test_contract.py | both sides' `COMMANDS` lines |
| adapters/planned.json | REF's ideas, less the ones the branch built, plus any it added |

These are the files every add-on's pull request touches and that main's
own changes touch too. **Any other conflict stops that branch** and leaves it
exactly as it was, saying which file: two sides changing the same code is a
person's call. A conflict in one of these files that doesn't fit its rule
(a changelog conflict outside Unreleased, a tree entry both sides changed)
stops it too.

**Nothing moves until it checks.** After the merge, `test_docs.py` runs in
the scratch worktree; it is the check that catches a merge settled wrong. Only
when it passes is the branch moved to the new commit. If the branch is checked
out somewhere, that checkout is moved with it, and only when it has no changes
of yours, committed or not. Nothing is pushed: it prints the push, a plain
one, since nothing of the branch is rewritten.

**Any branch, yours or shared.** A merge keeps every commit the branch had,
so a checkout of it elsewhere stays valid, and the push needs no force. It
is how this repo merges, too.

**What it writes.** Its own code writes only inside the scratch worktree it
makes. Git moves the branch, and the checkout when it has one; the card's
`writes: nothing` can't say that, so this does.

**What it can't see.** `test_docs.py` passing means the docs and the trees are
right, not that the branch's tests still pass on top of the new main. Run
those after, or the full CI run. And the guard that holds every add-on to its
card judges code inside this repo: its tests run restack on a copy of the
repo in a scratch folder, which the guard doesn't judge, so it holds the
rules, not the git.

**Exit codes:** 0 every branch moved, or already holds REF; 42 none needed it,
or pytest isn't installed to check; 2 refused, or a branch stopped.

**Uses:** the kernel's exit codes, and `adapters/stdlib/readme/readme.py` and `adapters/stdlib/ci/bugs.py` to make
again what they make.

**Never:** changes your checkout while it has changes of yours, pushes, or
settles a conflict it has no rule for.
