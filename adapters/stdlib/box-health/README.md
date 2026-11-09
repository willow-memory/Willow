<!-- willow-addon
section: Trust and proof
line: Is your willow all right? One line: files it can't read, readers out of date, and when its record was last checked.
source: new
added: 2026-10-29
version: 0.1.0
writes: nothing
network: none
role: page
looks-for: books, mail, office, pdf
output: report
-->
# box-health

Is the box all right? A report: one line to say, a row for each concern.

    python adapters/stdlib/box-health/box_health.py --box DIR [--json]

    box-health: empty, nothing needs you; 214 rows hold; 3 approved, 2 waiting; every file readable; words list as last used; last out row 2026-10-20 (4 days ago)

    box-health: populated, box needs you: 3 things, 9 files can't be read
    ## needs you
      approvals  1 suggestion waiting for you
      out        no out row yet
    ## can't be read
      .docx      3 files, read by office
      .pdf       2 files, read by pdf
      over 1 MB  2 of them
    ## fine
      record     3 rows hold
      approvals  0 approved, 1 waiting

It prints [a report](../ci/README.md#the-report-contract), the shape every
report add-on shares. `--json` gives the same report as one JSON object.

What it looks at, in this order:

| Part | Says |
|---|---|
| the chain | whether every row's hash holds; a break is said first and alone, since nothing after it can be trusted |
| approvals | how many hold under your key, how many suggestions wait, and any approval that fails its proof or whose proposal file is no longer the bytes you approved |
| files it can't read | the files in your folder the bite skips (binary, too large, not UTF-8 text), counted by extension, with the add-on that reads that kind of file when this repository has one, and how many of them are over the kernel's 1 MB |
| the words list | whether it is still the one the last question used, and that it reads at all |
| `out` | when the record last had an out row, the kernel's look at what waits on you, and how long ago |

Hidden files and folders are not counted: the bite doesn't read them either.
A waiting suggestion, an unreadable file, a changed words list or a box that
has never had an out row each makes the box `populated`, since each is something you
can act on. `--long` is still accepted and changes nothing: every part has its row.

The approvals are checked through the kernel's `sealed`, which reads your key
there and nowhere here. It writes nothing, not even an out row, so asking
how the box is doesn't move the record's tip.

Exit codes: 0 `empty` (nothing needs you); 42 `populated` (something needs
you); 2 refused (a chain that doesn't hold, or a bad command line).

**What it doesn't do:** run the readers or say what is inside an unreadable
file. It points at the add-on; running it is yours.

**Uses:** the kernel's `read`, `sealed`, `standing` and `read_words`.

**Never:** writes anything, or reads the key.
