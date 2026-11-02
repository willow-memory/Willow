<!-- willow-addon
section: Finding things
line: Everyone your files name, and every place each is mentioned.
source: new
added: 2026-10-27
writes: nothing
network: none
-->
# people

The roster of the people your folder speaks of, most mentioned first, and,
named, any one of them with every place they're mentioned.

```
$ python adapters/stdlib/people/people.py --box DIR
  654  Nell       in 24 files, 2021-03-05 to 2026-09-20
  553  Dad        in 32 files, 2021-03-07 to 2026-10-18
   26  Ferris     in 6 files, 2021-03-26 to 2026-08-21
9 people, by what the files do with a name

$ python adapters/stdlib/people/people.py --box DIR ferris
2021-03-26  logbook/2021.txt:112          Ferris came by about the Steinway.
2026-08-21  messages/sms_dad_2026.txt:81  [2026-08-21 19:36] Dad: Ferris came by, we played cards
27 mentions of "Ferris" in 6 files
```

**A name is known by what the files do with it**, not by a list of names: it
is written capitalized at least as often as lowercase ("Walked" starts
sentences, but "walked" outnumbers it, so it is no one; a "kati" typed
quickly in a chat doesn't cost Kati her name); at least once it does a
person's thing — it speaks (a chat's stamped speaker line, "Kati said" and
the other speech verbs), or it comes, calls, rings, visits, meets, asks,
tells, thanks, pays or helps, or is rung, met, told or thanked by name — and
it isn't a month's or a weekday's name, which also come and go. Every word
that passes is a person, and the roster says what it counted, never who
matters: a town someone "left" can stand in it (Odile's roster seats a
Creek), and reading the roster is how you'd notice.

**A mention is a line.** Every line that writes the name, in any case,
counts once and is cited; the drill-down lists them oldest first, dated by
the line, the nearest date above it in its file, or the file's name, undated
mentions last, and the roster's spans skip what no date reaches.

On willow's demo folders the rosters come out as the families they are:
Hollis's Nell, Dad, Mom, Dana, Ferris and Dr Marchetti; Bernadette's Bernie,
Gerry, Mags and Siobhán; Teodora's Teo, Sam, Row, Maisie, Ana and Jo;
Odile's Kati, Harriet, Everett and Cyrus — 44 names for Odile, a few of them
places that moved.

It only reads, and the same folder gives the same bytes. Exit codes, the
kernel's: 0 people found; 42 none, or WHO is no one the files name; 2
refused.

**Uses:** the kernel's `chunks`, `words`, `newest`, `FUNCTION` and `config`.

**Never:** changes your files; writes anything, even the record; keeps a
list of names; says who matters.
