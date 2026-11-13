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

## The laptop against Kaggle, on one pile

The private piles run on the maintainer's laptop and the public ones on
Kaggle, so a step whose output depends on the machine would look like a
difference between piles. To know which, climate-almanac was traced on the
laptop too, from the same freeze (`climate-almanac/laptop/`). Same pile, byte
for byte (the manifests match). Of 357 steps, 15 are unsteady on one machine
or the other; of the other 342, **317 print the same bytes on both** and 25
don't. They are kept in [machine-bound.json](machine-bound.json):

- They describe the machine they run on (the editors and assistants it has,
  its setup): aider, bot-venv, browse, claude-code, codex-cli, copilot,
  cursor, emacs, gemini-cli, jetbrains, opencode, shell, start, vim, vscode,
  windsurf, zed.
- A tool is on one machine and not the other, so the step fires on one
  only: code-shape fires on the laptop; ocr, pdf, photos, record-sql, sheets
  and stems on Kaggle. forge reads differently too.

The report marks these steps wherever a public pile meets a private one, so
nothing it says turns on the machine. The rest are held to be the machines'
same answer.
