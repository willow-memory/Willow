<!-- willow-addon
section: Keeping track
line: Tokens each agent session spent, by day and by repo, summed from its own session files and priced from a table you keep.
source: new
added: 2026-10-31
writes: nothing
network: none
-->
# session-cost

Tokens each agent session spent, by day and by repo.

    python adapters/stdlib/session-cost/session_cost.py --from FOLDER \
        [--prices FILE]

    session-cost: 2 sessions, 1 day
    2026-10-30  Willow  claude-opus-5-5  in 100 out 50
    total  in 100 out 50

Walks FOLDER for jsonl session files and sums the usage they already
recorded. The day and the repo come from the file (`timestamp`, and the
folder name of `cwd`). `--prices` is a table you keep, one

    model  dollars_per_million_in  dollars_per_million_out

line; without it, only tokens are said. It never goes online for a price.

It only reads. A folder with no recorded usage is "nothing there". Exit
codes, the kernel's: 0 some usage; 42 nothing there; 2 refused.

**Uses:** the kernel's exit codes.

**Never:** writes anything, fetches a price, or reads the key.
