# Stewart crossover: a fan's files beside a real life

Sir Patrick Stewart died on 28 October 2026. This study sets a fictional
Star Trek fan, Wren Castellano, beside the real record of a few years of his
life (2020 to 2023: the three seasons of *Star Trek: Picard* and his memoir,
*Making It So*), and asks one thing: **can every word about him in her files
be shown to come from a source, with what the sources don't hold shown as
not held?** Her files are as she left them on 2026-10-22 (her last entry
is from 2023), six days before his death, so they must not know of it.

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
2. **What isn't held is shown, not repeated.** Five traps are planted in
   her files, each labelled as what it is: a friend's wrong fact (the
   memoir "a 2021 memoir"), a misquote, a reseller's "signed by Patrick
   Stewart", a Klingon word typed in the wrong case, and (from freeze 2) the
   same friend's wrong birth date, set beside the sources' own. Each must
   be caught by the check named for it.
3. **Her files don't know what came after them.** Asked whether he died,
   her files hold no passage that says so, and no date in them is after
   2026-10-22.
4. **Parody is told from fact.** The Gerald canon's Sir Patrik Stewpott (a
   parody mirror, "always on a screen, never present", from willows-grove)
   is in the pile. Asked about him on a screen, it is among the passages
   that hold the question whole: Gerald shows up. Asked of the sources, nothing holds it.
5. **Nothing about him goes unseen.** Every line of hers that names him,
   the show or the memoir holds a frozen line word for word; any other is
   unseen, never sound, as Forge's measure panel counts what nothing
   measured.

## Five repositories, each with a part

| Repository | What it does here |
|---|---|
| Willow | the kernel, its rank and record; claim-check, quote-check, misquote, words-tlh and make-it-so (and contradictions, in runs 1 and 2); this study |
| willows-grove | `seat_say.run_checks`, the seat's four checks (cites served, every box cited, nothing the boxes lack, quotes exact), on each fact's sentence; and the parody line, at its commit |
| willow-mcp | `web_search._trusted_host`, the hand-kept list of hosts it trusts, asked of each fact's sources |
| willow-bot | the one-script kernel's `verify`, run on the verdict record beside Willow's own |
| Forge | `measure_panel`'s rule that a thing nothing measured is unseen, never sound, applied to her lines; the pattern, not its code |

Nestor's seals are not used: nothing here is sealed, and no key but each
box's own, made for the run, is made or read.

## What is frozen

[FROZEN.json](FROZEN.json) holds each frozen file's SHA-256, and the tools'
from all five repositories with each one's commit, for the freeze in force
(freeze 3), with each earlier freeze's file hashes kept beside its reason;
`test_stewart_crossover.py` fails if a frozen file changes. A change is a
new freeze, in its own commit, with its reason.

- [sources.json](sources.json): eight sources by address, time and SHA-256,
  never their text. A wiki page is pinned at a revision and a data file at a
  commit, and held by its bytes. A news page changes by the hour (its
  sidebars rotate other stories, one of them a "Cause Of Death Revealed"
  headline), so it is held by its article's own lines: each line's SHA-256,
  and only those lines are read. [fetch.py](fetch.py) fetches them again and
  says of each whether it is held, and (from freeze 2) writes any line
  longer than the kernel reads as its sentences, one a line, every word kept
  (known bug #89: the kernel drops a line's text past its 500th character).
- [questions.json](questions.json): the seven facts with their claims and
  sentences, two quotes, five traps, five beats, every line of Wren's that
  may name him, the hit rule and eighteen pass rules.
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

## Freeze 2

Run 1 (below) failed two rules, and the person asked for a new freeze. It
changes three things, each for a reason run 1 showed, and nothing else:

- **fetch.py folds long lines.** "Make it so" is in CNN's page past the
  kernel's 500th character of its line, where nothing built on the kernel
  reads (bug #89, filed from this run). A line over 500 characters is now
  written as its sentences, one a line; no word is dropped or changed. The
  quote rule is as it was.
- **T1 is judged by claim-check alone.** contradictions reads a date, never
  a bare year, and no source gives the memoir more than its year, so T1's
  second check could not have held. Its first, which held, is its rule now.
- **T5 is added for contradictions:** "Kati swears Patrick Stewart was born
  on 13 July 1941 in Mirfield." The sources give his birth as a full date,
  so contradictions can read both sides. It was chosen knowing that, after
  run 1, and so it tests the tool on a case it is built for, not a blind
  one.

Before freeze 2, run.py ran once more with nonsense, on the folded sources:
no error, no line over 500 characters left in them, and the same verdicts as
the first dry run, with T5 failing as nonsense must.

## Freeze 3

Run 2 (below) failed two rules, and the person asked for another freeze.
It changes two rules, each for a reason run 2 showed, and nothing else:

- **T5 is two claim-checks, side by side.** The kernel reads a date only in
  figures (2026-10-14, 21/10/2026), and no source writes a date about him
  so: his birth is "July 13, 1940" or "13 July 1940" in prose, and figures
  only inside wiki templates and citations. So contradictions can't read
  either side of any claim about him here, and it leaves the study. T5 now
  holds when the wrong claim ("born 13 July 1941 Mirfield") is in no source
  and its truth ("born 13 July 1940 Mirfield") is whole in two publishers,
  the two shown together. No source's words are rewritten to make a date.
- **G1 asks the same question of every passage.** "Patrick Stewart on a
  screen" is asked with claim-check on the whole pile, which lists every
  passage holding all its parts, not the kernel's top three, which run 2's
  folded sources filled. Gerald shows up if the parody's passage is among
  them.

Before freeze 3, run.py ran once more with nonsense: no error, and the
same verdicts as before, T5 and G1 failing as nonsense must.

## How to run it

    python demo/stewart-crossover/fetch.py --to MIRROR
    python demo/stewart-crossover/run.py --mirror MIRROR --wren WREN \
        --work WORK --box BOX
    python kernel.py verify --box BOX

with willows-grove, willow-mcp, willow-bot and Forge checked out beside this
repository. Wren's files are made by [make_life.py](make_life.py) into
`life/` (`--check` holds them to the frozen lines); they were written after
freeze 1, and only the frozen lines in them name him.

## Results: run 1, 2026-10-30

Every source held when fetched (each news page's frozen lines all there).
**15 of the 17 rules held; 2 failed.** The verdicts are rows on a kernel
record, copied to [results/record.jsonl](results/record.jsonl) without its
key; `kernel.py verify` says "the chain holds: 18 rows, 0 sealed", and so
does willow-bot's. [results/run-1.json](results/run-1.json) is every
outcome, less the words misquote printed from CNN's line (so its hash is not
the record's `results_sha256`, which is of the whole file).

| Rule | Verdict | What was found |
|---|---|---|
| facts | held | every fact whole in 2 or 3 publishers: Wikipedia with Deadline (memoir 2023, the last season), with Variety and CNN (2020 to 2023), Deadline and CNN (Paramount+, 1987, Mirfield 1940), Deadline and Variety (Xavier) |
| facts-trusted | held | Wikipedia, the one host here willow-mcp trusts, holds each; it trusts none of deadline.com, variety.com or edition.cnn.com |
| facts-grove | held | the seat's four checks on each sentence: cites served, every box cited, nothing the boxes lack, and no quote ("na") |
| quotes | **failed** | the CNN line "the distinction between Jean-Luc Picard and Patrick Stewart became thinner and thinner" found verbatim; **"Make it so" not found verbatim anywhere** |
| T1 | **failed** | claim-check found no source with "memoir Making It So 2021" (held), but **contradictions didn't set Kati's line beside a source** |
| T2 | held | the misquote isn't in any source; misquote's closest passage is CNN's, the line that holds the real quote |
| T3 | held | no source holds "Patrick Stewart signed Enterprise model": the seller's claim stays the seller's |
| T4 | held | "qapla'" is in boQwI' only as "same words", never verbatim (it spells `Qapla'`); the kernel's words for the two are the same, the cost words-tlh's card names |
| death | held | no passage of hers holds "Patrick Stewart died" |
| dates | held | no date of hers after 2026-10-22 |
| G1 | held | asked "Patrick Stewart on a screen", the kernel served the Gerald line second: Gerald shows up |
| G2 | held | no source holds Sir Patrik Stewpott, always on a screen, never present |
| K1 | held | "nuq 'oH Qapla'?" through words-tlh asked "qapla" and was served boQwI''s entries, after Dev's chat line |
| M1 | held | make-it-so wrote the order, "engage: rewatch Star Trek: Picard, season one", beside its passages, and check said it holds; it was never run |
| unseen | held | every line of hers naming him, the show or the memoir is a frozen line |
| fiction | held | each of her eight files says so first |
| verify | held | both kernels, on the record |

## What failed, and why

**"Make it so" is in CNN's page, and the kernel never reads it.** The line
that says it ("His oft-repeated line, “Make it so,” became a signature
tagline.") is the end of a 542-character paragraph ("Make it so" starts at its
503rd), and `kernel.chunks`
keeps a line's first 500 characters (`line[:MAX_CHUNK]`) and drops the rest
without a word. So no tool built on the kernel (quote-check, claim-check,
bite) can find anything past the 500th character of a long line, here or in
any folder; Wikipedia's paragraphs often run longer. LIMITS.md and BUGS.md
don't say so. The kernel isn't changed here: this is said for the
maintainer, and quote1 stays failed.

**contradictions reads a date, not a year.** Kati's "a 2021 memoir" and the
sources' 2023 are bare years, and contradictions takes the kernel's reading
of a date, which never makes a day out of a month, let alone a year: given
two lines that differ only by "2021" and "2023" it says nothing in the
folder states a date. The trap was frozen with a check that could not have
caught it; the mistake is in the rule, made before the freeze, not in the
tool, which does what its card says. claim-check caught the wrong year
alone.

Neither is fixed by changing a frozen file. A freeze 2 would be its own
commit, with these reasons.

## Results: run 2, from freeze 2, 2026-10-30

Every source held. **16 of the 18 rules held; 2 failed**, one of them new.
The record is [results/record-2.jsonl](results/record-2.jsonl) (both
kernels: "the chain holds: 19 rows, 0 sealed"), every outcome
[results/run-2.json](results/run-2.json), less misquote's words as before.

| Rule | Run 1 | Run 2 | What changed |
|---|---|---|---|
| quotes | failed | **held** | with CNN's long line folded, "Make it so" is found verbatim on it |
| T1 | failed | **held** | judged by claim-check alone, which held both times |
| T5 | (new) | **failed** | claim-check held (no source has a birth in 1941), but contradictions didn't set the line beside a source |
| G1 | held | **failed** | the Gerald line is no longer among the three passages served |
| the other 14 | held | held | facts, facts-trusted, facts-grove, T2, T3, T4, death, dates, G2, K1, M1, unseen, fiction, verify |

## What failed in run 2, and why

**T5: the kernel reads dates in figures only.** Its `newest` reads an ISO
date, a compact one, or day and month in figures with a four-digit year
(21/10/2026). "13 July 1941" and "July 13, 1940", as Kati and the sources
write them, are not dates to it, so contradictions found no date on either
line, and T5 could never have held. That was knowable from the kernel's own
docstring before freeze 2, and was missed: the mistake is in the freeze,
again, not the tool.

**G1: folding moved the ranking.** Freeze 2 cut Wikipedia's long
paragraphs into sentences, so more, shorter passages of his article hold
"Patrick Stewart" and "screen" together, and three of them now fill the
kernel's top three ahead of the Gerald line, which run 1 served second.
The parody is still in the pile and G2 still holds (no source has it); it
just doesn't surface first. A change made to fix one rule broke another,
and it is written down as that.

Run 1's results stand beside these. A freeze 3 would be the person's call,
in its own commit with its reasons.

## Results: run 3, from freeze 3, 2026-10-30

Every source held. **All 18 rules held.** The record is
[results/record-3.jsonl](results/record-3.jsonl) (both kernels: "the chain
holds: 19 rows, 0 sealed"), every outcome [results/run-3.json](results/run-3.json).

| Rule | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| facts, facts-trusted, facts-grove | held | held | held |
| quotes | failed | held | held |
| T1 | failed | held | held |
| T2, T3, T4 | held | held | held |
| T5 | (new) | failed | **held**: no source has a birth in 1941; Deadline and Wikipedia hold 13 July 1940 in Mirfield, whole |
| death, dates | held | held | held |
| G1 | held | failed | **held**: the Gerald line is first of seven passages holding "Patrick Stewart on a screen" whole |
| G2, K1, M1, unseen, fiction, verify | held | held | held |

Three freezes to hold every rule is itself a result. Each freeze changed
only what the run before it showed broken, and each is in its own commit
with its reason. The reasons were a kernel bug (#89), the kernel's reading
of dates (figures only), and a side effect of the first fix (ranking moved).
None loosened a rule: each made the check ask the sources what the rule
always meant. Runs 1 and 2 stand beside run 3, failures and all.

