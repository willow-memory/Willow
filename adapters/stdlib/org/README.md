<!-- willow-addon
section: Reading more kinds of files
line: Org-mode files as plain lines, Org's markup taken off and each outline entry its own passage, cited by the .org file's own lines.
source: new
added: 2026-11-02
writes: to
network: none
role: reads
output: mirror
reads: .org
-->
# org

Your Emacs Org files (agenda, journal, notes) as the plain lines they say.

    python adapters/stdlib/org/org.py mirror --from FOLDER --to MIRROR

The kernel reads an .org file as it is, stars, drawers, `#+` lines, link
brackets and all, and an agenda with no blank lines is a few long passages,
each dated by the latest date anywhere in it. The mirror has the same number
of lines as the source, and each line is the source's line with Org's markup
taken off, so a passage found in the mirror is on that same line of the .org
file:

    Home › TODO [#A] Ring the vet :home:pets:
    SCHEDULED: 2024-03-05 09:00 +1w
    CLOCK: 2024-03-04 10:00 to 11:30 => 1:30
    Tomato; 2024-02-10; 2

**It adds no word of its own.** A word written into passage after passage is
half of any two-word question, and would answer one about something your
files don't hold. So TODO, SCHEDULED, CLOCK, a property's name and a checkbox
stay as Org wrote them, and only the markup comes off. The tests hold it: the
mirror's words are the source's, and no word but a date's digits is in most
passages of a file.

| Org | The mirror |
|---|---|
| a headline | its text as written (keyword, priority, cookie, tags), stars off. A heading with only headings under it is blank and said once, before the headline below it (`Garden › Tomatoes › Water them`), so each part of an outline is its own passage |
| a timestamp, active or inactive | its date and time without brackets or day name: `2024-03-03 10:00`; a range as `2024-03-03 to 2024-03-05`; a repeater or warning as written (`+1w`, `-7d`); a diary expression as written |
| a property drawer | each `:KEY: value` as `KEY: value`, the drawer's own lines blank; an ID or CUSTOM_ID blank, since it is a link's target and org-roam writes one into every note |
| a logbook | its lines as written, timestamps as above |
| `#+TITLE`, `#+SUBTITLE`, `#+AUTHOR`, `#+DATE`, `#+FILETAGS`, `#+CAPTION` | `title:`, `subtitle:`, `author:`, `date:`, `filetags:`, `caption:`; every other `#+` line is blank |
| a source, example or fixed-width block | kept as written, its markers blank |
| a quote, verse or other block | its text, markup off, its markers blank |
| a comment, a comment block, an export block (an html or latex block in older Org) | blank |
| a link | its description, or its target when it has none |
| emphasis | the markers taken off where Org reads them as markup, never inside a path like /usr/bin or a name like snake_case |
| a table | each row its cells, `Tomato; 2024-02-10; 2`, an empty cell left out; the header (the first row, when a rule is under it) moved down onto that rule, so it begins the passage its rows are in; a later rule and the formulas blank |

A header written beside every value would be in every passage of a long
table, so it is said once. The cost: a row in a later passage of a long table
no longer names its columns, so "what's in bed 3" finds "3" only beside its
plant.

Each file (.org or .org_archive) is written to MIRROR at the same relative
path with .txt added. FOLDER is only read: hidden folders and files are
skipped, and nothing is written inside it. A file with nothing to say, or
that can't be read, is skipped and counted, never a crash:

    wrote 3 files to MIRROR; skipped 1

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`); Python's
standard library for the format.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, or goes online.
