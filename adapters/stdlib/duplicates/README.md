<!-- willow-addon
section: Finding things
line: Passages that say the same thing in two files, and which one is newer.
source: new
added: 2026-10-27
writes: nothing
network: none
tags: no-install, offline, read-only, search
-->
# duplicates

Every passage of your folder that says the same thing as a passage in
another file, grouped, each copy with its date and place, and the newest
named: the note you copied into a second file and then kept editing in only
one of them, the recipe living in three places, the boilerplate a sender
mails you every month.

    python adapters/stdlib/duplicates/duplicates.py --box DIR

    2 copies, newer garden/2026-05-02.md:3
      2026-05-02  garden/2026-05-02.md:3   Tomatoes want sun and deep watering.
      2024-04-01  garden/2024-04-01.md:3   Tomatoes want sun and deep watering!
    2 copies, which is newer the files don't say
      undated     recipes/bread.md:1       Knead, prove twice, bake at 230.
      undated     old/notes.md:40          Knead, prove twice, bake at 230.
    2 passages said in two or more files, 4 copies in all

**What counts as the same thing.** Two passages whose words match, in order,
read the kernel's way (its `words`): case, punctuation and spacing aside,
nothing else forgiven. A word changed is another passage, not a copy, and a
date is a word: "paid rent" on two days is two facts. A passage under 8
words is never reported, since a short line ("see above", a heading) repeats
without being a copy of anything. Near-copies are another job:
[diverge](../diverge/) says where two folders part, line by line.

**Which one is newer.** A copy's date is the latest its own text says, read
as the kernel reads one (its `newest`; 11/03/2026, either way round, is
never guessed), else the date its file is named for. The newest copy is
named only when its date beats every other; copies tied to the day, or a
newest with no date, leave it unsaid: your files don't say which is newer.

**One file's repeats are the file's business.** The same line twice in one
log counts only when the passage is also in another file; then every copy is
listed, the same file's too.

On willow's demo folders it finds Bernadette's library-hold emails, eight
copies of the same collection notice, newest first and named; Hollis's
folder holds 48 passages said in two or more files, most of them a bank's
and a pharmacy's boilerplate, which is the honest answer: a sender really
does say the same thing in many files.

It only reads, and the same folder gives the same bytes. Exit codes, the
kernel's: 0 duplicates found; 42 none of 8 words or more; 2 refused.

**Uses:** the kernel's `chunks`, `words`, `newest` and `config`.

**Never:** changes your files; writes anything, even the record; calls a
passage a copy on anything but its words, in order.
