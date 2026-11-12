# What the author planted: the answer key (notes, written before the generator)

**Never boxed.** A run reads the folder blind; this file is how its findings are
checked afterwards. A tool that finds none of these has missed one, and a tool
that finds something not on this list has found something to look at.

Fiction throughout. The people, the school and the companies are invented. The
real facts the story stands on (Section 936, Hurricane Maria, LUMA, NSF award
2305699, PROMESA) are kept by address and SHA-256 in `sources.json`, never as
text, so any of them can be fetched again and rechecked. Every number marked
*invented* below is invented, in the files too.

## The grant draft's claims (`life/grants/draft.md`)

| # | Claim in the draft | What the folder and the sources say | Add-ons | A person decides |
|---|---|---|---|---|
| C1 | "The Trust holds a Type 2 engine award" | NSF record 2305699: program "NSF Engines - Type 1", 05/15/2023 to 04/30/2025, $999,903 | claim-check, thesis | A later award, or simply wrong |
| C2 | "Outages have cost the school about $40,000" | No source; `life/receipts/outage-costs.csv` totals $14,873.50 (*invented*; each amount is written with its `$`, as a receipts export writes it, so `amounts` can read it) | amounts, claim-check, thesis | Which figure goes in |
| C3 | "LUMA Energy took over the grid in June 2021" | Holds, in two places the page must be read for: the saved NBC News page is dated June 2, 2021 and says a private company "on Tuesday took over" the grid (June 1, 2021); the passage with "took over" does not itself say "June 2021", so claim-check shows some parts and a person confirms with the dateline | claim-check | Nothing; it stands |
| C4 | A quotation from the open lesson in `life/lessons/03-...` | The draft drops one word ("alone") from the lesson's sentence | quotes | Restore the original |
| C5 | "the credit ended in 2005, after a phase-out that began in 1996" | The report: began 1996, ended around 2005 (some sources: January 2006). Her father says on tape it ended in 1996; her own note says 2005 | contradictions finds none; the gap the `year-claims` idea is for | Which year, and how to say it |
| C6 | "Our school went 76 days without grid power after Maria" | Holds against her own log (*invented*: 2017-09-20 to 2017-12-04) | claim-check | Nothing; it is her own record, cited as such |

**Run against an evidence pile that leaves the draft out.** The draft says each of these claims in its own words, so with the draft in the pile every claim's best match is the draft itself (found in a first trial). The folder minus `grants/` plus the saved sources is the evidence.

**The language gap (found in a first trial):** C6 is an English claim about a Spanish log. claim-check, which matches words, cannot bridge "76 days" and "76 días"; the same claim asked in Spanish finds the log's line. A run must ask C6 in both languages and say which found it.

C3 and C6 are planted as **holding**, so the run shows a tool that confirms as
well as one that catches.

## Traps, so a tool can't get it right by accident

- **T1:** the word "Type" is in both "Type 1" (the record) and "Type 2" (the
  draft), so a word match alone finds the record and misses the difference;
  only reading both lines settles C1.
- **T2:** a 2018 receipt for a **$6,000 transfer** from Tomás (an email, in
  Spanish) sits near the battery-bank receipt of $6,240.00: a reader who adds
  the transfer as a cost double-counts it.
- **T3:** a 2019 outage-log line that says "casi 40 mil" about **voltage**
  ("casi 40 mil voltios en el poste"), so "40" is not a clean signal for C2.
- **T4:** the 2004 plant closing and the 1996 law are in the interview, so a
  question about "1996" finds both the true start of the phase-out (the report)
  and the father's wrong end of it (the tape).

## The two languages

The folder is bilingual as the island is: the outage log, the district notices,
the emails and Ernesto's interview are in Spanish, the grant draft and one
lesson in English, one lesson in each. A question asked in Spanish must find
English and Spanish passages (`words-es`); a translation is only ever a
proposal until the person it speaks to seals it (`translate`). **No one has yet
read the Spanish for what rings false: a Puerto Rican reader must, before this
goes beyond its author.**

## Identifiers

Phones are `787-555-01xx`, mail is at `example.org` and `example.com`, and no
real address, account or card number appears.

## Not in this folder (and why)

- **Photos.** The doc planned them; a photo with real EXIF needs a binary the
  generator would have to make. Left out for now, said here.
- **Real source text.** Kept by address and hash only (`sources.json`).
- **A real lesson's text.** The "open community lesson" of the plan is an
  invented stand-in (`life/lessons/03-...`), because no licence has been read
  yet for the real one. Swap it only after reading the licence.
