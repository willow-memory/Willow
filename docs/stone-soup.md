# Stone soup: squeezing a pile

One pile of real public data, and add-on after add-on dropped in until
something nobody asked for comes out. Everything here ran on the pile the
[markets demo](../demo/markets-2026-11-05/) fetches, through boxes the
[money hour demo](../demo/money-hour/) builds. The output shown is real,
trimmed; the failures are shown too, because knowing where a tool misreads
is half of reading with it.

## 1. The stone: one pile, fetched once

```
$ python demo/markets-2026-11-05/fetch.py --to PILE --contact YOUR-EMAIL
froze 944 sources, 2 failed, 664.6 MB
$ python demo/markets-2026-11-05/mirror.py --from PILE --to MIRROR
1297 files in MIRROR
```

Every source is the snapshot add-on's, as it came, with its SHA-256; a
publisher's error page that came with a 200 is set aside, not kept as data.
`--contact` is only for SEC EDGAR, and goes to sec.gov alone.

**First lesson: fold before you ask.** The kernel reads only the first 500
characters of a line, and a Fed minutes paragraph is two thousand. Asked
when the minutes first said "tariffs", the unfolded box answered March 2025;
broken at its sentences, every word kept, it answered January 2025. Ten
weeks, and nothing said a passage had been cut. The money hour's
[run.py](../demo/money-hour/run.py) has the `fold` it uses.

## 2. The water: a box for each question

A box over everything is slow (one question over 665 MB took seven and a
half minutes) and a box over the wrong thing answers the wrong question. So
each question gets a box over what it's about:

| Box | Pile | For |
|-----|------|-----|
| `fed` | the FOMC's statements and minutes, 2023 to 2026, folded | what the Committee wrote, and when |
| `presconf` | the press conference transcripts, folded | what the chair said aloud |
| `filings` | the 55 latest 10-Ks, folded | what companies say about themselves |

For many questions of one big folder, [scan](../adapters/stdlib/scan/)
indexes it once (1.25 million passages in 43 seconds) and answers each in
about ten; split a folder past a few million passages into several indexes,
or the machine runs out of memory.

## 3. The first handfuls: add-ons that read words

**[timeline](../adapters/stdlib/timeline/)** put every rate decision since
2023 in order, each line cited, and the decisions it read matched each
statement read directly, all 31:

```
2024-09-18  statements/20240918.html.txt:557  ... the Committee decided to lower the target range ...
2026-09-16  statements/20260916.html.txt:555  The Committee decided to raise the target range ...
```

**[first-mention](../adapters/stdlib/first-mention/)** dated a worry: tariffs
first in the minutes of January 2025, artificial intelligence in May 2024.

**[sort](../adapters/stdlib/sort/)** placed every one of the 55 10-Ks by a
person's own themes in 11 seconds. It places a file by the theme it holds
most, so on 10-Ks cybersecurity wins on volume: every one now has a
cybersecurity section. Read it as "mostly about", not "mentions".

**[thesis](../adapters/stdlib/thesis/)** put a letter's every sentence to the
sources. Written naturally ("On 2026-09-16 the Committee decided to raise..."),
one of four held: a statement never writes its own date beside its
decision. Written in the sources' own words, five of six held, and the sixth
was the planted slip.

## 4. The surprise: chaining two add-ons

[dialect](../adapters/deps/dialect/) lists the words a pile uses far more than
the world does. Feed each one to first-mention, and the pile's vocabulary
gets a history. [dialect-dates](../adapters/deps/dialect-dates/) does both
in one run:

```
$ python adapters/deps/dialect-dates/dialect_dates.py --box BOX --top 8
  2023-03-22  2026-04-29  disinflation     41 mentions in 19 files
  2023-07-26  2025-12-10  restrictiveness  12 mentions in 8 files
  2025-12-10  2026-09-16  rmps             26 mentions in 5 files
```

On the minutes that gave words nobody had asked about: "buildout", first in
January 2026 ("the financing of the AI-related infrastructure buildout in
opaque private markets warranted monitoring"); stablecoins in July 2025;
"disinflation" last in April 2026, five months before the Committee raised
rates. On the press conference transcripts it gave tariffs at the podium on
7 November 2024, two meetings before the minutes, and, because transcripts
name every questioner, a dated who's-who of the Fed press corps.

## 5. What didn't season the pot

| Add-on | What it did on this pile | Why |
|--------|--------------------------|-----|
| [reading-level](../adapters/stdlib/reading-level/) | scored the statements' menus | a saved web page is mostly navigation; count the policy text yourself |
| [contradictions](../adapters/stdlib/contradictions/) | paired the unemployment rate with the 2 percent goal | two amounts in sentences that sound alike are not a disagreement |
| [claim-check](../adapters/stdlib/claim-check/), [thesis](../adapters/stdlib/thesis/) | held "3-3/4 to 4 percent" by January's 3-1/2 to 3-3/4 | the kernel reads 3-3/4 as 3, 3 and 4; open the cited passage |
| [pair-drift](../adapters/stdlib/pair-drift/) | before a fix, flagged a summary's correct "$0.27" | it read "from $0.26 to $0.27" as one range; it now reads "from A to B" as a change, so "runs from 302 to 375" reads as a change too: word both sides alike |
| [dialect](../adapters/deps/dialect/) | listed "wouldn" and "hasn" | a curly apostrophe splits a contraction |
| [pile-poetry](../adapters/stdlib/pile-poetry/), [quiz](../adapters/stdlib/quiz/) | verse ending "Flickr page", a blank in a press-release header | the page's leftovers are passages too |

None of these is a reason to leave the add-on out. Each says what the tool
reads, and a person who knows that reads its answer correctly.

## 6. Serve it: a stack

When a chain earns its place, write it down as a [stack](../adapters/stdlib/stack/)
so the next refresh of the pile runs it in one command. The money hour's
[fed.md](../demo/money-hour/fed.md) and [filings.md](../demo/money-hour/filings.md)
are two:

```
$ python adapters/stdlib/stack/stack.py --box BOX --stack demo/money-hour/fed.md
```

The recipe, for any pile of your own: fetch once and pin it; fold long
lines; a box per question; the word readers first; chain the one that names
words into the one that dates them; then write down where each one misread,
next to what it found.
