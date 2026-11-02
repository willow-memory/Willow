<!-- willow-addon
section: Reading more kinds of files
line: What gh prints with --json (issues, pull requests, runs), saved to a file and read as dated passages.
source: new
added: 2026-10-29
writes: to
network: none
-->
# gh-json

What gh printed, searchable by number, title, author and day.

    python adapters/stdlib/gh-json/gh_json.py mirror --from FOLDER --to MIRROR

Save `gh issue list --json ...`, `gh pr list --json ...` or `gh run list --json ...`
to a file and each item is written, oldest first, as a dated passage:

    issue #12 (open) 2024-03-02 ana: Tomatoes want more sun [bug, garden]
      The bed by the fence is shaded after noon.
      comment 2024-03-03 ben: Move them to bed 2.
    pull request #14 (merged) 2024-03-04 ben: Move tomatoes to bed 2 (branch bed-2)
    run 1234 (failure) 2024-03-04 CI on main: Move tomatoes

An item with a `number` and a `title` is an issue, or a pull request when it has
a `headRefName`, `mergedAt` or `isDraft`; a pull request with a merge time is
"merged". A run has a `databaseId` and a workflow, conclusion or status. gh only
prints the fields it was asked for, so what is absent is left out, never
invented. Other JSON is skipped and counted.

Each file is written to MIRROR at the same relative path with .txt added.
FOLDER is only read: hidden folders and files are skipped, and nothing is
written inside it. A file that can't be read is skipped and counted, never a
crash:

    wrote 2 files to MIRROR; skipped 1

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`); Python's
standard library for the format.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, or goes online.
