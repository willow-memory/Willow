<!-- willow-addon
section: For maintainers
line: What willow's repo needs from GitHub, kept in one folder so it can be taken away.
source: box
added: 2026-10-23
writes: nothing
network: GitHub, through gh, to read the author of a pull request a security report points to
tags: no-install, online, read-only, maintainers
-->
# github

Everything willow's repo needs from GitHub, and nothing else does. The
kernel and every other add-on run and test the same without it.

    python adapters/stdlib/github/github.py report < ISSUE_BODY
    python adapters/stdlib/github/github.py check

| Part | What it is |
|---|---|
| [host.json](host.json) | how GitHub titles the merge of a pull request, for `adapters/stdlib/ci/whose.py --host` |
| `report` | a security report's comment: the pull request behind each line the report names, and its author, tagged |
| `check` | `.github/` held to the repo: one CI run per change (pushes run on main only, and a pull request's newer commit cancels the run it replaces), the CI matrix, each of ci.py's gates run by exactly one job and every job on the same Pythons, the idea form, the security form, and the changelog job skipping Dependabot's pull requests and no one else's |
| `.github/` | GitHub reads it only at the repo's root, so it lives there, but it belongs to this folder and `check` holds it |

**Taking it away.** Delete this folder and `.github/`. `test_strip.py`, at
the repo's root, shows that what's left still passes every test that
doesn't describe the published repo (the docs still name what you took).

**Another host.** A folder beside this one, say one for GitLab, with its
own host.json (`"label": "!{n}"`, and the titles GitLab gives a merge) and
its own CI file. [whose.py](../ci/whose.py) needs nothing else.

**Never:** it never posts anything itself; the workflow posts what `report`
prints. It never writes a file, and it never sends the report's own text
anywhere.

Exit codes, the kernel's: 0 the comment printed, or `.github/` holds; 2 it
doesn't, or a bad command line.
