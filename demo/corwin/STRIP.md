# Corwin, blind: the strip-down

2026-11-06. Corwin was built by an agent that read nothing outside `demo/` but
the repo root's listing and its `.gitignore`. It wrote his files, his answer
key, and twenty questions in his voice. A second agent, the tester, read only
`QUESTIONS.md` and saw his files only through what willow served or a check
printed (file names it could list; their contents it could not open). It
recorded both passes in `served.md` before it opened `PLANTED.md`.

Two leaks weaken the independence, both toward the person writing this, not the
tester. The builder's report said one source was filed under Corwin's own name for
it, a hint at N5. And CI's demo gate prints the tail of `make_life.py --check`,
which named N6's dates and the four traps before scoring. Neither reached the
tester.

## The setup

His files through willow's readers: `mail` (74 `.eml`), `calendar` (1 `.ics`),
`bank` (35 money CSVs), `csv-rows` (job CSVs and his source catalogue),
`deps/pdf` (8 PDFs), and `text` over everything, again over every mirror, to
break lines past the kernel's 500 characters. The `chats` reader wrote nothing
(exit 42): his chats are plain text, not WhatsApp or Telegram exports, so they
came in through `text`. One box over all of it (318 files); a second over his
kept sources alone (15 files), for the ledger checks.

**Pass A** asked his twenty questions with the kernel's `bite`, as written.
Every one served something, so `why-not` and `typos` never ran.

**Pass B** ran the checks a ledger-keeper using willow would: `quotes` on his
latest revision (rev 5, a draft) and his first, against the sources box;
`misquote` on each quote `quotes` called "almost" (13); `claim-check` on five
claims; his catalogue's SHA-256 against the kept files, and `fixity`; and on the
main box `pair-drift`, `contradictions`, `duplicates`, with `thesis` and
`clauses` besides.

## The needs

| Need | Pass A: question, what served | A | Pass B: check, output | B |
|---|---|---|---|---|
| N1 the Planck line on his slide is a misquote ("Even the vacuum performs vibrations...") | questions 1 and 9: his slide note beside Mattias's matcher, its best match "the oscillators are said to perform vibrations", and Corwin blaming the OCR | evidence served | `misquote`: "the vacuum performs vibrations: the quote has it; your files don't", in Planck's §140; `claim-check`: "lacks vacuum" | **found** |
| N2 Dedekind's "free creations of the human mind" cited to Frege | question 3: Dedekind §73, and Mattias's summary "both Frege and Dedekind hold" | evidence served | `quotes`: the words "as written" in Dedekind's preface; it checks the words, not the citation | evidence served |
| N3 his own flagged speculation now a line cited to Weyl | question 5: Mattias's "it thinks Weyl invented your empty set idea", his "Weyl does say it, more or less" | evidence served | `thesis`: L47 lacks "vacuum, physical, empty", among 81 of 85 lines "short"; `quotes`: the Weyl words inside the quotation marks hold | evidence served |
| N4 Ottilie's Ehrenfest objection unanswered a year | question 2, "what did ottilie say about ehrenfest": her "L37 This overstates Ehrenfest, and it's the line I'd most want you to change", and his note, "She asked again about the Ehrenfest note. Later." | **found** | `clauses`, rev 4 to rev 5: L37 unchanged, L56 putting it on a slide | evidence served |
| N5 the paper he can't get is already in his folder | questions 11 and 12: catalogue row "Annalen der Physik 1913?, pp. 551-560 ... article.pdf", and L24 "Still can't get it", in separate answers | evidence served | no check looked; the catalogue's listing shows two rows with the same pages | evidence served |
| N6 his license lapses Nov 30, and the Hallett job with it | question 6, "when does my license expire": the card (11/30/2026) and the board's "0.0 of 18.0 required CE hours"; question 8: the Hallett start, Dec 7 | **found** (the license); evidence served (the job) | nothing in Pass B reads a deadline | missed |

## The traps

| Trap | A | B |
|---|---|---|
| T1 the Planck PDF's hash "didn't match" (a `.part` file) | held: question 20 served the explanation | held: every catalogued hash matches |
| T2 Ottilie's von Neumann objection, withdrawn | **sprang**: question 7 served "L10 Are you sure? ... Please check" without the withdrawal | **sprang**, weakly: `quotes` rated the right L10 quote "almost" (9 of 9 words) and exited 42 |
| T3 the 2023 CE deficiency notice, resolved; CE spam | held | held |
| T4 Zermelo "not found" | held: question 13 served the old todo, and the Zermelo PDF beside it | held |

**Three of six found: two by asking (N4, and N6's license half), one by checking
(N1). Every other need had its evidence served and nothing joining it up.**

## What it says

- **The kernel answered every question, and each answer holds only that
  question.** N4 and N6 were found because Corwin's questions named Ehrenfest
  and his license. Nothing joined the license to the Hallett job, the catalogue
  row to L24, or Mattias's "it thinks Weyl invented your empty set idea" to L47.
  The joins are a reader's job.
- **`quotes` with `misquote` was the one tool that found a need nobody asked
  about.** The Planck misquote was the one Corwin had already explained away
  when his friend's matcher flagged it: he blamed the OCR, and the check named
  the four words the source doesn't hold.
- **`quotes` checks the words inside quotation marks, never the source the line
  cites.** A true quote with the wrong author (N2) or a true quote with his own
  words after it, inside one cited line (N3), passes.
- **OCR is the noise floor.** About 12 of `quotes`' 13 "almost" were the scans'
  OCR ("hu man", "dutch", ligatures), which buries the one real miss and springs
  T2. `thesis` counts line labels like "L37" as missing words: 81 of 85 lines came
  out "short".
- **The tester's one step off the command lines:** `quotes` shortens each quote
  in its output, and the ledger couldn't be read, so the whole quotes for
  `misquote` and `claim-check` were taken from `quotes`' own `quotations()`
  function, and the catalogue was listed through the kernel's `chunks`.
- **A second run** should ask questions that don't name the topic (Hollis's "ear
  doctor phone number" never says hearing), and give `quotes` a mode that checks
  a quote against the source its line cites.
