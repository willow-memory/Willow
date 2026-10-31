<!-- willow-addon
section: Reading more kinds of files
line: corpus-lens's process reports on your own sessions with agents, as passages: where your intent arrives, who writes the code.
source: new
added: 2026-10-31
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# corpus-lens

corpus-lens process reports as passages: where your intent arrives, who
writes the code.

    python adapters/stdlib/corpus-lens/corpus_lens.py \
        mirror --from FOLDER --to MIRROR

    # corpuslens report

    > This run read 21 events (dropped 0, counted not hidden)...

    ## What this run found

    - **steering_density** — 70.0% of your prompt turns arrive mid-task
    - **composition_mix** — You authored code in 0.0% of your prompts

Walks FOLDER for reports corpus-lens already wrote: markdown that starts
`# corpuslens report`, or JSON with `schema_version`, `audit` and
`results`. Each report is written to MIRROR at the same relative path with
.txt added. Session logs are not read; [agent-transcript](../agent-transcript/)
is the one that opens those.

A file that is not a report is skipped and counted. Hidden parts are not
walked.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused.

**Uses:** the kernel's exit codes.

**Never:** writes inside FOLDER, opens a session log, or reads the key.
