<!-- willow-addon
section: Finding things
line: Each folder or repo ranked on its own and the lists merged in turns, so a large corpus can't push a small one out on volume alone, and a source that found nothing says so.
source: bot
added: 2026-10-29
writes: nothing
network: none
tags: no-install, offline, read-only, search, pile
-->
# fair-merge

A big folder shouldn't bury a small one.

One ranked list over a whole pile lets volume win: a thousand log lines hold
"frost" more often than the one garden note that answers. Here every source is
ranked by the kernel on its own, and the lists are dealt out in turns.

    python adapters/stdlib/fair-merge/fair_merge.py --box DIR "when is the frost"
    python adapters/stdlib/fair-merge/fair_merge.py --from FOLDER --from FOLDER "when is the frost"

    1. loose.txt:1    [.]       A frost warning came by post.
    2. logs/syslog:1    [logs]    frost-check cron 0 ran frost
    3. notes/garden.md:1    [notes]    Frost is due the first week of November.
    4. logs/syslog:3    [logs]    frost-check cron 1 ran frost
    logs: 2 more that held it, not shown
    archive: found nothing

A source is a folder. With `--box`, each folder at the top of the box's pile
is one, and the files loose at the top are one called ".". With `--from`, each
folder given is one. Each list is the kernel's own `rank` of that source alone,
so a passage must hold half the question's words and the rarest words weigh
most within a source rather than across them. The lists are dealt first of
each, then second of each, and so on, up to `--top N` passages (6 unless said).

A source with nothing to say says "found nothing" instead of disappearing, and
one with more than was shown says how many more. The question asked back (a
passage that only repeats it) is not an answer and is left out. The box's own
words list is read as the bite reads it.

It asks without asking: nothing is written, not even a record row.

**What it doesn't do:** weigh a source as more trustworthy than another. Turns
are fair, not smart; for the best passage across everything, use the kernel's
own bite.

Exit codes, the kernel's: 0 at least one passage; 42 none held it; 2 refused.

**Uses:** the kernel's `chunks`, `rank` and `echo`.

**Never:** writes anything, not even a record row.
