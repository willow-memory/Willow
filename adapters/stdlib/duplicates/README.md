<!-- willow-addon
section: Finding things
line: Passages that say the same thing in two files, and which one is newer.
source: new
added: 2026-10-27
version: 0.1.0
writes: nothing
network: none
role: page
-->
# duplicates

Every passage of your folder that says the same thing as a passage in
another file, grouped, each copy with its date and place, and the newest
named: the note you copied into a second file and then kept editing in only
one of them, the recipe living in three places, the boilerplate a sender
mails you every month.

    python adapters/stdlib/duplicates/duplicates.py --box DIR [--runs]

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

**When the passages don't line up: `--runs`.** A passage is where the kernel
cut the file, at a blank line or after 500 characters. The same text with
its paragraphs broken in other places, or cut at the 500th character on a
different word, is cut differently in two files, so its passages never
match and this finds one copy where the files share a hundred words. With
`--runs` the passages are not compared. Each file is its words in order, read
the kernel's way, and a run of 8 words or more that two files share is a
copy, wherever each file broke its paragraphs:

    3 copies of a run of 94 words
      cox-1905-part17.html.txt:43          to be as much angry as frightened i will not give you any...
      pioneer-reminiscences-1916.txt:9062  to be as much angry as frightened i will not give you any...
      seward-county-reminiscences.txt:121  to be as much angry as frightened i will not give you any...

A word in order is still the only thing a copy is: a word changed ends the
run (so "rises" and "arises" end one), and so does a word that one file breaks
across two lines. A run also ends where the files that share it change, so a
stretch three files hold and the stretch after it that only two hold are two
runs, each listing the files that hold it. Each copy is shown at the line its
first word is on, with no date, since which is newer is the other mode's
question. The runs mode reads every file's words into memory, so it suits a
folder of books and pages, not a folder of hundreds of thousands of passages.

On 86 files of a Nebraska county's histories, the plain mode found 170
passages said in two files, and `--runs` found 543 runs, 50 of them between
a book of settlers' reminiscences and the chapter of the county history it
repeats (about 1,560 words, the longest 94, a settler's account of an Indian
scare that three files hold). It also finds what a
website repeats on every page: run it on pages cut down with the web-pages
add-on's `--body-only`, or the menu is the longest thing it reports.

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
