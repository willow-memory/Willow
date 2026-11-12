<!-- willow-addon
section: Finding things
line: The files sort placed, copied (never moved) into a pile of their own per category, each copy logged with where it came from and its hash.
source: new
added: 2026-11-12
version: 0.1.0
writes: to
network: none
role: tools
uses: sort
output: report
-->
# land

The files [sort](../sort/) placed, copied (never moved) into a pile of
their own per category, each copy logged with where it came from and its
hash. The step after a sort: a folder of everything, split into one folder
per thing, each ready for a box of its own.

```
python adapters/stdlib/land/land.py --of SORT.json --from FOLDER --to DIR \
    [--skip PREFIX ...] [--dry-run] [--json]

land: populated, copied 3 files into 2 categories, 0 already there, 2 waiting on you, 41 skipped
## health
  letters/clinic.pdf  copied
## money
  bank/may.csv        copied
  bank/june.csv       copied
## waiting on you
  notes/june.md.txt   more than one: money 1, health 1
  ideas.md            unsorted: no phrase of yours
```

SORT.json is sort's report as JSON: `sort.py --box DIR --categories FILE
--json`, or the copy a [stack](../stack/) keeps of its sort step, handed on
as `{NN.json}`. FOLDER is the folder of originals the box's pile was read
from. Each file sort put in a category is copied from FOLDER to
`DIR/<category>/pile/<its path>`, and logged in
`DIR/<category>/landed.jsonl`, one line a copy: its path, where it came
from, its sha256, and the hits sort placed it by. Each category's `pile` is
then a folder to `kernel.py init` a box over.

**The original, not the words.** A pile holds what the readers wrote, so
`<reader>/<path>.txt` is the words of `<path>`. A pile path names, in this
order: the file at that path in FOLDER; the file it is the mirror of (the
extension a reader adds taken off, and a long file's part number with it);
then those two with the first folder taken off (a reader's own folder, in a
pile made by several), the mirror first. The first that is a file in FOLDER
is the one copied, so a bank statement lands as the CSV the bank reader
reads, not as its words. The same original reached by two readers is
copied once; put in two categories by them, it is said, under **in two
categories**, and copied nowhere.

**What waits on you.** sort's **more than one** and **unsorted** are never
copied: a phrase of yours, or a seal on what [sort-ask](../sort-ask/)
suggested, settles them, and the next sort places them. A copy that would
replace a different file already in DIR is left undone, under **left as it
was**; the same bytes already there are **already there**, so a second run
copies nothing twice. A path under `--skip PREFIX` (a code checkout inside
the folder, say) is passed over and counted. `--dry-run` says all of it and
writes nothing.

It prints [a report](../ci/README.md#the-report-contract), and `--json`
gives the same report as one JSON object.

Exit codes, the kernel's: 0 every placed file copied or already there
(populated), or nothing placed (empty); 42 something waits on you; 2
refused (a bad command line, SORT.json not sort's report, FOLDER not a
folder that's there, DIR a file, one inside the other). DIR is made on the
first copy if it isn't there.

**Uses:** [sort](../sort/)'s report.

**Never:** moves, renames or deletes an original; writes outside DIR;
replaces a file already there; copies a file sort didn't place; follows a
pile path out of FOLDER.
