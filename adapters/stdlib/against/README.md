<!-- willow-addon
section: For maintainers
line: A pull request held to the other open ones: a name both add fails, a file both change is said.
source: new
added: 2026-11-03
version: 0.1.0
writes: nothing
network: none
role: repo
uses: similar
runs-in: repo
-->
# against

Two pull requests built the same add-on, or both added a line to the same
place, and neither could see the other. This holds one pull request to the
others that are open, and says which ones to look at.

    python adapters/stdlib/against/against.py check --base origin/main HEAD pr/12 pr/13

    duplicate: both add add-on sort (#12)
    collides: adapters/stdlib/ci/ci.py with #13; merge its branch first and base on it
    settled: CHANGELOG.md with #13; restack settles it
    near: your idea sorted is near #12's sort
    checked: #12 3fa9c21
    checked: #13 b07e5d4
    2 checked, 1 duplicated, 1 collided, 1 near, 0 not checked

Run it in the repository. HEAD is this pull request's head, each OTHER another
open pull request's, and REF what they branch from; all are any git refs, so
CI fetches `refs/pull/<N>/head` and a person can name local branches. Each pair
is read from where the two left REF (`git merge-base`), so main's later
commits are nobody's. A pull request stacked on another, or one that merged
the other, is read from where the two left each other instead, so what they
share is neither's: the one below sees only what the one above adds past it. That holds after
each has merged REF again since, when they share their stack's commits but
neither holds the other's head: what those shared commits add is still
neither's.

**What it says, for each other pull request:**

| Line | When | Exit |
|---|---|---|
| `duplicate:` | both add an add-on folder in `adapters/stdlib/` or `adapters/deps/` (a `words-<code>` pack too), an idea of the same name to `adapters/planned.json`, the same key to `COMMANDS` in `adapters/stdlib/ci/test_contract.py`, or the same path to FILES.md. An idea built by one and added by the other is the same name. | 2 |
| `collides:` | a trial merge of the two heads (`git merge-tree`) conflicts in a file other than the ones below; the line names it and says to merge that branch first and base on it | 0 |
| `settled:` | the trial merge conflicts only in a file [restack](../restack/) settles by rule: ADDONS.md, README.md, BUGS.md, CHANGELOG.md, FILES.md, `adapters/stdlib/ci/test_contract.py`, `adapters/planned.json`; or any other Markdown file where both sides only added lines, which restack keeps both of | 0 |
| `near:` | an idea or add-on yours adds is near one theirs adds, by [similar](../similar/)'s search | 0 |

Both pulling the same idea *off* `adapters/planned.json` is not a duplicate: it
only means both built something, and building different ones is fine. Only
adding the same thing is.

It ends with each pull request it checked and the short commit it read, then a
tally. The report is the same for the same refs.

**Exit codes:** 0 nothing duplicated; 2 a duplicate, or a bad command line; 42
nothing to check: no OTHER given, or one that is not a ref or shares no
history with REF (the report names it).

**A collision is a warning, never a failure.** Two branches changing the same
code is for the people writing them to settle; this only says which pull
request to merge first.

**Never:** goes online, writes the repository, or changes a ref. The trial merge
writes its objects to a scratch folder, not to `.git`.

**Uses:** the kernel's exit codes, and `adapters/stdlib/similar/similar.py`
for `near:`. The list of files restack settles is held again here, and a test
holds it to restack's own.
