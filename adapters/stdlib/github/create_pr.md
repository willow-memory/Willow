# create_pr: the steps before a pull request opens

The stack [create_pr.py](create_pr.py) runs, in this order, on the branch
you're on. A step is `- NAME -- ARGS`, as in any [stack](../stack/): NAME is
an add-on (`ci.bugs` is [bugs.py](../ci/bugs.py) in ci), run from the repo's root. `{base}` is
the base branch as origin has it, `{branch}` yours, `{scratch}` a folder of
the run's own, `{open}` every other open pull request's branch, and `{pr}`
its number once it has one.

A step that exits 0 is done. One that exits 42 or 2 stops the run there:
create_pr.py says which, shows what it printed, and exits 42, since that
is yours to look at. A few 42s mean nothing is owed, and are said in the
pull request instead (create_pr.py names them). Whatever a step leaves
changed is committed as `tidy:`, never written by hand.

## main brought in

Conflicts in the files this repo makes are settled by their own rules.

- restack -- --onto {base} {branch}

## made, never written by hand

Each file a script makes, in the order adapters/stdlib/ci/made.py keeps:
the add-on lists, BUGS.md, FILES.md, the lists kept A to Z, a demo's
report.

- ci.made -- write

## checked here

The gates the change can reach, fast ones first; a change that reaches
everything leaves every gate to CI, which runs them anyway, and still runs
what the rest of it reaches.

- ci.ci -- run lint --box {scratch}/lint
- test-impact.impact -- run --base {base} --narrow --jobs 4

Each add-on the change touches, run on every demo person's real folder.

- ci.realdata -- run --base {base}

## held to the open pull requests

- against -- check --base {base} HEAD {open}

## after it opens

Its number is written into its changelog entry before this runs.

- ci.changelog -- --base {base} --pr {pr}
