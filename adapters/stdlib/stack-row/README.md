<!-- willow-addon
section: Trust and proof
line: A stack's kept run put on your record as one row: which steps ran, how each ended, and the hash of what each printed, never the words.
source: new
added: 2026-11-11
version: 0.1.0
writes: record
network: none
role: tools
uses: stack
-->
# stack-row

A stack's kept run put on your record as one row.

    python adapters/stdlib/stack-row/stack_row.py --box DIR --run FOLDER [--now TS]

    put on the record: row 3, 9 steps (8 clean, 1 ended otherwise)
    already on the record: row 3 holds this run as it stands, 9 steps (8 clean, 1 ended otherwise)

**Why.** [stack](../stack/) run with `--to FOLDER` keeps what each step
printed in that folder. The record knows nothing of it. After the 28 steps
of [demo/kept](../../../demo/kept/README.md) it held two rows: the start,
and the one a step happened to append. What the run found could not be
proven later, traced back or sent on with the rest, and
[prov](../prov/) had nothing to say of it.

**What the row holds**, for each step that has ended:

| field | what |
|---|---|
| `n`, `addon` | its place in the stack, and its add-on |
| `mark`, `fed` | the stack's own marks, from its log: the add-on and its arguments hashed, and the files it was fed hashed |
| `exit`, `lines` | how it ended and how many lines it printed; a step that was not run has no exit |
| `sha256` | the SHA-256 of what it printed, as kept |

and `of`, one hash over all of those, which is the run as it stands.

**Never the output, never an argument.** A step's arguments can hold your
words (a question, a name), and the record keeps acts, not words. The marks
say two steps were asked the same way without saying how.

**As the last step of the stack itself**, it records every step before it:

    - stack-row -- --box {box} --run FOLDER

Its own step has started and not ended, and is left out. A step the log
says was started and never ended is left out the same way: half a step's
output is not what it printed.

**Asked twice, it writes once.** When the newest such row on the record is
of the run as it stands, it says so and adds nothing. A run gone on with
(`--resume`, a step added) is another run as it stands, and gets a row.

It reads FOLDER and the record, and writes the record only, through the
kernel. `--now TS` is the time on the row, as the kernel takes it.

**Exit codes**, the kernel's: 0 the row was written, or was already there;
42 no step of the run has ended yet; 2 refused (a bad command line, no such
box, a record that doesn't verify, a folder that isn't a kept run).

**Uses:** the kernel's `append`, `read` and `now`; the stack add-on's log,
by its lines.

**Never:** reads the key, seals anything, keeps a step's output or its
arguments, or goes online.
