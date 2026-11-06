# Changes not yet released

Each pull request's changelog entry, in a file of its own, the shape
[towncrier](https://towncrier.readthedocs.io/) reads. No two pull requests
write the same file, so none conflicts with another over the changelog; a
release folds them all into [CHANGELOG.md](../CHANGELOG.md) and deletes them.

A file's name is the pull request's number and the entry's kind:
`<number>.<kind>.md` (253.added.md for #253). Before the pull request has a number, it is
`+BRANCH.KIND.md` (`+feat-llm-cli.added.md`), and
`adapters/stdlib/github/create_pr.py` renames it to the number in the push
that opens the pull request. The kinds are the changelog's headings:
`added`, `changed`, `deprecated`, `removed`, `fixed`, `security`.

The file holds the entry's text, as it would read after `- ` in the
changelog, with no number: towncrier adds `(#253)` from the name. A fix
names what it fixes, `bug #12`, as always.

    `llm-cli`: suggestions through the llm command, run on a model a person
    already set up for it

`adapters/stdlib/ci/changelog.py` holds a pull request to having one, CI
runs it, and FILES.md lists this folder, not its files.
