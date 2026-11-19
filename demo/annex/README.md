# The Annex: eight boxes that never touch, and what only a witness can see

**Frozen 2026-11-19**, in the commit `FROZEN.json` is in, alone:
[FROZEN.json](FROZEN.json) holds the SHA-256 of `make_life.py`, `scene.py`,
`annex_os.py` and `corridor.md`, the eight pass rules, and the hash of every
tool the scene uses. `test_annex.py` fails if a frozen file changes; a change
is a new freeze. Everything here is invented: the people, the firms, the
program, the chip company and every document. The story behind it is in
[STORY.md](STORY.md).

Not a blind study, and it doesn't pretend to be. The scene was played many
times while it was built, so the rules were written before the code but tuned
against its output. What the freeze holds is that the checks can't be
loosened afterwards, and that the scored run below is the one this code makes.

    python demo/annex/make_life.py
    python demo/annex/scene.py run --life demo/annex/life --to /tmp/annex --box /tmp/annex-study
    python demo/annex/annex_os.py build --scene /tmp/annex --to /tmp/annex-os.html

## The day

Integration day, deep in a facility. Three contractors, three programs, one
spec. Each compartment is a willow box (a pile, a record, a key of its own), so
access to one is never access to another. Material crosses a wall only as a
sealed package (`share`), a `sent` row on one chain and a `received` row on
another. Everything is compromised, each box differently, and the record is the
only thing that can tell which ways it can see.

| Box | Who | What is wrong with them |
|---|---|---|
| `vask` | Dr. Vask, a psychologist turned ML specialist, at Helio | signs for a renewal she doesn't believe in |
| `karst` | the Former's firm; its spec asks every party for everything | over-asks; its planner asked about her before her badge |
| `lumen` | the sensors firm; one engineer, Pell | quietly sells a second stream, and says so if asked straight |
| `program` | the office that owns the schedule | its schedule and the gate's clock are an hour apart |
| `counter` | the analyst; holds the unsealed rumour | keeps it unsealed as leverage, and rewrites a seal's date |
| `intake` | the gate | waves people through |
| `oversight` | the inspector | reads nothing, witnesses everything; the report is buried |
| `prior` | Vask's own history | never crosses the wall |

The scene plays, in order: the wall (one question, two boxes); two sealed sends;
a package edited on the way; each box's own stack over its own pile; the
"operator" clash and the two clocks arriving at Oversight; spec 2.2 taking from
three boxes and giving nothing back; the planner's log (92 minutes before the
badge, and `fixity` says untouched); Counterintel's backdated seal and the
witness that names it; the one file an assistant may read (`approved-only`);
and the corridor, where nothing is recorded. [ANNEX-OS](annex_os.py) is a
fictional green-screen page over the result: a badge for each door, a manifest
printer that refuses the unsealed, a witness run whose dead-man's page goes
dark, a briefing that reads only what was served, a corridor with the
record light off.

## The pass rules

| | rule |
|---|---|
| R1 | no sealed package holds a long line of any pile but its sender's |
| R2 | the rumour is in no package and not in the file an assistant is served |
| R3 | asked about another box's subject, a box answers nothing on record (exit 42) and serves nothing, while the box that holds it serves its own |
| R4 | the witness holds every real chain and names exactly the rewritten copy |
| R5 | a package edited on the way is refused as broken where it lands |
| R6 | nothing but the person's own `seal` wrote a seal: every seal row is the person's, and each box holds as many as its owner sealed |
| R7 | the corridor wrote no row on any chain, and the question asked after it holds no word of itself |
| R8 | no box alone finds the clash or the clocks: each box's own stack flags nothing |

## The dry run

`scene.py run --dry` (2026-11-19): every question replaced by nonsense, each
pile plus one nonsense passage the nonsense finds (its words out of order, so
it is no echo, and one per box so no package can hold another's line). Eight
boxes built, every step ran after the kernel (the seals, the sends, the
stacks, the witness, the served file, the corridor), all eight chains verify,
and the eight rows are named `annex:dry:R1` to `R8`, state `wired`.

What it found before the freeze: a repeated question serves the earlier
sealed answer first (as the kernel promises), so the second seal in a box
found no passage to cite. Each dry question now carries a different nonsense
word. What it can't see: it skips every check that reads real content (the
wall's exit 42, the clash and clock text, the planner's 92 minutes, what the
served file says), so those are only exercised by the scored run.

## The scored run

2026-11-19, after the freeze, on a box outside the repo:

    R1 pass   R2 pass   R3 pass   R4 pass   R5 pass   R6 pass   R7 pass   R8 pass

    $ python kernel.py verify --box /tmp/annex-study
    the chain holds: 17 rows, 0 sealed

Sixteen verdict rows (eight dry, eight scored), each carrying the SHA-256 of the
answers it was scored on and of the tools. Eight of eight pass.

## Freeze 2

[FROZEN-2.json](FROZEN-2.json), 2026-11-19, committed alone. CI on the pull
request caught a fault in how `scene.py` spells its paths, not in anything the
scene does: it built them part by part (`ROOT / "adapters" / ... / "stack.py"`),
and `test-impact` reads a bare `"stack.py"` string as every file by that name,
including `demo/bernadette/stack.py`. So a change to `what_changed.py`, which
that stack runs, planned `demo:annex` and failed
`test_impact.py::test_the_steps_are_ordered_cheapest_first`. The four paths
(`STACK`, `FIXITY`, `APPROVED`, `SHARE`) are now one string each, as
`demo/johnson` writes them. The diff against freeze 1 is those four lines; no
rule, check or other file changed. The dry run and the scored run were made
again on the new hash, on a fresh box outside the repo: `R1` to `R8` pass,
`kernel.py verify` holds (17 rows). That run's rows carry the new `scene.py`
hash, so they are not freeze 1's.

## What failed, and what this doesn't show

- **The cross-box comparison is the scene's own.** Oversight receives the
  sealed answers, but no add-on reads received packages, so the side-by-side of
  the clash, the clocks and the planner is a few lines of `scene.py`, said so in
  its output. That is a gap this demo found in willow, not a result.
- **R8 is weaker than it reads.** `contradictions` reads dates and amounts in
  one box's own files, so it could never see a clash of word definitions
  ("operator": a process, a person), and the two clocks are in different
  boxes. R8 passes because no box alone *can* find them with this tool. A box
  with a tool that read definitions would test it harder.
- **R6 checks the records, not the scene's intent.** It holds every seal row to
  the person's own `seal` and the counts to the scene's, which is what the
  records can show; that the scene never reads a key it was given is its own
  claim, and the keys are written where the scene can reach them.
- **One chain was rewritten, on purpose, in a copy.** The real Counterintel
  chain holds; the witness names the copy. Only Oversight kept a package from
  Counterintel, so Oversight is its only witness: had it never sent one, the
  rewrite would go unseen.
- **The page and the corridor are fiction.** `corridor.md` is what two people
  remember and says it is not evidence; the briefing's matcher is a toy.
- **The tests aren't frozen**, only the four files and the tools. A loosened
  test would show in a diff, not in `FROZEN.json`.
