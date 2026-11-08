# The money hour: four people from willow's demos, and the real markets

Teo, Bernie, Hollis and Marisol, from four of willow's other demos, meet on
a video call about money once a month. Between them they repeat what the
Fed did, what unemployment was, what a yield was on a given day, what a
company spent buying back its stock, and what the new Fed chair said, and
each writes down a wager on the market before the day. Some of it is right
and some is what a cousin, a husband, the radio or a newsletter told them.

The claim: **every figure or quote about the world in their files is held to
the real record, and what the record doesn't hold is caught by the check
named for it.** The record is the [markets demo's pile](../markets-2026-11-05/),
fetched from FRED, the Treasury, the Fed, the ECB and SEC EDGAR on
2026-11-05. The people are fiction ([CHARACTER.md](CHARACTER.md)); the
figures are not, and every one of them is in [PLANTED.md](PLANTED.md) with
its source.

    python demo/markets-2026-11-05/fetch.py --to PILE --contact EMAIL
    python demo/markets-2026-11-05/mirror.py --from PILE --to MIRROR
    python demo/money-hour/make_life.py --mirror MIRROR
    python demo/money-hour/run.py --mirror MIRROR --work WORK      # about two minutes

## What the real record says, as the table met it

- The FOMC held at 3-1/2 to 3-3/4 percent from January to July 2026, then
  **raised** a quarter point on 16 September, to 3-3/4 to 4, and held on
  28 October with two votes against, for another raise.
- Kevin Warsh has chaired the press conferences since June 2026; April's
  was Jerome Powell's last.
- US unemployment was 4.2 percent for September 2026.
- The ECB's deposit facility rate went to 2.5 on 2026-09-16.

So a cousin's "they cut in September" and a radio's "Chair Powell said" are
the mistakes a person would make, and are the traps.

## How it runs

[run.py](run.py) takes a **slice** of the mirror, the fourteen sources (17 files) the
table talks about (seven FOMC statements, two press conference transcripts,
UNRATE, the S&P 500 closes, Treasury's 2026 curve, the ECB deposit rate and
Apple's 10-K), so every box builds in seconds and every passage an answer
cites is one somebody named. Lines over the kernel's 500 characters are
written as their sentences, every word kept (bug #89, as the Stewart
crossover does).

Then five boxes, each with a key made for the run: `sources` over the slice,
and one per person over their own folder. Each rule is judged by its own
add-on, by command line: claim-check, quote-check, misquote, pair-drift and
market-calls against the record, make_life's own check on the lines, and the
[money-hour stack](money-hour.md) on Teo's box (said, people, amounts,
coming-up, todo), which is what she would run before each call.

It stops where a person takes over. Each wager's close is proposed from the
slice's own S&P 500 rows, and its outcome waits on that person's seal, with
their key. Nothing here seals, and no key but each run box's own is made or
read.

## Results: run 1, 2026-11-05

**18 of 19 rules held; 1 failed.** In about ten seconds over the slice.
[results/run-1.json](results/run-1.json) is every outcome, with places, not
the sources' words.

| Rule | Verdict | What was found |
|---|---|---|
| R1 to R7 | held | each fact whole in a passage of its own source: the 16 September and 28 October statements, Treasury's curve (twice), UNRATE, the ECB's series, and the 10-K |
| V1 | held | verbatim in the 29 July transcript |
| T1 | held | "lower" is whole in no 2026 statement; "raise" is whole in 16 September's |
| T2 | held | misquote finds the July transcript and names always -> before and only -> just |
| T3 | held | within UNRATE, 3.9 is whole in no row for 2026-09-01; 4.2 is |
| T4 | held | the July transcript holds Chairman Warsh whole, and lacks powell |
| **T5** | **failed** | pair-drift lists **$95.8B** (the planted drift) and also **$0.27** |
| calls | held | four wagers on four records, made before the open; each close proposed, waiting on its seal |
| lines, after | held | every real-world line is frozen and present; none is dated after today |
| stack | held | said finds six quotes from the minutes, by Bernie, Hollis and Marisol, each dated |
| verify | held | all five chains hold; 0 sealed on any |

**T5, why it failed (fixed in freeze 3).** The 10-K says the dividend was raised "from $0.26 to
$0.27"; the newsletter says "raised the quarterly dividend to $0.27".
pair-drift reads "$0.26 to $0.27" as a range, one figure with both ends
(its card's own rule, made for "$180 to $190 billion"), so the summary's
$0.27 alone is not found in the full text. The summary is right; the
reading is wrong for "from X to Y", which is a change, not a range. The
summary was not rewritten to pass: the rule stands as frozen, the failure is
the finding, and it is worth filing against pair-drift.

The wagers, once each person seals: Hollis wrong (the 30th fell, 7580.07
from 7720.39), Marisol even, Bernie and Teo right.

## Freeze 2: across years and companies

The table's questions grew past one month and one company, so freeze 2
adds what willow does with a whole shelf of sources, and changes nothing
run 1 judged:

- **Two desk boxes, every line folded.** `fed` holds the FOMC's statements
  and minutes, 2023 to 2026; `filings` holds the 55 companies' latest
  10-Ks. `fed-unfolded` sits beside the first, built from the same files
  unfolded, to show what folding changes.
- **Marisol's timeline**, to hand to Lupe: every rate decision since 2023,
  each line cited, by [timeline](../../adapters/stdlib/timeline/).
- **When the minutes first said it**, by
  [first-mention](../../adapters/stdlib/first-mention/), folded and not.
- **Hollis's themes** ([themes.txt](themes.txt)) over the 55 10-Ks, by
  [sort](../../adapters/stdlib/sort/).
- **Teo's November letter**, in two drafts, each sentence put to the sources
  by [thesis](../../adapters/stdlib/thesis/); the final draft keeps one slip
  of her own (T6).
- **One page across the four records**, by
  [across](../../adapters/stdlib/across/) with digest: what waits on whom.
- **Three stacks:** [fed.md](fed.md) and [filings.md](filings.md) for the
  desks, and [money-hour.md](money-hour.md) with two new pools (digest,
  history).

## Results: run 2, 2026-11-05

**25 of 26 rules held; 1 failed, T5, as in run 1.** About two minutes.
[results/run-2.json](results/run-2.json).

| Rule | Verdict | What was found |
|---|---|---|
| run 1's 19 | as before | the same 18 held, T5 failed the same way |
| fold | held | tariffs are first in the minutes of **2025-01-29**, read directly and by first-mention on the folded box; the **unfolded** box says 2025-03-19, because January's mention is past its line's 500th character. Folded, 166 mentions in 14 files; artificial intelligence is first on 2024-05-01 |
| timeline | held | all 31 statements, each decision as the statement says it: 2023 r r r m r m m m, 2024 m m m m m l l l, 2025 m m m m m l l l, 2026 m m m m m **r** m (r raise, l lower, m maintain) |
| sort | held | every one of the 55 placed. Companies by the theme their filing holds most: 29 cyber, 18 rates, 8 AI, 1 tariffs (TJX), 1 climate (XOM). A long 10-K is read in parts and each part is placed on its own, so DUK and SO are in rates and cyber, and one part each of MS's and NEM's holds no theme. Cyber leads on volume: every 10-K now has a cybersecurity section, and sort places a file by the theme it holds most |
| thesis | held | final letter: 5 of 6 held, T6 short (lacks lower). Her first draft, in her own words: 1 of 4 held, the dated ones short, since a statement never writes its own date beside its decision |
| T6 | held | her slip is the one short sentence |
| across | held | one page, four records, each with its wager's outcome waiting on its seal |
| stacks | held | all three run; the Fed desk flags, the others print and pass |

**Two things to read, not just count.** thesis holds the letter's line 2
("maintain ... at 3-3/4 to 4 percent"), but the first passage it names is
**January's**, which says 3-1/2 to 3-3/4: the kernel reads 3-3/4 as 3, 3
and 4, so neighbouring ranges share every part. 28 October's statement is
among the passages holding it, and the rule asks for that, but a person
reading the letter's support should open the passage, not trust the count.
And the fold finding is bug #89's again: without folding, willow's answer
about when something was first said was ten weeks late, and nothing said so.

## Freeze 3: the fix, and run 3

Run 2's one failure, T5, was pair-drift's, not the newsletter's: it read
"from $0.26 to $0.27" as one range, so the summary's correct $0.27 looked
like drift. [pair-drift](../../adapters/stdlib/pair-drift/) now reads
"from A to B" as a change, two figures, each with the sign, scale and unit
they share; "$180 to $190 billion" is still one range. Its tests say both.
run.py now numbers its results by the next free run-N.json, so no run's
results are rewritten. Nothing else changed.

**Run 3, 2026-11-05: 26 of 26 rules held.** T5 now finds the planted
$95.8B in the summary only, and nothing else. Every other verdict is run
2's. [results/run-3.json](results/run-3.json).

## What is frozen

[FROZEN.json](FROZEN.json) holds the SHA-256 of questions.json, make_life.py,
run.py, the three stacks and themes.txt, and pair-drift's own code, as run 3
ran them, with each earlier freeze's hashes kept beside its reason; `test_money_hour.py` fails if one changes. Before the freeze one pass of run.py read pair-drift's figures in
the wrong shape ($95.8 billion where it prints $95.8B); run.py was fixed to
read its own form, and nothing else changed. A change now is a new freeze,
with its reason.
