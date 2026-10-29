<!-- willow-addon
section: Finding things
line: Who owns this file: the CODEOWNERS rule that matches it, cited by line, on GitHub, GitLab and Forgejo alike.
source: new
added: 2026-10-29
writes: nothing
network: none
tags: no-install, offline, read-only, search
-->
# codeowners

Who owns this file, and which line of CODEOWNERS says so.

    python adapters/stdlib/codeowners/codeowners.py --from REPO src/app.py docs/intro.md
    python adapters/stdlib/codeowners/codeowners.py --box DIR src/app.py

    src/app.py
        .github/CODEOWNERS:12   /src/   @alice @org/web

The CODEOWNERS file is looked for where the forges look: `.github/`, the top
of the repo, `docs/`, then the folders named gitlab, forgejo and gitea (each
with a dot in front), in that order,
and the first there is read. Each path is then matched the way that forge
does:

| File | How a path is matched |
|---|---|
| GitHub's (in `.github/`, the top or `docs/`) | gitignore-style patterns; the last rule that matches wins |
| GitLab's (in its dot-folder, or any file with `[Section]` lines) | the last match in each section wins and a section's owners add up; a rule with no owners takes its section's defaults; a section named twice is one |
| Forgejo's and Gitea's (in their dot-folders) | each rule is a regular expression, and every rule that matches adds its owners |

A pattern with a slash at the start or inside is anchored to the top; one
without matches at any depth. `<dir>/` is every file under a folder of that
name, `<dir>/*` only the files directly in it, and `**` crosses folders. A rule
with no owners clears a path for GitHub, and is shown as "(no owners)". A
regex that doesn't compile is noted and skipped.

A path is only matched, never opened, so it need not exist, and a leading
`./` or `/` is ignored.

Exit codes, the kernel's: 0 every path has an owner; 42 a path has none (or
there is no CODEOWNERS file), which waits on you; 2 refused.

**What it doesn't do:** know a team's members, or check that an owner can
review. It reads the file; the forge decides.

**Uses:** the kernel's box, to find the pile.

**Never:** runs, fetches or writes anything.
