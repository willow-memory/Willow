A pull request's changelog entry goes in a file of its own,
`changes/+BRANCH.KIND.md`, towncrier's shape, never in CHANGELOG.md: every
pull request added its entry to the same lines there, so each merge left all
the others conflicting with main, a merge and a full CI run apiece.
create_pr.py names the file for the pull request, changelog.py holds a pull
request to having one (an entry in CHANGELOG.md still counts, for the ones
already open), FILES.md lists changes/ and not its files, and a release folds
them in with `towncrier build`
