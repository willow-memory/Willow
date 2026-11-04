<!-- willow-addon
section: Finding things
line: What you wrote on this date in earlier years.
source: box
added: 2026-10-23
writes: nothing
network: none
role: page
output: report
-->
# on-this-day

What your files say happened on this date in earlier years.

    python adapters/stdlib/on-this-day/on_this_day.py --box DIR [--now TS] [--json]

    on-this-day: populated, 2 lines written on 10-23 in 2 earlier years
    ## 2025
      dad/care-log.csv:68  2025-10-23,71.4,118/67,65,
    ## 2023
      tuning/2023.txt:205  2023-10-23  Wendell Ashby - Yamaha U1 (1988)

Newest year first, a group a year. `--json` prints the same report as one JSON object. A line counts when it holds the date itself, read the way
the kernel reads one, or when it's the first line of a file named by that day.
A passage's other dates never stand in for a line's own: the first build let a
ledger's later row date its earlier ones, and its test now holds that shut.

**Exit codes:** 0 something was written on this day (`populated`) or nothing was (`empty`); 2 refused.

**Uses:** the kernel's `chunks`, `newest`, `config` and `now`.

**Never:** writes anything.
