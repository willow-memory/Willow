<!-- willow-addon
section: For maintainers
line: Main merged into your branches, conflicts in the files the repo makes or only adds to settled by its own tools, and any other left to you.
source: new
added: 2026-10-24
version: 0.1.2
writes: nothing
network: none
role: repo
tags: git
runs-in: repo
-->
# restack

When main moves, every branch waiting to merge conflicts in the same few
files: the add-on list, the changelog, the file tree. This merges REF into
each one, settling those by the rules the repo already follows, and stops on
anything else.

    python adapters/stdlib/restack/restack.py --onto REF BRANCH [BRANCH ...]

    claude/addon-timeline: deb56e83 -> cf502d3c, origin/main merged in; settled CHANGELOG.md, 1 new entry moved to changes/
      push: git push origin claude/addon-timeline

Fetch first (`git fetch origin main`, then `--onto origin/main`): it never
goes online.

**What it settles, and how.** REF is merged into each branch in a scratch
worktree of its own, never in your checkout, as one merge commit. When the
merge conflicts:

| File | Settled as |
|---|---|
| ADDONS.md, README.md, `adapters/stdlib/readme/week.json` | REF's, then made again by `adapters/stdlib/readme/readme.py write`: in the same week REF's tags and nearest entries stand, and only the branch's new entries are worked out |
| BUGS.md | REF's, then made again by `adapters/stdlib/ci/bugs.py write` |
| CHANGELOG.md | REF's, with each entry the branch added under `## Unreleased` moved to a fragment of its own: `changes/<N>.<kind>.md` when it ends `(#N)`, else `changes/+<branch>.<kind>.md`; one REF already holds (a branch stacked on another pull request) only leaves. This one runs whether the merge conflicted there or not; a branch that changed the file any other way stops |
| FILES.md | REF's, then made again by ci/files.py (its cuts, groups.py's order, the branch's files), with what the branch wrote of each file only it added |
| test_contract.py | both sides' `COMMANDS` lines, and entries either side added to `COMMANDS`, `READERS` or `PILE_EXTRA`, with imports, whole |
| adapters/planned.json | REF's ideas, less the ones the branch built, plus any it added, by name A to Z as `adapters/stdlib/ci/order.py` holds the list |
| any other Markdown file | both sides' lines, REF's first, when each side only added lines where the base had none (two paragraphs on one add-on's card), a blank line between paragraphs |

These are the files every add-on's pull request touches and that main's
own changes touch too. **Any other conflict stops that branch** and leaves it
exactly as it was, saying which file: two sides changing the same code is a
person's call. A conflict in one of these files that doesn't fit its rule
(a changelog conflict outside Unreleased, a tree entry both sides changed,
a Markdown line the base had that either side changed) stops it too.

**test_contract.py by what was added.** Two readers each add a sample to
`READERS`, and git lines the two new entries up against one shared closing
line, so neither side of the conflict holds a whole entry and no rule on
lines can settle it. When the lines aren't only `COMMANDS` lines, it reads
the file at the base and on both sides with Python's own parser and takes
REF's, with each entry the branch added to `COMMANDS`, `READERS` or
`PILE_EXTRA` put whole at the end of its dict, and any import the branch
added after REF's last. An entry REF already has is left as REF has it. A
branch that changed or removed an entry that was there, or changed anything
else in the file, stops: that is a person's call.

**Everything the repo makes is made again.** After the merge, every script
on the repo's own list of what it makes, `adapters/stdlib/ci/made.py`, is run
in the scratch worktree: the add-on lists, BUGS.md, the tree in FILES.md,
the lists kept A to Z, and whatever main adds to that list later, since the
list is read there and not kept here. One script on it is left out, the one
that asks PyPI for a new pin's dates: this never goes online.

**Nothing moves until it checks.** Then `test_docs.py` runs in the scratch
worktree; it is the check that catches a merge settled wrong. After it,
the one script left out is asked to check, which asks no one: a pin with no
date stops the branch, and the message says so. Only when both pass is the
branch moved to the new commit. If the branch is checked
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
