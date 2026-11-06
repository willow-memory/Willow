# Pull requests, for agents

Opening one, keeping it current, and what CI's rows need. Part of
[AGENTS.md](../../AGENTS.md); CONTRIBUTING.md's Pull requests has the steps.

## Opening one

- **Open it with create_pr.py.** Commit the change and its changelog entry,
  then run `python adapters/stdlib/github/create_pr.py`: it runs the steps
  below for you, opens the pull request and numbers its entry, and exits 42
  only on what needs you, saying what. The rest of this page is what it does,
  for when it stops.
- **Leave the checkout alone while it runs.** It can take many minutes, and
  it commits what its steps change (`tidy:`) on whatever branch is checked
  out when they finish: switch branches meanwhile and that commit lands on
  the other branch, and its last checks read the wrong one. Do other work in
  a `git worktree` of its own.
- **Several sessions can share a branch.** Fetch before you push, merge
  what's new, and never force-push.
- **Merging makes a merge commit**; squash isn't allowed on this repo.
- **Branch from `main`; open it, add its number to CHANGELOG.md, and push
  once.** Another pull request may take the number you guessed, so write the
  real one, and do it in that one push: each push starts every check, and the
  first run should not be thrown away.
- **Don't stack on the open pull requests by habit.** CI's `against` job
  holds yours to them: a duplicate (a name both add) fails it; a collision
  names the pull request to merge first. Stack only on one it names, merge
  its branch into yours and make it your base. Run it yourself before you
  open: `python adapters/stdlib/against/against.py check --base origin/main
  HEAD OTHER ...`. The steps are in CONTRIBUTING.md's Pull requests.
- **Work that needs another unmerged branch stacks on it.** An add-on whose
  idea, or whose card's link, exists only on another branch is built from
  that branch, and its pull request's base is that branch; built from
  `main`, it fails `test_docs.py` and clashes on `adapters/planned.json`.
- **When GraphQL isn't reachable** (some cloud agent sessions), `gh pr create`
  is refused; open it through the REST API instead:

      gh api repos/willow-memory/Willow/pulls --method POST \
          -f title=... -f head=BRANCH -f base=main -f body=...

  A shallow clone fetches only `main`, so a pushed branch shows as never
  pushed until its own fetch refspec is added.

## When main moves under a branch

Merge or rebase, then regenerate rather than hand-merge what is generated:
`python adapters/stdlib/ci/made.py write` makes every made file again
(ADDONS.md and the README's add-on sections, BUGS.md, FILES.md, the lists
kept A to Z, craft-assembly's report). CHANGELOG.md is merged by hand: both
sides' lines, in their order.

## A new CI row

A gate added to `gates()` in `adapters/stdlib/ci/ci.py` is also named in the
two lists of gates in `adapters/stdlib/ci/test_ci.py`. A demo's tests need no
row: a demo folder with tests that no `DEMO_TESTS` row runs gets
`demo:FOLDER` from `demo_tests()`. Write a row only to give it another name
or a program it needs (craft-assembly's git and cargo). Missed,
`tests:adapters-*` fails, and `tests:strip-*` with it, since it runs the same
tests. A new test file needs nothing: the chunks are cut from the files there
are, and one not in `adapters/stdlib/ci/test-times.json` counts as the
median.
