# Pull requests, for agents

Opening one, keeping it current, and what CI's rows need. Part of
[AGENTS.md](../../AGENTS.md); CONTRIBUTING.md's Pull requests has the steps.

## Opening one

- **Look at the open pull requests first, whatever you branch from.**
  Branching from `main` is where your work starts, not a sign that nothing
  else is in flight: another session may be building the same idea, or
  changing the same file, on a branch main doesn't have yet. Before the
  first change, list them (`gh pr list`, or your GitHub tools) and read the
  ones near yours. Once your branch has a commit, hold it to them:

      git fetch origin '+refs/pull/*/head:refs/remotes/pr/*'
      python adapters/stdlib/against/against.py check --base origin/main HEAD pr/12 pr/13

  naming each open one. A duplicate found then costs a message on their pull
  request; found by CI, it costs a branch. create_pr.py runs the same check
  again before it opens yours.
- **Open it with create_pr.py.** Commit the change and its changelog entry,
  then run `python adapters/stdlib/github/create_pr.py`: it runs the steps
  below for you, opens the pull request and numbers its entry, and exits 42
  only on what needs you, saying what. The rest of this page is what it does,
  for when it stops.
- **Run it in the background, in a worktree of its own.** It can take many
  minutes, and it commits what its steps change (`tidy:`) on whatever branch
  is checked out when they finish: switch branches in its checkout meanwhile
  and that commit lands on the other branch, and its last checks read the
  wrong one. So give it a `git worktree` of its own, start it in the
  background, go on working in yours, and read what it printed when it ends:
  the pull request's number, or what it stopped on.
- **Several sessions can share a branch.** Fetch before you push, merge
  what's new, and never force-push.
- **Merging makes a merge commit**; squash isn't allowed on this repo.
- **Branch from `main`; open it, name its changelog fragment for it, and
  push once.** Another pull request may take the number you guessed, so
  use the real one, and do it in that one push: each push starts every
  check, and the first run should not be thrown away. create_pr.py does it.
- **Check the open pull requests always; stack on one only when told.**
  Checking is the step above, and never skipped. Stacking is not the
  default: CI's `against` job holds yours to them too, and a duplicate (a
  name both add) fails it, while a collision names the pull request to
  merge first. Stack only on one it names: merge its branch into yours and
  make it your base. The steps are in CONTRIBUTING.md's Pull requests.
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
kept A to Z, craft-assembly's report). A changelog fragment is a file no
other branch writes, so it never conflicts. An entry written in CHANGELOG.md
the old way is refused by CI; `restack.py --onto origin/main BRANCH` moves
it to a fragment as it merges main in.

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
