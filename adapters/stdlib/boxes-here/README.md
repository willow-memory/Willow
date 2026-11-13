<!-- willow-addon
section: Keeping track
line: The boxes already in a folder and what waits on each, so one that is there is opened, not made twice; and a list of the ones you choose.
source: new
added: 2026-11-11
version: 0.1.0
writes: to
network: none
role: tools
uses: projects
output: report
-->
# boxes-here

The boxes already in a folder, what waits on each, and a list of the ones
you choose to keep at hand.

    python adapters/stdlib/boxes-here/boxes_here.py --in FOLDER [--deep N] [--json]

    boxes-here: populated, 2 boxes under /home/you/papers; 4 suggestions wait on you
    ## boxes already here
      taxes/box        30 rows: 12 asked, 9 approved, 3 waiting
      letters          8 rows: 2 asked, 0 approved, 1 waiting
    ## not looked in
      scans/2019/q1    it is 3 folders down, and holds folders of its own

**Why.** A box is a folder that holds a kernel.json: a record was started
there. Nothing says so from outside. Start a new one over a folder that
already has one somewhere inside it and there are two records of the same
files. And a box kept apart from your other projects, private papers that
wait on your approval, is found only by remembering where it is. This
looks, and says.

**What it looks at.** FOLDER and the folders under it, `--deep` folders
down (3, unless told; 9 at most). It looks for the one file and counts the
record's rows, as [projects](../projects/) counts them. It opens nothing
else of yours. It doesn't look in a folder whose name starts with a dot,
through a link to a folder, or inside a box.

**Where it stopped short is said.** A folder at the last depth that holds
folders of its own, or one that couldn't be opened, is listed under "not
looked in". So "no box here" is never said of a place it didn't look.

**A box it can't count is still listed**, with why: a broken chain, a
record that can't be read.

**A list of the ones you choose:**

    python adapters/stdlib/boxes-here/boxes_here.py keep --to FILE BOX [BOX ...]
    python adapters/stdlib/boxes-here/boxes_here.py drop --to FILE BOX [BOX ...]
    python adapters/stdlib/boxes-here/boxes_here.py --kept FILE [--json]

`keep` adds boxes to FILE by where they are. Nothing is copied or moved: a
box stays where you keep it. `drop` takes them off. `--kept` reads the
list back the way `--in` reads a folder, and says which are gone.
[browse](../browse/) shows the boxes on such a list beside your projects.

**Where a box is, not who may read it.** The list says where each box is
and nothing else. This sends a box nowhere. What may leave the machine, a
model that isn't on it most of all, is decided where that is already
decided for everything: the operator's standing consent.

It writes FILE, under `--to`, and nothing else: no row on any record, and
your key is never read. FILE's folder must be there already.

Exit codes, the kernel's: 0 said, or done (no box is an empty report); 42
a suggestion waits on you in one, a record can't be counted, or a kept box
is gone; 2 refused. `--json` prints
[the report](../ci/README.md#the-report-contract) as one JSON object.
