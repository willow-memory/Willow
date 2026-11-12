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

**What the five claims show.** The tools find where to read; they do not judge.
C1 (the draft says Type 2): claim-check serves the NSF record, and only a
person reading it sees it says Type 1. C3 (June 2021): the NBC page's sentence
"on Tuesday took over" is found, and a person confirms the date from its
dateline. C4: found by `quotes`. C5: found in two places, her father's tape and
her own note, which the tools do not see disagree. C6: only in Spanish.

**Also found.** `contradictions` reads the battery bank and the inverter, two
purchases at one vendor with different prices, as an "amount" disagreement. That
is a false alarm, and it is in the dry run's and the run's output.

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
