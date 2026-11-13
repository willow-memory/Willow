<!-- willow-addon
section: Finding things
line: Dates that admit doubt ('about 1880', 'sometime in March') read and kept with their doubt, in EDTF.
source: new
added: 2026-10-27
version: 0.1.1
writes: nothing
network: none
role: page
-->
# fuzzy-dates

A family history says "about 1880", a letter "sometime in March", a label
"the 1990s". The kernel's dates are exact days, so these say nothing to it;
this reads them with the doubt kept, in EDTF (ISO 8601-2, the library
world's format for exactly this), each with the phrase as written and where
it is.

```
python adapters/stdlib/fuzzy-dates/fuzzy_dates.py --box DIR

1880~      about 1880             family/gran.md:4
188X       the early 1880s        family/gran.md:9
1944-21    spring 1944            letters/war.md:2
XXXX-03    sometime in March      notes.md:7
1880/1885  between 1880 and 1885  family/tree.md:3
../1900    before 1900            family/tree.md:8
3 fuzzy dates, the doubt kept
```

**The grammar is words, small and said in full**, and nothing else is
guessed: about, around, circa, roughly or approximately before a month and
year or a year (`1880~`, `1972-03~`); maybe, possibly or perhaps before a
year (`1880?`); a decade, with or without early, mid or late (`188X`);
spring, summer, autumn, fall or winter of a year (EDTF's seasons, `1944-21`
to `1944-24`); before or after a year (`../1900`, `1950/..`); between one
year and another, or from one to another (`1880/1885`); sometime in a
month (`XXXX-03` for a year unsaid); early or late in a year, the early or
latter part of it, or the close, end or beginning of it (`1872`); and a year
said as two digits, in '79 or of '79, or a season of it, spring of '79
(`XX79`, `XX79-21`: the century is unsaid, so the format leaves it
unspecified and the add-on does not choose one). A year is four digits, 1000
to 2999, so a price, a page number or "about 500 people" never reads as one,
and a bare question mark is a sentence's, not a date's; a two-digit year
needs its apostrophe, and `'60s` is a decade, not a year. Early, mid and late
stay in the phrase shown, not the EDTF: the decade, or the year, is what the
format can carry.

The two-digit and early-or-late shapes came from reading a county's old
histories, where "late in 1893", "very early in the year 1873" and "in the
spring of '79" are how a date is said and none of the other shapes read them.

**What admits no doubt is left to the kernel.** A plain "March 1972" and an
exact day are `newest`'s job; this reads only the doubt, so the two never
read the same words. Overlapping readings keep the first, so the years
inside "between 1880 and 1885" read once, as the span.

On willow's demo folders, Hollis's piano ledger gives 91 fuzzy dates, most
of them instruments logged by their build decade ("1910s upright");
Stewart's crossover notes give one ("from 2020 to 2023"); the other seven
folders have none, and say so.

It only reads, and the same folder gives the same bytes. Exit codes, the
kernel's: 0 fuzzy dates found; 42 none; 2 refused.

**Uses:** the kernel's `chunks` and `config`.

**Never:** changes your files; writes anything, even the record; reads a
doubt the words don't say, or a bare number as a year.
