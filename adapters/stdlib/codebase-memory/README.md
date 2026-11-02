<!-- willow-addon
section: Reading more kinds of files
line: codebase-memory-mcp's code graph, read from a copy of its SQLite file: each function, what calls it, and its file and line.
source: new
added: 2026-10-31
writes: to
network: none
-->
# codebase-memory

A code-graph SQLite file as passages: each function, what it calls, and
its file and line.

    python adapters/stdlib/codebase-memory/codebase_memory.py \
        mirror --from FOLDER --to MIRROR

    vendor_sync_check (function)
    file: tools/vendor_sync_check.py:129
    name: tools.vendor_sync_check.vendor_sync_check
    edges: import tools.vendor_sync_check.CheckResult

Walks FOLDER for `.db` files that hold a `symbols` table and an `edges`
table (the graph codebase-memory-mcp writes, or a copy of it). Each
function or method becomes one paragraph, sorted by name. The original is
only read, and only through SQLite's own read-only open.

Each graph is written to MIRROR at the same relative path with .txt
added. A file that is not a graph is skipped and counted. Point the
kernel at MIRROR to ask who calls what.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused.

**Uses:** the kernel's exit codes.

**Never:** writes inside FOLDER, or changes the graph.
