<!-- willow-addon
section: For maintainers
line: What willow's repo needs from GitHub, kept in one folder so it can be taken away.
source: box
added: 2026-10-23
writes: changes/*
network: GitHub, through gh, to read the author of a pull request a security report points to, and for create_pr.py to list the open pull requests and open yours
role: repo
uses: ci, readme, stack, restack, test-impact, against
runs-in: repo
-->
# github

Everything willow's repo needs from GitHub, and nothing else does. The
kernel and every other add-on run and test the same without it.

    python adapters/stdlib/github/github.py report < ISSUE_BODY
    python adapters/stdlib/github/github.py check
    python adapters/stdlib/github/create_pr.py [--base BRANCH] [--title TEXT] [--footer TEXT]

| Part | What it is |
|---|---|
| [host.json](host.json) | how GitHub titles the merge of a pull request, for `adapters/stdlib/ci/whose.py --host` |
| `report` | a security report's comment: the pull request behind each line the report names, and its author, tagged |
| `check` | `.github/` held to the repo: one CI run per change (pushes run on main only, and a pull request's newer commit cancels the run it replaces), the CI matrix, each of ci.py's gates run by exactly one job and every job on the same Pythons, the idea form, the security form, and the changelog job skipping Dependabot's pull requests and no one else's |
| [create_pr.py](create_pr.py) | this branch's pull request, opened by the steps in [create_pr.md](create_pr.md); see below |
| `.github/` | GitHub reads it only at the repo's root, so it lives there, but it belongs to this folder and `check` holds it |

**Opening a pull request.** Commit the change, its changelog fragment with
it (`changes/+<branch>.<kind>.md`, [changes/README.md](../../../changes/README.md)),
then run `create_pr.py`. It runs [create_pr.md](create_pr.md), a
[stack](../stack/) of the repo's own add-ons, in order: `restack` brings
main in, [made.py](../ci/made.py) makes again every file a script makes, `ci` lints,
`test-impact` runs the gates the change reaches (when it reaches
everything, only what the rest of it reaches: CI runs them all), and `against` holds it to the open pull
requests. Then it pushes, opens the pull request (or finds the one open for
this branch), names its changelog fragment for its number, runs
[changelog.py](../ci/changelog.py) with it, and pushes again.

- **Done by itself:** what a step makes is committed as `tidy:`; the
  body is the template's four sections, from the commits' messages, the
  touched add-ons' cards, what each step printed, and what was left to CI.
- **Stopped on, exit 42:** a step that fails or needs you, a collision
  `against` names, a change with no changelog entry, a branch origin has
  moved on, and GitHub out of reach. It says which, and what to do; run it
  again after. A push or an open GitHub answers with an error (a 502) is
  tried again first, after 2, 4, 8 and 16 seconds, and before each new open
  it looks for the pull request, which an error answer can still have made. A 42 that owes nothing (no other pull request to hold it to, no add-on a person runs to try on real data,
  a gate whose tool isn't here) is said in the pull request instead.
- **Never:** rebase, amend or force-push, approve or merge, or write a file
  but the changelog fragment's name.

**Taking it away.** Delete this folder and `.github/`. `test_strip.py`, at
the repo's root, shows that what's left still passes every test that
doesn't describe the published repo (the docs still name what you took).

**Another host.** A folder beside this one, say one for GitLab, with its
own host.json (`"label": "!{n}"`, and the titles GitLab gives a merge) and
its own CI file. [whose.py](../ci/whose.py) needs nothing else.

**Never:** `github.py` never posts anything itself; the workflow posts what
`report` prints. It never writes a file, and it never sends the report's own
text anywhere. `create_pr.py` posts one thing, your pull request, and writes
one thing, your changelog fragment's name.

Exit codes, the kernel's: 0 the comment printed, or `.github/` holds, or the
pull request is open with everything pushed; 42 `create_pr.py` stopped on
something that needs you; 2 `.github/` doesn't hold, or a bad command line
(or `create_pr.py` refused: not on a branch, uncommitted changes, nothing to
open).
