<!-- willow-addon
section: Play
line: bureau, the Bureaucracy homage at UTETY, on the record: the deadlock proved, every visit a row, and Gerald's napkin the only way out.
source: new
added: 2026-11-14
version: 0.1.0
writes: record
network: none
role: tools
-->
# bureau

You attended a lecture you did not sign up for. The Office of Records will
resolve the discrepancy on six documents and will happily tell you which
six. Three of them have never been issued.

    python adapters/stdlib/bureau/bureau.py --box DIR new
    python adapters/stdlib/bureau/bureau.py --box DIR go OFFICE
    python adapters/stdlib/bureau/bureau.py --box DIR hand OFFICE
    python adapters/stdlib/bureau/bureau.py --box DIR wait
    python adapters/stdlib/bureau/bureau.py --box DIR look
    python adapters/stdlib/bureau/bureau.py --box DIR quit
    python adapters/stdlib/bureau/bureau.py --box DIR prove
    python adapters/stdlib/bureau/bureau.py --box DIR check

**The building.** The offices are queue, pigeon, library, department, gate,
stacks, records, gerald and hanz. `go` visits one, `hand` hands over what
you hold, `wait` waits, `look` says what you hold, and `quit` stops going,
the only losing move. Every rule is reasonable and nobody is obstructive;
each refusal is the office being exactly itself.

**The deadlock is proved.** `prove` searches the building twice: strictly,
honouring the fine print, and credulously, matching on what the docket
shows, the way you read it. The strict search never reaches a resolution;
the credulous one does; the gap between them is the false hope, and the
three documents in it are named. It reads no box.

**The way out** is not in the building. Surprise is spent with every
visit; when it runs out the goo is visible, and after a wait nobody set
Gerald leaves a napkin: a word Hanz can read, a blank Records will accept,
or a grape, and the wait starts again.

**The record.** `new` seeds the game from the record's tip: bureau's own
xorshift32, seeded by the tip's first eight hex digits, so the same seed
plays the same game in bureau's browser engine. Each move is a
`bureau-move` row through the kernel's own `append`, carrying the state
bureau compares: what you hold, surprise, dwell, the refusal tier, how it
resolved. `check` plays every game on the record again from its seed, and
names the first row whose state isn't what the moves give; while one
doesn't hold, nothing else is played.

Exit codes, the kernel's: 0 done, or every game holds; 2 refused.

**Where it comes from:** bureau, in the SAFE App Store, which keeps its web
docket and its calibration ledger; this is its building, its goo and its
proof. The offices and prose are carried word for word from bureau's own
source. Played against bureau's own `Session` on 79,973 moves from 2,000
seeds, every narration line and every state the same, both endings
reached, and the proof identical. The lore is Sean's: Gerald, the napkin,
the grape, the goo, the squeakdogs, Hanz and his orange are canon; the
discrepancy, the offices and the requirement graph are not.

**Never:** shares a surface with UTETY's campus front, which is for children
and whose rule is that feedback is about the work, never the learner; this
is a machine for frustration on purpose. Never reads the key, or writes the
record except through the kernel.
