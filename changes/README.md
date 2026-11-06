# Changes not yet released

Each pull request writes its changelog entry here, in a file of its own,
never in [CHANGELOG.md](../CHANGELOG.md). No two pull requests write the
same file, so none conflicts with another over the changelog. A release
folds every file here into CHANGELOG.md with
[towncrier](https://towncrier.readthedocs.io/) and deletes them.

## The file's name

`+<branch>.<kind>.md` while you work: your branch's name with any `/` as a
`-`, then the kind of change. A branch named feat/llm-cli adding something
writes `+feat-llm-cli.added.md`.

The kind is one of the changelog's headings, in lower case: `added`,
`changed`, `deprecated`, `removed`, `fixed`, `security`.

When the pull request opens, `adapters/stdlib/github/create_pr.py` renames
the file for its number, `<number>.<kind>.md` (253.added.md for #253), in the
same push. You don't rename it yourself.

## What goes in it

The entry's text as it will read in the changelog after `- `, opening with
the add-on's name in backticks, and no number: towncrier adds `(#253)` from
the file's name. A fix names what it fixes, `bug #12`.

    `llm-cli`: suggestions through the llm command, run on a model a person
    already set up for it

One entry a file. A pull request with two entries of the same kind writes
two files, each its own name after the branch's:
`+feat-llm-cli-docs.changed.md` beside `+feat-llm-cli.changed.md`.

## What holds it

`adapters/stdlib/ci/changelog.py` refuses a pull request that changed more
than the docs and has no entry, and one that adds an entry to CHANGELOG.md
itself, saying which fragment to write instead; CI runs it on every pull
request. A branch written the old way is fixed by
`adapters/stdlib/restack/restack.py`, which moves its new entries here when
it merges main in.
FILES.md lists this folder and this README, not the entries, which come and
go with every pull request.
