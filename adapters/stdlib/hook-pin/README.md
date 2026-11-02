<!-- willow-addon
section: Assistants
line: Each hook's SHA-256 kept on the record when you approve it, so a hook that changed since is named before it runs, never silently trusted or skipped.
source: new
added: 2026-10-24
writes: record
network: none
tags: hooks
-->
# hook-pin

A hook runs only as the bytes you approved.

    python adapters/stdlib/hook-pin/hook_pin.py --box DIR approve FILE...
    python adapters/stdlib/hook-pin/hook_pin.py --box DIR check FILE...
    python adapters/stdlib/hook-pin/hook_pin.py --box DIR run --file FILE --hook "COMMAND"

A hook file can change after you read it: an update, a merge, a tool
rewriting its own settings. `approve` writes one `hook-pin` row through the
kernel's own append for each file: where it is and the SHA-256 of its
bytes. Approving again after a change is a new row, and the old one stays.

| Verb | What it does |
|---|---|
| `approve` | pins each file as it is now |
| `check` | each file: `pinned`, `changed` since the row it names, or `never pinned` (exit 42 unless all are pinned) |
| `run` | the gate: runs COMMAND only if FILE, the hook's own file, is pinned and unchanged; otherwise blocks (exit 2) and says why. The hook's input, output and exit code pass through |

Put `run` where the hook's command was in settings.json, with the hook's own
command in `--hook` and its file in `--file`.

**Never:** reads the key, or runs a hook whose file changed since you approved it.
