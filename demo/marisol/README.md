# Marisol's island

A fictional teacher's folder, built so each kind of file meets the add-on that
reads it, and so a grant draft with six claims in it can be checked against her
own folder and the real sources. Frozen once ([FROZEN.json](FROZEN.json)) and
run once; the result is below, with what failed.

- [CHARACTER.md](CHARACTER.md): who she is and how her work writes itself down.
- [PLANTED.md](PLANTED.md): the answer key, written before the generator.
- [questions.json](questions.json): every question, the hit rule and every pass
  rule, frozen before the run.
- `python3 demo/marisol/make_life.py` writes `life/` and `names.txt`, the same
  bytes every run; `--check` holds the written files to PLANTED.md.
- [sources.json](sources.json) keeps the real sources by address, time and
  SHA-256, never their text; `python3 demo/marisol/sources.py fetch DIR` gets
  them again and `check DIR` compares hashes offline. One source (a NBC New York
  page) could not be fetched and no claim depends on it.
- [run.py](run.py) is the run; [results/](results/) holds what it wrote.
- [handoff/](handoff/) is a separate, small thing: a zip with instructions for a reviewer to
  check and seal one Spanish sentence from their own box, and instructions for one
  reviewer in particular. It holds no key and no personal document.

Everything about the people, the school and the companies is invented. The
real facts are Section 936's phase-out (the 1996 Act scheduled its repeal for
2005), Hurricane Maria on 2017-09-20, LUMA taking over the grid on Tuesday,
June 1, 2021 (the NBC page is dated June 2), and NSF award 2305699 ("NSF
Engines - Type 1", 05/15/2023 to 04/30/2025, $999,903).

## The run

No model was asked. One box holds her folder, without the draft whose claims
are being checked, read through its add-ons, beside the saved real sources. The
kernel serves, the tools find where to read, a person decides.

    python3 demo/marisol/sources.py fetch DIR
    python3 demo/marisol/make_life.py
    python3 demo/marisol/run.py --life demo/marisol/life --sources DIR --work W --box B

Run 1 (`results/run-1.json`, SHA-256 `68666e72ec21688a936bfc81b860982fa32e1eb407fe7c1cd06fcb0174f55d36`), judged against the rules frozen
before it. Five held and one did not:

| Rule | | What happened |
|---|---|---|
| served | **failed** | 7 of 9 questions did what was frozen; the repeal question and the brother question did not (below) |
| gap | held | An English claim about the Spanish log found nothing (the predicted gap); the same claim in Spanish found it. `contradictions` did not join her father's year to her own note's |
| amounts | held | `amounts` read the receipts: they total $14,873.50 and none is $40,000 |
| quotes | held | `quotes` called the draft's quotation "almost" and named the dropped word, "alone" |
| unsealed | held | No seal or decline row: code never approves |
| verify | held | `kernel.py verify` holds on the evidence box and the verdict box |

**What failed.** The brother question asked, in Spanish, how much her brother sent for the
batteries. The mail reader writes an email as a header passage and body
passages; the question's words (Tomás, baterías) matched the header, which was
the only passage served, and the line with the $6,000 was never served. The repeal question asked
when the credit was repealed; the kernel ranked the NBER paper's title lines and
another CRS passage above the one that says "ultimate repeal in 2005", which is
in the pile. Both are misses of the kernel's rank, not of the folder. Neither
rule was changed after seeing this.

*Corrected by run 3 (below):* the repeal half of this is wrong. The phrase is
in the saved CRS page but in no passage of the box: the web-pages reader
breaks the page at every `<br/>`, so "ultimate repeal in" and "2005." are two
passages. That miss is the reader's, not the kernel's rank.

**Run 2, on freeze 2** (`results/run-2.json`, SHA-256 `28f17ad678ccf431881f458e63ac054fd973223720824e346d03136dbb2fe99a`;
its dry run with nonsense, `results/dry-run-2.json`, served nothing and
sealed nothing). Freeze 2 builds the box as VI.9 says, read where its files
are kept: each reader's mirror is a source of its own, her `log/` and
`lessons/` are read in her folder and the credit note through a list, where
run 1's box was a pile of copies of all seven. Three of the five pages had
changed online by then (the NBER, NBC and Wikipedia ones; the CRS report
and the NSF award had not) and are frozen as fetched. The result is run 1's:
the same five rules held, `served` failed on the same two questions, and
every question was served the same passages, word for word and in the same
order. Only their places changed, named now by the source they were read
in (`mail/...`, `log/...`), not by a folder of copies.

**What the five claims show.** The tools find where to read; they do not judge.
C1 (the draft says Type 2): claim-check serves the NSF record, and only a
person reading it sees it says Type 1. C3 (June 2021): the NBC page's sentence
"on Tuesday took over" is found, and a person confirms the date from its
dateline. C4: found by `quotes`. C5: found in two places, her father's tape and
her own note, which the tools do not see disagree. C6: only in Spanish.

**Also found.** `contradictions` reads the battery bank and the inverter, two
purchases at one vendor with different prices, as an "amount" disagreement. That
is a false alarm, and it is in the dry run's and the run's output.

## Run 3, on freeze 3

Freeze 3 is the maintainer's extension, in three strands, each asked on a box
of its own and judged into a verdict box of its own ([questions-3.json](questions-3.json),
[run3.py](run3.py)). `python3 demo/marisol/make_life_3.py` writes `life-more/`
beside `life/`, which is untouched: a school calendar, her texts with Tomás,
the lab's budget sheet and its battery sensors, read by the calendar, sms,
office and home-sensors readers, against a new paragraph of her draft (C7 to
C10, never boxed). Its dry run with nonsense (`results/dry-run-3.json`) built
every box, served nothing and sealed nothing, and skipped the two kinds that
take no question, so no answer was seen before the freeze. Run 3
(`results/run-3.json`, SHA-256 `3dd2079329e4e95cffeb9345a69fc9905d884099fef3f3d7aa911aaa69a5da2d`)
was asked once:

| Strand | Rule | Result | What it rests on |
|---|---|---|---|
| life | served | held | The Spanish question finds the calendar's closures; her texts' "Ya llegaron los $6,000" is found in Spanish and in English; the English claim about the bank finds the sensor sheet |
| life | gap | held | English claims find neither the Spanish calendar (C7) nor the budget, which says Chromebooks, not laptops (C9) |
| life | count | held | 7 passages say "Cierre por apagón"; the draft says 9 days |
| life | budget | held | `amounts` reads the Chromebook line, $3,468.00, and the total, $4,040.00; nothing says the draft's $18,000 |
| claims | served | **failed** | The Spanish question about the principal and the diesel served nothing (below); the tape's 28 years and the 2004 closing, and Inés's "que cada afirmación lleve su fuente", were found in Spanish; the championship question served nothing, as predicted |
| claims | gap | held | The three English claims about Spanish lines (C11, C12, C14) missed, as predicted |
| misses | reach | **failed** | `all-passages` ranks no passage holding either phrase in its first 10; its first three were the kernel's own each time |
| misses | phrases | **failed** for the repeal, held for the brother | `pile-rank` puts "$6,000" second in the mail mirror; it finds no "repeal in 2005" |
| misses | rank | held | `kernel.py` is the file freeze 2 ran |
| every strand | unsealed, verify | held | No seal or decline row; every evidence and verdict box verifies |

**What failed.** *The repeal.* No passage in the box holds "repeal in 2005", so
no ranking could have served it. The saved CRS page writes a line break
(`<br/>`) at the end of each line of the printed report, and the web-pages
reader makes each one a passage break: "…phaseout and ultimate repeal in" is
one passage and "2005. The tax credit…" the next. Runs 1 and 2 said the
phrase was in the pile and the kernel ranked it too low; that was never
checked, and it was wrong. *The brother.* `all-passages` serves one passage,
the email's header: the body ("Te mandé $6,000 … baterías") holds too few of
the question's words for the kernel's half-the-words rule ("mandé" is not
"mandó"). `pile-rank`, which ranks without that rule, serves the body second.
*The diesel.* The Spanish question asks what the principal *pidió*; his email
says "Le *pido*", and "Director" is in its signature, another passage. Too
few of the question's words are in any one passage, so nothing is served.
None of these changed a rule or the kernel's rank; each is written down here
as found, after the run.

**What it shows.** Read where they are kept, four more kinds of file her work
leaves were found and checked: the calendar against the draft's 9 days, the
texts confirming the money's arrival, the budget against the draft's figure,
and the sensors against "a full school day" (4.5, 4.0 and 5.0 hours against a
6.5-hour day; a person reads the sheet the claim points to). The language gap
held again on three new claims. And following the two old misses showed one
was a reader splitting a page, not a rank: the next bite there is the
web-pages reader, not the kernel.

## Run 4, on freeze 4

Run 3 found the repeal miss was the web-pages reader's: it made every `<br>`
a passage break, and the saved CRS report ends each printed line with one.
The fix reads a page that ends twenty lines or more with `<br>` as wrapped
lines, one sentence a line (in the clauses add-on, which web-pages reads
pages with; willow branch `ccr-8ddfb123-dbqhkm`, not yet on main). Freeze 4
changed nothing in this folder but FROZEN.json: the questions, rules and
expectations are as they were, and every tool but `clauses.py` is the file
freeze 3 ran. Its dry runs with nonsense (`results/dry-run-4.json`) served
nothing; FROZEN.json says what the author saw while checking the fix. Run 4
(`results/run-4.json`, SHA-256 `38ed797bf0aff42f7b7ffe2f013d82aa639e765784e6a7bb03d672d6963ad137`)
asked every question of freezes 2 and 3 once:

| Run | Rules held | Rules failed | Changed since the run before |
|---|---|---|---|
| run.py (freeze 2's) | gap, amounts, quotes, unsealed, verify | served: the repeal and the brother questions, as in runs 1 and 2 | the repeal question's served passages (below) |
| life | every rule | none | nothing |
| claims | gap, unsealed, verify | served: the diesel question, as in run 3 | nothing |
| misses | rank, unsealed, verify | reach (the brother only), phrases (the repeal only) | `all-passages` now reaches the repeal sentence, 10th |

**What the fix moved, and what it didn't.** The sentence "…scheduled the
credit for phaseout and ultimate repeal in 2005." is now one passage in every
box (`web-pages/crs-rs20695.html.txt:48`), where no passage held it before.
The kernel ranks it 10th, and pile-rank 9th, for the repeal question: below
the three NBER passages both now serve first, and so the repeal question and
pile-rank's first three still miss. What runs 1 to 3 served from the CRS
page was one printed line ("Credit and was provided under section 936…"),
now part of its paragraph. So the repeal miss is two misses, and one is
fixed: the reader cut the sentence (fixed), and the kernel's rank puts it
10th (kept: the rank is never loosened for recall). Every other question was
served the same passages, word for word; the grid and the 76-day questions'
NBC passages are at new line numbers because the NBC page was fetched again for freeze 3, not
because of the fix. The brother and the diesel questions are as run 3 left
them: too few of the question's words in the passage that holds the answer.

## What the freeze is and is not

It is not a blind pre-registration. Before it, the six claims were tried once by
hand against the same pile (the results changed three things in PLANTED.md: the
draft must stay out of the evidence, claim C3 holds only through the page's
dateline, and an English claim cannot find the Spanish log), and the dry run ran
`amounts`, `quotes` and `contradictions`, which take no question, so their
answers were seen before the freeze. The questions and rules were fixed after
that and before the frozen run. One of the nine was predicted to fail (the English claim about the Spanish log), and it did.

**What the dry run could see.** With every question replaced by nonsense it ran
the readers, the pile, the box, the verdict rows and `verify`, and found the
wiring sound. It could not see the code that reads served passages, since
nothing was served; `test_marisol.py` holds that, on made-up answers.

## Before anything beyond this is claimed

1. A Puerto Rican reader reads the Spanish for what rings false. A model wrote it.
2. The PROMESA signing date is confirmed; it is in no claim here.
3. The "open community lesson" is an invented stand-in, because no licence has
   been read for the real one.
