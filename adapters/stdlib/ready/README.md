<!-- willow-addon
section: For maintainers
line: A branch made ready for its pull request, on no host: the repo's own steps run in order, what they make committed, and the body written.
source: new
added: 2026-11-08
version: 0.1.0
writes: to, changes/*
network: none
role: repo
uses: ci, stack, restack, test-impact, against
runs-in: repo
-->
# ready

Everything a pull request needs from willow's own add-ons, before it opens
and after, with no host to ask. [create_pr.py](../github/create_pr.py) runs
it around GitHub's part; without GitHub, or on another host, run it by hand.

    python adapters/stdlib/ready/ready.py steps  [--steps FILE]
    python adapters/stdlib/ready/ready.py check  --base REF
    python adapters/stdlib/ready/ready.py run    --base REF [--open REF]... [--steps FILE] [--to FILE]
    python adapters/stdlib/ready/ready.py body   --base REF --from FILE [--footer TEXT]
    python adapters/stdlib/ready/ready.py opened --base REF --pr N [--steps FILE] [--to FILE]

REF is the branch the pull request goes into, as this checkout has it
(origin/main, say): fetch it first.

| Verb | Does |
|---|---|
| `steps` | lists [steps.md](steps.md)'s pools and steps: what `run` and `opened` run |
| `check` | refuses what can't open (not on a branch, on REF's own branch, uncommitted changes, nothing REF doesn't have) and stops, 42, on a change that owes a changelog fragment and has none |
| `run` | `check`, then every pool but the last, in order, from the repo's root; what a step makes is committed as `tidy:`; `--open` names the other open pull requests' branches, for `against`; `--to` keeps what each step printed |
| `body` | prints the pull request's body, the template's four sections, from the commits, the touched add-ons' cards, and what `run` kept |
| `opened` | once it has number N: renames `changes/+<branch>.<kind>.md` to `changes/N.<kind>.md` and commits it, then runs the last pool, [changelog.py](../ci/changelog.py) with N |

A step that exits 0 is done. A 42 that owes nothing (`against` with no
other pull request, `realdata` with no add-on a person runs, `restack` with
main already in, `test-impact` with a gate whose tool isn't here) is noted
for the body and passed. Any other exit stops the run there, 42, and so
does a collision `against` names: it says which, and what the step printed.

**By hand, with no host:**

    git fetch origin main
    python adapters/stdlib/ready/ready.py run --base origin/main --open origin/<their branch> --to /tmp/record.json
    python adapters/stdlib/ready/ready.py body --base origin/main --from /tmp/record.json > /tmp/body.md
    # push the branch, open the pull request with /tmp/body.md, then with its number:
    python adapters/stdlib/ready/ready.py opened --base origin/main --pr <N> --to /tmp/record.json
    # and push again

**Never:** push, ask a host anything, rebase, amend or force-push, approve
or merge. It writes no file but `--to` and a fragment's new name; every other
change is a step's own, committed as `tidy:`.

Exit codes, the kernel's: 0 done; 42 something needs you (a step that
failed or stopped, a missing fragment), and it says what; 2 refused (a bad
command line, a step naming an add-on that isn't here, or what `check`
refuses).
