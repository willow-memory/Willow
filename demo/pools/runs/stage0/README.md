# Stage 0: every step alone, twice, on the public piles

Run on Kaggle from the second freeze (willow-pool-test at b33031cb), 2026-11-13,
21:4x to 22:32Z: one notebook a pile, each fetching Willow at the freeze and its
pile at the pinned commit, holding the pile's shape to the freeze before running.

Each folder holds the trace's rows of two runs (`rows-a.jsonl`, `rows-b.jsonl`)
and `run.json` (seconds, processor). `known-gaps/probes.json` is the 21 probes'
results, asked in a notebook of their own (`probes-run.json`): the trace keeps
no step's folder, so the probes notebook ran hurdat2 and csv-rows by their own
step command lines and gathered their mirrors (known_gaps.py read). Its first
two tries stopped before any question was asked (the mirrors weren't kept; the
probe list is kept under "probes"); `probes-timeline.txt` has them.

| pile | seconds a run | fired | unsteady | timed out | breaches |
|---|---|---|---|---|---|
| willow | 1,174 / 1,155 | 303 of 357 | 15 | 0 | 0 |
| nestor | 816 / 808 | 294 | 14 | 0 | 0 |
| jeles | 274 / 272 | 295 | 14 | 0 | 0 |
| homestead-law | 143 / 141 | 295 | 15 | 0 | 0 |
| forge | 172 / 174 | 296 | 14 | 0 | 0 |
| climate-almanac | 61 / 57 | 295 | 15 | 0 | 0 |
| known-gaps | see run.json | 289 | 15 | 0 | 0 |

The probes, all as frozen: keyed-once 4 of 4 hit, controls 2 of 2 (not found:
hurdat2 closed it); stray-quotes 4 of 4 missed, controls 3 of 3 hit (found);
split-entry 4 of 4 missed, controls 4 of 4 hit (found).

The privacy gate was run over these files before they were committed. Its one
deny-list flag is the add-on name oakenscroll, a step name already public in
this repository; the maintainer said it should not be on that list.

The private piles' rows stay on the maintainer's laptop.
