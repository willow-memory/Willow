<!-- willow-addon
section: Trust and proof
line: Figures a summary says that its full text doesn't: a draft and its packet side by side, ranges and billions read as written.
source: new
added: 2026-10-29
writes: nothing
network: none
tags: writing
-->
# pair-drift

Figures a summary says that its full text doesn't: the packet that drifted
from its draft, a number changed in one and not the other.

    python adapters/stdlib/pair-drift/pair_drift.py --box DIR [--full NAME] [--summary NAME]

    research/childrens-software-interruption  summary 3 figures, full 14, 1 only in the summary
      README.md:131  118          playgate in safe-app-store: merged, in the store's CI matrix, 118
    research/sociotechnical-ai-sovereignty    summary 0 figures, full 43, 0 only in the summary
    2 pairs read, 1 with drift

**A pair is two files in one folder**: the full text, DRAFT.md unless
`--full` names another, and its summary, README.md unless `--summary`
does. Every figure in the summary is looked for in the full text, and one
the full text never says is listed with its line. A pair where the summary
says no figures at all reads as 0: nothing to drift, which is worth
knowing too.

**A figure is a number with what makes it one**: a currency sign, a
percent, a scale word (thousand, million, billion, trillion, or k, M, B, T),
MW or GW, or three or more digits. A range is one figure with both ends kept,
so "$180 to $190 billion" and "$180-190B" agree and "$195-205B" doesn't.
"$5 billion" is never read as "$5". Bare numbers under 100, years from 1900
to 2099 and a year with its month (2026-03) are left out.

It only reads, and the same folder gives the same bytes. Exit codes, the
kernel's: 0 a summary carries a figure its full text doesn't; 42 every pair
agrees, or no pair was found; 2 refused.

**Uses:** the kernel's `chunks`, `config` and `REFUSED`, `ESCALATE` and
`ALIVE`.

**Never:** changes your files; writes anything, even the record; picks
which of the two is right.
