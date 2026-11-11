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

    stack-bridges: populated, 29 steps, 14 bridges, 3 deep; 19 rest on no other
    ## what each step takes, and from which
      04 index-cache        01 code-comments: what it wrote, {box}-code
      06 scan               03 index-cache: what it wrote, index-repo; 04 index-cache: what it wrote, index-code
      07 glance             06 scan: its output
      25 restore-drill      24 backup: what it wrote, usb
    ## the order that leaves them in, the record aside
      rest on no other      19: 01 code-comments, 02 git-history, 03 index-cache, 10 first-mention
      1 step deep           7: 04 index-cache, 05 index-cache, 09 fair-merge, 15 pile-rungs
      2 steps deep          1: 06 scan
      3 steps deep          2: 07 glance, 08 why-not
      the longest way down  07 glance → 06 scan → 04 index-cache → 01 code-comments
      name the record       15: a step that adds a row and one that reads the record are a bridge no stack file says

**Why.** [stack](../stack/) runs a file's steps top to bottom. But the
steps are not a row. Some take what an earlier one made, and the rest
could run in any order, or at once. Which is which is decided when the
stack is written, and nothing says it: a card says what an add-on `uses`,
never what a step in someone's stack takes from the step above. This
reads the file and says it. On the 29 steps of
[demo/kept](../../../demo/kept/README.md) there are 14 such bridges, the
longest way down is three steps, and 19 steps rest on no other.

**A bridge is one step taking what another made**, and two kinds are read:

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

**What it cannot see: the record.** A step that adds a row and a later one
that reads the record lean on each other, and the file names only `{box}`
for both. So the page says how many steps name the record, and that those
keep the order they are written in. Nor does it see a place a step writes
without being told to with `--to`, or reads without naming.

It is not a check that the stack will run: an add-on that isn't here, an
option it doesn't take, a file that isn't there. That is the `stack-check`
idea's job.

[example.md](example.md) is a small stack with five bridges to try it on;
none of the stack add-on's own examples has one, each step there asking
the record alone.

It reads the file and writes nothing. It runs no step and opens no folder
the stack names. `--json` prints
[the report](../ci/README.md#the-report-contract) as one JSON object.

**Exit codes**, the kernel's: 0 the bridges hold, or there are none
(`empty`); 42 one can't hold; 2 refused (a bad command line, no such file,
a file that isn't a stack).

**Uses:** the kernel's exit codes; the stack add-on's `parse_stack`.

**Never:** writes anything, runs a step, reads the key, or goes online.
