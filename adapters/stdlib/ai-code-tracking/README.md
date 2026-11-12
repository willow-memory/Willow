<!-- willow-addon
section: Reading more kinds of files
line: Which code Cursor's AI wrote, from its tracking database: each scored commit and conversation, and lines by tab, composer and human.
source: new
added: 2026-11-12
version: 0.1.0
writes: to
network: none
role: reads
reads: .db
output: report
-->
# ai-code-tracking

Which code Cursor's AI wrote, from the database Cursor keeps for it.

    python adapters/stdlib/ai-code-tracking/ai_code_tracking.py \
        mirror --from FILE_OR_FOLDER --to MIRROR
    python adapters/stdlib/ai-code-tracking/ai_code_tracking.py \
        report --from DB [--json]

Besides its chats, Cursor keeps `ai-code-tracking.db` in its ai-tracking folder: a hash of
each chunk its AI wrote (where, by which model, in which conversation, when)
and, for each commit it scored, how many lines tab completion, the composer
(the agent) and the person added and deleted.

**mirror** writes, for the kernel to search, one paragraph per scored commit

    commit 0123abc on main
    date: 2026-05-17
    message: fix the tomato bed
    lines added 10, deleted 2
    by tab: added 3, deleted 0
    by composer: added 5, deleted 1
    by human: added 2, deleted 1
    AI percentage: v1 80.0, v2 80.0

and one per conversation: its id, the models, the first and last time, how
many chunks the AI wrote and in which file extensions. The hashes are never
written, and neither is `tracked_file_content`, the code Cursor keeps of your
files: it stays in the database. Each database is written to MIRROR at the
same relative path with .txt added (a second file, with <n> before .txt, past the kernel's 1 MB
read limit). A file that is not this database, or holds nothing, is skipped
and counted. `--from` is the database itself or a folder to walk for `.db`
files.

**report** prints [a report](../ci/README.md#the-report-contract): totals
(commits scored, lines added by tab, by composer, by human), chunks by model,
and commits and lines by month. `--json` gives the same report as one JSON
object. A database with no rows reports `empty`; a file that is not the
database, `unreachable`.

The original is opened read-only through SQLite's own `mode=ro` and never
written.

Exit codes, the kernel's: 0 wrote some, or reported; 42 nothing readable
(or unreachable); 2 refused (a bad command line, MIRROR and FROM inside one
another).

**Uses:** the kernel's exit codes.

**Never:** writes inside FROM, copies a hash or the code in
`tracked_file_content`, or reads the key.
