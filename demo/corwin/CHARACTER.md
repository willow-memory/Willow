# Corwin Tamsett

Fictional. Made for the demo on 2026-11-06; no real person is behind him or anyone around him. Phones are
`555-01xx`, mail is at `example.com`/`.org`/`.net`/`.edu`/`.gov`, and the one IP address is in `192.0.2.0/24`.
The authors of the papers he reads are real and named as themselves.

Corwin Tamsett is 46, a master electrician, and has worked for himself for fifteen years as **Tamsett Electric**
from his house at 41 Larch Row, **Orrin Falls**, a made-up town of 11,000. He does houses, a few small businesses
(a dental office, a bakery, a church, a library) and, when he wins the bid, school district work, across Orrin
Falls, Tamarack, Wexcombe, Hadley Gap, Calder Mills and Brindle Ford. About 210 jobs a year. His license is
ME-27714 with the State Board of Electrical Examiners, renewed every three years with continuing-education hours.

He didn't go to university. In January 2024 his daughter asked him at dinner whether zero is a number and to prove
it, and he couldn't, and since then he has kept **the Zero Ledger**: a long text file of numbered lines about
zero, nothing, the vacuum, symmetry breaking and the foundations of number. Each line is marked as what a cited
work says (`[S]`), his own reading (`[M]`), unchecked (`[?]`) or dropped (`[x]`). Numbers are never reused. He
reads the German with a dictionary and DeepL. Four revisions so far and a fifth in draft.

**Family.**
- **Gwen Tamsett**, his wife, is the librarian at the Orrin Falls middle school.
- **Bea** (Beatrix), their daughter, is 18, a senior; passed her road test in September 2026.
- Gwen's mother lives in Tamarack; Christmas and Thanksgiving are at hers.

**The ledger's two readers.**
- **Ottilie Brandvold** is a PhD student in condensed-matter physics (low temperature) at Kessick University, the
  state university an hour away. She found the ledger through a forum in May 2024 and checks its `[S]` lines
  against the papers, by email, in batches. Precise, blunt, physics only: she won't do Frege or Dedekind.
- **Mattias Oyelaran** is Corwin's friend from school, now a machine-learning engineer in Singapore (twelve or
  thirteen hours ahead). He reads along and now and then runs something on the ledger: an embedding map, a
  nearest-neighbour list, a fuzzy quote matcher, a model's summary. His outputs land in `mattias_runs/`.

**Others in his files.** Dario Pask is his part-time apprentice. Kellner Electric Supply is his supply house
(account 40-1187). Brightwire CE sells online continuing-education courses. Renata Oduya is facilities coordinator
for Orrin Falls Unified. Halberd Insurance is his agent.

## How his life writes itself down

The folder is `life/`, about 300 files and 0.3 MB (before the papers are fetched), covering January 2024 to
November 2026.

| Folder | What | Approx. count |
|---|---|---|
| `ledger/` | The Zero Ledger, one file per revision: rev 1 (2024-04), 2 (2024-12), 3 (2025-09), 4 (2026-05), 5 (draft, 2026-10) | 5 |
| `sources/catalogue.csv` | The papers he keeps or wants: id, citation, where he got it, file, SHA-256, date kept, a note | 1 |
| `sources/` (fetched) | The papers themselves, under the file names he gave them, put there by `fetch.py` | 14 |
| `reading_log.txt` | What he read, when, from where | 1 |
| `notes/` | Dated working notes on the ledger, and scraps from the rest of his life | ~50 |
| `mail/inbox`, `mail/sent`, `mail/junk` | Emails as `.eml`: Ottilie's batches and his replies, Mattias, the licensing board, a CE provider, the school district, customers, supplier statements, a trade newsletter, junk | ~75 |
| `chat/` | Phone chat exports: Mattias by year, Gwen for 2025 and 2026 | 5 |
| `mattias_runs/` | What Mattias ran on the ledger | 4 |
| `work/jobs_YYYY.csv` | Every job: date, customer, town, job, hours, whether Dario was there, materials, billed, how paid, invoice | 3 |
| `work/invoices/`, `work/quotes/` | Text invoices for the commercial accounts, and one bid | ~82 |
| `license/` | His license card and the papers from the last renewal (2023) | 5 |
| `money/bank/` | Monthly checking-account CSV exports | 35 |
| `receipts/` | Receipts saved as text | ~18 |
| `todo/` | Dated todo lists | 17 |
| `calendar/corwin_calendar.ics` | A calendar export | 1 |

Today, in his world, is **2026-11-04** (a Wednesday).

## The papers

`fetch.py` fetches fourteen public-domain or openly published papers into `life/sources/` (or `--to DIR`) and
refuses any whose bytes don't match the pinned SHA-256; `fetch.py --check` hashes what is already there, offline.
`make_life.py` never calls it, and nothing it fetches is committed. Re-running `make_life.py` keeps what was
fetched. The pins came with the brief, except **Mach's *Science of Mechanics*** (archive.org
`sciencemechanic02machgoog`, djvu text), which had none: it was fetched twice on 2026-11-06, both times
`987490ff6a92ab24ce9109dbf1cf6c14380609dd2d1ca4f2e817e5217f29af11`, and that is the pin in `fetch.py` and in his
catalogue. His catalogue also names four papers he never got hold of, with no file.

## What he'd say he wants from a tool

> "I've got three years of this in text files and I can't hold it in my head any more. I want to ask it what I'd
> ask Ottilie, what did I say about Planck, where did that line come from, have I got that paper, and have it show
> me. And if I've written something down that isn't so, I'd rather hear it from my own files than from a room full
> of grad students on the nineteenth."
