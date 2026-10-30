<!-- willow-addon
section: Reading more kinds of files
line: CI run logs you downloaded (GitHub Actions, GitLab CI, Forgejo Actions): each failing step as a passage.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# ci-logs

Your CI run logs, searchable by failing step and its last lines.

    python adapters/stdlib/ci-logs/ci_logs.py mirror --from FOLDER --to MIRROR

Each step that failed is a short passage: its name, the time of its error, the
last lines it printed and the error itself:

    failed step: Run pytest (2026-10-29 03:28)
      FAILED tests/test_garden.py::test_sun - assert 5 == 6
      ##[error]Process completed with exit code 1.

Three logs are read, told apart by their lines: GitHub Actions and Forgejo
Actions (a timestamp on every line, steps opened with `##[group]`, errors marked
`##[error]`), the same as `gh run view --log-failed` prints it (job, step and
timestamp separated by tabs), and GitLab CI (`section_start:` markers and an
`ERROR: Job failed` line). A step keeps its last 15 lines before the error, with
colour codes taken off. A log with no failing step, or that is not one of the
three, is skipped and counted: a run that passed has nothing to find.

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
