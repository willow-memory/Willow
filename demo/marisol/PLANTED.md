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

## Freeze 3: more of her life (`life-more/`, from `make_life_3.py`)

Written before the generator, as the sections above were, and corrected once
before the freeze (below). `life/` is untouched: runs 1 and 2 read the same
bytes they did. The new paragraph of her draft is `life-more/grants/draft-3.md`,
never boxed.

| # | Claim in the new paragraph | What her files say | Read by | A person decides |
|---|---|---|---|---|
| C7 | "Outages closed the school for 9 class days in 2022-23" | The district calendar (`calendar/escuela-2022-23.ics`, *invented*) has 7 days "Cierre por apagón" (three for Fiona, four more), among other events | calendar | 7, not 9 |
| C8 | "My brother's $6,000 arrived in February 2018" | Holds: her texts with Tomás (`phone/sms-backup.xml`, an Android backup) say "Ya llegaron los $6,000" on 2018-02-12, three days after his email | sms | Nothing; it stands |
| C9 | "We need 30 laptops at $600 each, $18,000 in all" | The lab's budget (`budget/presupuesto-laboratorio.xlsx`, *invented*) asks for 12 Chromebooks at $289.00, $3,468.00, and totals $4,040.00; $18,000 is nowhere | office, amounts | Which figure goes in |
| C10 | "The lab's battery bank runs the lab through a full school day" | The battery sensors (`sensors/history.json`, Home Assistant history, *invented*): on the three outage days of 2026-09-01 to 14 the bank ran the lab 4.5, 4.0 and 5.0 hours, against a 6.5-hour school day | home-sensors | It doesn't, yet: say so |

**Corrected before the freeze (C10).** The sensors were first planted as one
entity, the bank's charge in %, sampled through the day. The home-sensors
reader keeps one daily mean per entity, so an outage day's afternoon low
(22%) averages to 63.7 and the claim can't be settled from the mirror. A
second entity, "Lab backup runtime" in hours, now says it directly, and the
entities are named in English so an English claim can find the sheet. This
was found by reading the reader's README and a mirror of the files, before
any question was asked.

## Freeze 3: more claims, the same folder

| # | Claim | What `life/` says | Expected |
|---|---|---|---|
| C11 | "The principal asked me to keep track of what I spend on diesel" | Holds: Héctor's 2018 email, "Le pido que lleve la cuenta de lo que gasta en diésel" | claim-check in English misses; words-es in Spanish finds it |
| C12 | "My father worked 28 years in the plant's laboratory" | Holds: the tape, "llevaba veintiocho en el laboratorio" | the number is written out, so English misses; Spanish finds it |
| C13 | "the plant closed in 2004" | Holds: "Cerró en el verano de 2004"; the tape's 1996 line (T4) is the trap | words-es finds it |
| C14 | "Puente Digital asked for a source for every claim" | Holds: Inés's email, "que cada afirmación lleve su fuente" | English misses; Spanish finds it |
| C15 | "the robotics club won a state championship" | Nothing says so | silent |

## Freeze 3: the two misses followed

Runs 1 and 2 failed two questions: the repeal question ("ultimate repeal in
2005" is in the pile, ranked below the top three) and the brother question
(the mail reader's header passage was served, not the body with "$6,000").
Freeze 3 asks the same words of two tools that point at where to look, and
changes nothing in the kernel: `all-passages` (the kernel's own rank, every
passage it would serve; the phrase is predicted 10th or better) and
`pile-rank` (BM25F with phrases, over the web pages' mirror for the repeal
and the mail mirror for the brother; predicted in its first three).
