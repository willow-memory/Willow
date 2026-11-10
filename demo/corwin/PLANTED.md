# PLANTED: answer key (testers: do not read until after scoring)

All paths are relative to `life/`. `python3 make_life.py --check` verifies the core evidence for each need.
Where a need turns on a source's words, the source file named is the one `fetch.py` puts in `life/sources/`, and
the words quoted here were checked against it (PDFs through `pdftotext -layout`).

## Needs

### N1: The Planck line he means to put on a slide is a misquote (urgent: the talk is 2026-11-19)
L21 has been `[S planck-1913 §140]` since rev 1: *"Even the vacuum performs vibrations at the temperature zero,
the mean energy of which is as large as hν/2."* Planck says no such thing about the vacuum. The source
(`sources/planck_heat_radiation_masius.pdf`, §140, between the running heads "IDEAL LINEAR OSCILLATORS 169" and
"ENTROPY AND PROBABILITY 170") says: *"Hence, for the zero point of the absolute temperature E becomes, not 0, but N hν/2 … That the
oscillators are said to perform vibrations even at the temperature zero, the mean energy of which is as large as
hν/2 and hence may become quite large for rapid vibrations, may at first sight seem strange. It seems to me,
however, that certain facts point to the existence, inside the atoms, of vibrations independent of the
temperature …"* It is about oscillators and vibrations inside atoms, much narrower than a claim about empty space.
- `ledger/zero_ledger_rev1.txt` … `rev5_draft.txt`: L21 unchanged, always `[S]`. L23 (`[M]`), L52 and L53 build on
  it ("the vacuum is not empty at zero (L21)").
- `notes/2024-03-10_zero_point.txt`: his own reading ("So the vacuum is never still") written straight after
  reading §140, the merge in the making.
- `mail/inbox/2024-06-09_batch_1_l13_l22.eml`: Ottilie left L21/L22 to him ("I don't have the Masius
  translation and these are about wording"), so it was never checked.
- `mattias_runs/2026-02-14_rev3_quotecheck.txt`: L21 scores 0.58 (every other quote 0.81–0.99), and the best
  passage it shows is "That the oscillators are said to perform vibrations even at the temperature zero …".
- `chat/mattias_2026.txt` (2026-02-15, again 2026-10-26) and `notes/2026-02-15_matcher.txt`: he blames OCR
  ("the fractions come out as junk"); Mattias points out the rest of that PDF scores 0.95+.
- On the slides: L56 in `ledger/zero_ledger_rev5_draft.txt` lists L21; `notes/2026-11-02_slides.txt` ("put the
  quote big").

### N2: Dedekind's words are cited to Frege (slow; a citation pointing at the wrong book)
L04 is `[S frege-1884]` (rev 3 on: `[S frege-1884, intro]`): *"Numbers are free creations of the human mind."*
Those are Dedekind's words, from the preface to the first edition of *Was sind und was sollen die Zahlen?* (1888):
in `sources/dedekind_essays_beman.pdf`, "PREFACE TO THE FIRST EDITION": *"My answer to the problems propounded in
the title of this paper is, then, briefly this: numbers are free creations of the human mind"*; in the German,
`sources/dedekind_was_sind_1888_djvu.txt` around page VII–VIII: *"die Zahlen ſind freie Schöpfungen des
menſchlichen Geiſtes"*. Dedekind repeats it in §73 ("we are justified in calling numbers a free creation of the
human mind"). Frege's *Grundlagen* (`sources/frege_grundlagen_1884.txt`) has nothing of the kind as his own view:
in §25 he quotes Berkeley (number is "gänzlich Geschöpf des Geistes") in order to reject it, and in §26 says number
is no more an object of psychology than the North Sea, which is the "tension" Corwin's L05 then struggles with.
- `reading_log.txt` 2024-02-04 and `notes/2024-02-04_dedekind_preface.txt`: he copied the line from Dedekind's
  preface, correctly attributed. `notes/2024-04-13_rev1_tonight.txt`: "Frege section first: zero (§74), free
  creations, the North Sea", the conflation.
- `ledger/zero_ledger_rev3.txt` L05 ("Tension with L06 … Frege holds both? Sort out.") and L46 (the same words,
  rightly to Dedekind §73).
- `mattias_runs/2025-10-05_rev3_neighbours.txt` (L04 ~ L46, 0.94) with `notes/2025-10-05_mattias_neighbours.txt`
  and `chat/mattias_2025.txt` ("Frege and Dedekind agreeing. that's the point").
- Why nobody caught it: `mattias_runs/2026-02-14_rev3_quotecheck.txt` skipped L04 (English quote, German source);
  `mail/inbox/2024-05-12_your_ledger_from_the_forum.eml`: Ottilie won't do Frege or Dedekind.
- `mattias_runs/2026-06-07_rev4_summary.txt` repeats it ("both Frege and Dedekind hold …").

### N3: His own flagged speculation became a line cited to Weyl, and later lines stand on it (slow-urgent: slide 5)
Rev 1 and rev 2 have L31 `[M]`: *"The vacuum is to physics what the empty set is to arithmetic: a nothing with
structure. SPECULATIVE, mine, don't lean on it."* In rev 3 L31 is `[x] folded into L47`, and L47 is
`[S weyl-1922 §12]`: a true quote from Weyl ("space in itself is nothing more than a three-dimensional manifold
devoid of all form") followed, inside the same `[S]` line, by *"the vacuum is the physical empty set, a nothing that
every structure is built on."* Weyl says nothing about an empty set: in `sources/weyl_space_time_matter.pdf` §12
(pages headed 144–145) he is reporting Riemann's view, "that space in itself is nothing more than a three-dimensional
manifold devoid of all form; it acquires a definite form only through the advent of the material content filling
it and determining its metric relations." The SPECULATIVE flag is gone, the claim now wears Weyl's name, and it is
leaned on.
- `ledger/zero_ledger_rev1.txt`, `rev2.txt` (L31 `[M]`), `rev3.txt` (L31 `[x]`, L47, "Changes since rev 2": "L31
  folded into L47: Weyl says it, and it's better with a citation"), `rev4.txt` (L48, L52 lean on L47),
  `rev5_draft.txt` (L56 puts L47 on a slide).
- `notes/2025-09-20_rev3_plan.txt`: "L31 was always the weak one, a line of mine with nothing under it … Fold L31
  into a new L47 with Weyl's words up front. Stronger with a citation."
- `notes/2024-05-19_mattias_map.txt` and `mattias_runs/2024-05-19_rev1_map.txt`: L31 alone, "either the most
  original line or the most made-up".
- Checked only inside the quotation marks: `mail/inbox/2025-11-09_batch_5_l37_l47_rev_3.eml` (L47 "quote matches
  Brose §12 … Weyl is reporting Riemann's view") and the quotecheck's "Only text inside quotation marks is matched".
- `mattias_runs/2026-06-07_rev4_summary.txt`: "Weyl identifies the vacuum as the physical empty set";
  `chat/mattias_2026.txt` 2026-06-07 ("it thinks Weyl invented your empty set idea" / "Weyl does say it, more or
  less"). `notes/2026-11-02_slides.txt`: "Slide 5 (Weyl: the vacuum is the physical empty set)".

### N4: Ottilie's objection to the Ehrenfest line has gone unanswered for a year (urgent: she warned him before the talk)
L37 (rev 2 on, unchanged through rev 5): `[S ehrenfest-1917]` *"Ehrenfest shows the laws of physics require space to
have exactly three dimensions: stable orbits, and stable atoms, exist only in R3."* L38 and L45 rest on it.
- `mail/inbox/2025-11-09_batch_5_l37_l47_rev_3.eml`: Ottilie: "This overstates Ehrenfest … In his introduction he
  says the questions, put that way, 'have perhaps no sense' … a conditional result about one family of force laws,
  not a proof about space. 'Require' and 'exactly' are your words. Either narrow it … or mark it [M]." The source
  agrees: `sources/ehrenfest_1917_three_dimensions.pdf`, Introduction (OCR cleaned): "When put in this way the
  questions have perhaps no sense … I will not try to find a better form for these questions"; §1 assumes the force from "the
  differential equation of LAPLACE-POISSON" and speaks of "the stability of the circular trajectories".
- `mail/sent/2025-11-16_re_batch_5_l37_l47_rev_3.eml`: his reply answers L43, L44, L46, L47 and says "The rest I'll
  fold into rev 4". L37 is not mentioned.
- `mail/inbox/2026-03-22_batch_6_…eml` (P.S.: "still keen to hear what you make of my L37 note from November"),
  `mail/inbox/2026-09-15_open_bench_nov_19.eml` ("If Ehrenfest makes a slide, please look at my batch 5 notes
  first. Grad students will have read that paper.").
- `notes/2025-11-10_batch_5.txt` ("I need to sit down with the paper again before I answer that one"),
  `notes/2026-03-24_batch_6.txt` ("Later"), `notes/2026-05-17_rev4.txt` ("Didn't get to Ehrenfest. Next rev."),
  `chat/mattias_2025.txt` 2025-11-11 ("I'll deal with it after Christmas"); todo lists 2025-11-17 and 2026-01-12
  carry it, later ones don't. `rev5_draft.txt` L56 and `notes/2026-11-02_slides.txt` put L37 on slide 4.

### N5: The paper he thinks he can't get is already in his folder (slow; a source he thinks he never got)
`sources/catalogue.csv` lists `einstein-stern-1913` (Einstein & Stern, *Einige Argumente für die Annahme einer
molekularen Agitation beim absoluten Nullpunkt*, Ann. d. Phys. (4) 40 (1913) 551–560) as NOT GOT, and L24 is `[?]`
"NOT SEEN" in every revision since rev 2. But the same catalogue has `Z-1424262`: "?? Annalen der Physik 1913?,
pp. 551-560, German. Title unreadable in the OCR", file `sources/article.pdf`, kept 2025-06-03, "something about a
Resonator and Planck's formula". That file (zenodo record 1424262, SHA-256 `2d1a44f8…`) is the Einstein–Stern
paper: its OCR title reads "E f h i g e Argumemte far die Armahme eilzer rnolekularem Agitation beim absolutern
Nzcllpumkt; von A. E i n s t e i n urnd 0. S t e r n", it opens (OCR as is) "Der Susdruck fur die Energie eines
Resonators lautet nach der ersten Planckschen Formel", says that by the second formula "hat der Resonator beim
absoluten Nullpunkt die Energie h u / 2", and a few pages on that "die spezifische Warme des Wasserstoffs die
Existenz h e r Nullpunktsenergie wahr- scheinlich macht". It is exactly what L24
wants.
- `reading_log.txt` 2024-09-15, 2024-10-05, 2024-10-19 and `notes/2024-09-15_einstein_stern.txt`,
  `notes/2024-10-19_ill_no.txt`: wanted, Wiley $42, ILL refused.
- `reading_log.txt` 2025-06-03 and `notes/2025-06-03_zenodo.txt`: two `article.pdf`s from one zenodo search, "pages
  551-560 … Something about a Resonator. Kept it, logged it as Z-1424262".
- `chat/mattias_2025.txt` 2025-06-03; `mail/inbox/2026-06-14_rev_4_einstein_stern.eml` and
  `notes/2026-06-14_ottilie_es.txt` (Ottilie couldn't get it either: "it's the paper the zero-point section stands
  on"); `mattias_runs/2026-02-14_rev3_quotecheck.txt` ("einstein-stern-1913 cited by L24, no file" next to "files
  … not cited by any line: … Z-1424262").

### N6: His master electrician license lapses on November 30, and with it the biggest job he's had (urgent, practical)
No file says it in one place. The evidence:
- `license/license_card_ME-27714.txt`: expires 11/30/2026.
- `mail/inbox/2026-09-01_license_renewal_window_open_me_27714.eml`: 18 CE hours needed, "Work requiring a license,
  including pulling permits, may not be performed on an expired license"; `2026-10-15_reminder_…eml`: 0.0 of 18.0
  on record.
- `mail/inbox/2026-03-14_your_order_…eml` and `receipts/2026-03-14_brightwire_ce.txt`: the 18-hour package, access
  through 2026-11-14, "Partial packages are not reported". Progress: `2026-05-02_…` (2.0), `2026-06-27_…` (6.0),
  `2026-10-01_your_access_ends_in_44_days.eml` (still 6.0 of 18.0: six two-hour modules, 12 hours, in ten days).
- `mail/inbox/2026-09-28_award_hallett_street_…eml`: $38,400; the permit must be pulled by 2026-11-23 and the
  contract (with "a copy of a current master electrician license valid through the work window") is due 2026-11-13;
  work starts 2026-12-07. `notes/2026-09-28_hallett.txt`, `work/quotes/2026-09-14_hallett_street_bid_26-114.txt`.
- The ledger crowding it out: `calendar/corwin_calendar.ics` has a "CE - Brightwire module" block on twelve
  Saturdays; the notes for those Saturdays (`notes/2026-07-11_saturday.txt`, `2026-08-08`, `2026-08-22`,
  `2026-09-12`, `2026-10-10`, `2026-10-24`) say he did the ledger or something else. `chat/gwen_2026.txt` 2026-10-20
  ("you said that in July"); `chat/mattias_2026.txt` 2026-11-02 ("nearly forgot. after the talk", and the talk is
  the 19th).
- `todo/todo_2026-07-05.txt` ("CE: modules 4-9 (12 hrs) BEFORE NOV"), `todo_2026-09-06.txt` ("CE!!!"); by
  `todo_2026-10-18.txt` and `todo_2026-11-02.txt` it is gone, replaced by slides and the Hallett contract.
- Contrast: `license/2023-12-02_note.txt` ("Did the last 6 hours in one weekend … Never again. Start next cycle
  early.") and `notes/2026-03-14_ce_course.txt` ("done by August").

## Traps (look like needs, aren't)

- **T1: The Planck PDF's hash didn't match.** `notes/2024-03-10_planck_hash.txt` reads like a corrupted or changed
  source, but he had hashed the unfinished `.part` download; the re-download matches, and the catalogue's
  `planck-1913` SHA-256 is the true one (`fetch.py --check` holds it). Every catalogued hash is right.
- **T2: Ottilie's objection to the von Neumann line.** `mail/inbox/2025-01-26_batch_3_l08_l12.eml` doubts L10 ("Are
  you sure? Dedekind starts at 1"). It was answered (`mail/sent/2025-01-28_…`, quoting p. 199) and withdrawn
  (`mail/inbox/2025-01-30_re_batch_3_l08_l12.eml`: "You're right … Withdrawn"); `notes/2025-01-29_von_neumann_check.txt`.
  The line is right: `sources/vonneumann_1923_transfinite.pdf` p. 199, "(O ist die leere Menge …) 0 = O, 1 = (O),
  2 = (O, (O))". Also odd-looking but right: L02, Frege's zero as the number of "sich selbst ungleich" (§74).
- **T3: The licensing board's CE deficiency notice.** `license/2023-11-08_board_ce_deficiency.txt` looks like the
  license in trouble, but it is the previous cycle's, resolved: `license/2023-11-20_ce_certificate_codecraft.txt`,
  `license/2023-12-01_renewal_confirmation.txt` ("No further action needed"). (It is the precedent for N6, not N6.)
  Also not real: `mail/junk/2026-10-02_your_ce_hours_may_be_at_risk_renew_with_us.eml`, spam.
- **T4: Zermelo 1908, "not found".** `todo/todo_2024-03-04.txt` and `todo_2024-11-25.txt` ("Zermelo still not
  found") and L08's `[?]` in rev 1–2 look like a missing source, but it was found on 2025-06-03
  (`notes/2025-06-03_zenodo.txt`, catalogue `zermelo-1908`, `sources/zermelo_1908_untersuchungen.pdf`) and L08/L09
  are `[S]` from rev 3. The same search is what brought down N5's file.
