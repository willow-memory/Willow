# Stewart crossover: a fan's files beside a real life

Sir Patrick Stewart died on 28 October 2026. This study sets a fictional
Star Trek fan, Wren Castellano, beside the real record of a few years of his
life (2020 to 2023: the three seasons of *Star Trek: Picard* and his memoir,
*Making It So*), and asks one thing: **can every word about him in her files
be shown to come from a source, with what the sources don't hold shown as
not held?** Her files end on 2026-10-22, six days before his death, so they
must not know of it.

Wren is fiction, and every file of hers says so on its first line. He is
not, so nothing about him is made up: her files name him only in lines
frozen here, before anything was asked, and each line is a fact two
publishers hold, a quote a source holds word for word, a planted trap the
checks must catch, or a line about her own life that states nothing about
him.

## The claim

1. **Every fact holds in two publishers.** Each of seven facts (the memoir
   and its year, the years *Picard* ran, its last season, Paramount+, the
   role in 1987, Professor Xavier, his birth in Mirfield in 1940) is found
   whole, every part in one passage, in sources from at least two of
   Wikipedia, Deadline, Variety and CNN; one of them is a host willow-mcp's
   web search trusts; and willows-grove's four checks pass on its sentence
   against those passages.
2. **What isn't held is shown, not repeated.** Four traps are planted in
   her files, each labelled as what it is: a friend's wrong fact (the
   memoir "a 2021 memoir"), a misquote, a reseller's "signed by Patrick
   Stewart", and a Klingon word typed in the wrong case. Each must be
   caught by the check named for it.
3. **Her files don't know what came after them.** Asked whether he died,
   her files hold no passage that says so, and no date in them is after
   2026-10-22.
4. **Parody is told from fact.** The Gerald canon's Sir Patrik Stewpott (a
   parody mirror, "always on a screen, never present", from willows-grove)
   is in the pile. Asked about him on a screen, the kernel finds it: Gerald
   shows up. Asked of the sources, nothing holds it.
5. **Nothing about him goes unseen.** Every line of hers that names him,
   the show or the memoir holds a frozen line word for word; any other is
   unseen, never sound, as Forge's measure panel counts what nothing
   measured.

## Five repositories, each with a part

| Repository | What it does here |
|---|---|
| Willow | the kernel, its rank and record; claim-check, quote-check, misquote, contradictions, words-tlh and make-it-so; this study |
| willows-grove | `seat_say.run_checks`, the seat's four checks (cites served, every box cited, nothing the boxes lack, quotes exact), on each fact's sentence; and the parody line, at its commit |
| willow-mcp | `web_search._trusted_host`, the hand-kept list of hosts it trusts, asked of each fact's sources |
| willow-bot | the one-script kernel's `verify`, run on the verdict record beside Willow's own |
| Forge | `measure_panel`'s rule that a thing nothing measured is unseen, never sound, applied to her lines; the pattern, not its code |

Nestor's seals are not used: nothing here is sealed, and no key but each
box's own, made for the run, is made or read.

## What is frozen

[FROZEN.json](FROZEN.json) holds each frozen file's SHA-256, and the tools'
from all five repositories with each one's commit;
`test_stewart_crossover.py` fails if a frozen file changes. A change is a
new freeze, in its own commit, with its reason.

- [sources.json](sources.json): eight sources by address, time and SHA-256,
  never their text. A wiki page is pinned at a revision and a data file at a
  commit, and held by its bytes. A news page changes by the hour (its
  sidebars rotate other stories, one of them a "Cause Of Death Revealed"
  headline), so it is held by its article's own lines: each line's SHA-256,
  and only those lines are read. [fetch.py](fetch.py) fetches them again and
  says of each whether it is held.
- [questions.json](questions.json): the seven facts with their claims and
  sentences, two quotes, four traps, five beats, every line of Wren's that
  may name him, the hit rule and seventeen pass rules.
- [run.py](run.py): judges every rule, and writes each as a verdict row on a
  kernel record outside the repo, with the SHA-256 of the results and of
  every tool.

## Decided by the person, before the freeze

- **Consent.** willow-mcp's consent gate holds back "a deceased relative",
  who can't consent. A public figure, as published obituaries and reference
  pages describe him, is outside that gate, and only such pages are used.
- **The parody stays in.** In the person's words: "Keep it in, if Gerald
  shows up, we're on the right track."

## Written after reading the sources

The sources were read before the freeze; the questions were not asked of
them. Written after reading, and so fitted to what they hold:

- which seven facts, and their sentences, which use the passages' own words
  so that grove's "nothing lacking" check can judge them (it was tried on
  boxes typed by hand, never on the sources);
- which lines of each news page are its article: from its first paragraph to
  its last, without its "RELATED:" links, video labels, photo credits and
  time stamps, and lines of under six words;
- the traps' wording, so that each is near enough to a source to be caught,
  and the second quote, the one CNN prints.

The Klingon Language Institute's page couldn't be used for words-tlh, since
its bytes change at every fetch; no source here is like that, since the news
pages are held by their lines.

## The dry run

Before the freeze, run.py ran once with every claim, quote, question and
line replaced by "qqqq zzzz", on a stub of Wren's files holding only a
fiction label and that nonsense. It ran twice, the second time after ids
were renamed, with the same verdicts. Every rule ran without an error; both
kernels verified the record (the boot and sixteen verdicts, none sealed),
and Willow's kernel verified it again with the verify verdict on it, 18
rows; the rules that ask for a fact or a quote failed, as they should with
nonsense; the rules that pass
when nothing is found (T3, G2) held; and the three that ask her files or
the whole pile (death, K1, M1) found the nonsense where the stub held it,
which shows her files are wired in. It could not see whether a real claim
finds its passages, or whether contradictions pairs T1's line with a
source's: those are what the run is for.

## How to run it

    python demo/stewart-crossover/fetch.py --to MIRROR
    python demo/stewart-crossover/run.py --mirror MIRROR --wren WREN \
        --work WORK --box BOX
    python kernel.py verify --box BOX

with willows-grove, willow-mcp, willow-bot and Forge checked out beside this
repository. Wren's files come next, after the freeze.

## Results

Not run yet.
