<!-- willow-addon
section: Ways to use it
line: Which steps of a stack take what an earlier step made, the order that leaves them in, and a step that takes what none before it made.
source: new
added: 2026-11-11
version: 0.1.0
writes: nothing
network: none
role: tools
uses: stack
output: report
-->
# stack-bridges

Which steps of a stack take what an earlier step made, and the order that
leaves them in.

    python adapters/stdlib/stack-bridges/stack_bridges.py --stack FILE [--json]

    stack-bridges: populated, 33 steps, 28 bridges, 3 deep; 11 rest on no other
    ## what each step takes, and from which
      04 index-cache        01 code-comments: what it wrote, {box}-code
      06 scan               03 index-cache: what it wrote, index-repo; 04 index-cache: what it wrote, index-code
      07 glance             06 scan: its output
      21 merkle             16 fixity: the record as it left it
      25 restore-drill      24 backup: what it wrote, usb
    ## the order that leaves them in
      rest on no other      11: 01 code-comments, 02 git-history, 03 index-cache, 10 first-mention
      1 step deep           15: 04 index-cache, 05 index-cache, 15 pile-rungs, 17 ids
      2 steps deep          5: 06 scan, 09 fair-merge, 25 restore-drill, 26 three-two-one, 31 kinds
      3 steps deep          2: 07 glance, 08 why-not
      the longest way down  07 glance → 06 scan → 04 index-cache → 01 code-comments
      write the record      2: 16 fixity, 33 stack-row; a step that names the record after one of these takes the record as it left it

**Why.** [stack](../stack/) runs a file's steps top to bottom. But the
steps are not a row. Some take what an earlier one made, and the rest
could run in any order, or at once. Which is which is decided when the
stack is written, and nothing says it: a card says what an add-on `uses`,
never what a step in someone's stack takes from the step above. This
reads the file and says it. On the 33 steps of
[demo/kept](../../../demo/kept/README.md) there are 28 such bridges, the
longest way down is three steps, and 11 steps rest on no other: it could
run in four rounds, 11 steps at once, then 15, then 5, then 2.

**A bridge is one step taking what another made.** Two kinds are read off
the file:

- **its output**: the step names an earlier step's kept output, as stack
  writes it, the step's two-digit place in braces;
- **what it wrote**: the step names a place an earlier step was told to
  write to with `--to`. The place itself, a file under it, or the folder it
  sits in, so a step given a folder is tied to the step that wrote a file
  there. A word like `usb:` before a path is taken off first.

**The order comes from the bridges.** A step that takes nothing rests on no
other. A step is one deeper than the deepest it takes from. Steps at the
same depth don't need one another: as far as the file says, they could run
at once.

**A bridge that can't hold** is said with its step, and ends 42:

- it takes an earlier step's output by a number no step before it has;
- it takes a place a later step writes, so it would read it before it is
  there.

**Two steps told to write to one place** are listed, and not as a fault.
For a folder that is how it is used: two of the stack add-on's own examples
write several files into one folder. For a file, one of the two is lost.
The stack file doesn't say which the place is.

**A third kind is read off the cards: the record.** A stack file names the
record the same way for a step that adds a row and one that only reads it.
The add-on's card tells them apart: its `writes` line names the record or
it doesn't. So a step that names the record after a step whose card says
it writes it takes "the record as it left it", from the last such step
before it. The page lists the steps that write the record. A step naming
an add-on that isn't here has no card, and is listed as not known.

This errs toward waiting. A step that names the record may never read a
row, and it is still placed after the writer above it.

**What it still cannot see:** a place a step writes without being told to
with `--to`, or reads without naming.

It is not a check that the stack will run: an add-on that isn't here, an
option it doesn't take, a file that isn't there. That is the `stack-check`
idea's job.

[example.md](example.md) is a small stack with six bridges to try it on;
none of the stack add-on's own examples has one, each step there asking
the record alone.

It reads the file and writes nothing. It runs no step and opens no folder
the stack names. `--json` prints
[the report](../ci/README.md#the-report-contract) as one JSON object.

**Exit codes**, the kernel's: 0 the bridges hold, or there are none
(`empty`); 42 one can't hold; 2 refused (a bad command line, no such file,
a file that isn't a stack).

**Uses:** the kernel's exit codes; the stack add-on's `parse_stack`; each
step's add-on's card, for its `writes` line.

**Never:** writes anything, runs a step, reads the key, or goes online.
