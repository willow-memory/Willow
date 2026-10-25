# Bernadette, blind, through the whole stack: the strip-down

2026-10-24. Built by an agent that read nothing outside its own folder, under
limits meant to keep her away from the first three: over 62, not in music,
bookkeeping or bees, sharing a home, outside the UK. It wrote her files in the
raw formats her apps would leave (single `.eml` files and an `.mbox`, `.ics`
and `.vcf`, WhatsApp and Telegram exports, an Obsidian vault, `.docx`,
`.xlsx` and `.odt`, Kindle clippings and an `.epub`, two PDFs, bank CSVs),
plus the answer key and twenty questions.

The tester read only `QUESTIONS.md` and `CHARACTER.md`. It ran
`stack.py run` once, which takes her folder through every layer of willow:
each reader into one mirror, `start`, the look-ahead add-ons, all twenty
questions through `readings` on the mirror and through the bare kernel on her
raw files, privacy over everything served, and an assistant over `mcp-lite`.
It made the one seal the run waited on (as Bernie, with her key, in a
throwaway box), ran `stack.py after`, and opened `PLANTED.md` only then.

## The needs

| Need | Her question | Served | Verdict |
|---|---|---|---|
| N1 the rego lapses 3 Nov, unpaid | 1, "when does the rego run out on the forester"; 2, "how much is the car rego this year" | the yearly calendar entry, "Car rego due … renew online before 3 Nov"; for 2, the budget sheet's estimate first (T2), then the calendar. This year's notice ($912.40, expiry 03/11/2026) came up only under question 9, about Mags's phone number | **evidence served**; not that it's unpaid, and the real amount only by accident |
| N2 the mole, never seen | 3, "when is my skin appointment with dr rao"; 20, "dermatoligist referal letter" | the 19 Aug skin check she cancelled ("cancelled - pennant final … REBOOK"), "Skin: see Dr Rao", and the GP's referral, from the PDF ("changed over the past year … I am concerned"). 20 found nothing: both words misspelt | **evidence served**; that the clinic cancelled the rebooking didn't come up (it did on her raw files, below) |
| N3 the health fund, suspended 14 Nov | 4, "did lakeside take the health insurance this month" | the final notice, and the bank line showing the last Lakeside debit on 28/07/2026 | **found, asked**; though the notice's passages were its header and sign-off, not its $1,238.55 and 14 November |
| N4 Mags, widowed, and Bernie not ringing | none asked it | under 9, Mags's card with her birthday, 30 Oct; under 10, about the ring, "Must ring Mags. Keep putting it off. What do I even say to her." | **an accident** |
| N5 the ring promised to Aoife at 21 | 10, "where did i put mums ring"; 11, "what did the jeweler say"; 19, "did i promise siobhan anything" | 10: "Found Mum's ring in the blue box … One of the claws is lifting", and "Emailed Sturt St Jewellers about Mum's ring". 11 served chats about tax and the health fund. 19 found nothing | **evidence served**; the promise itself missed twice: 11 on a spelling, 19 on one word (below; corrected) |
| N6 the tax return, due 31 Oct | 5, "whats the deadline for the tax" | "2026-10-31 TAX DUE (self lodge) … rental schedule!!", and Siobhán: "Mum it's due the 31st" | **found, asked**; the stuck depreciation schedule didn't come up |
| N7 the roof over Kieran's room | 7, "roofer quote for kieran's ceiling" | the to-do "Kieran's ceiling - ring Craig back re quote", and the quote: "valid 30 days … you'll likely see the ceiling plaster go" | **found, asked**; the insurer's "gradual leaks not covered" didn't |

**Three of seven found as asked, three with evidence served, one by accident,
none missed.** Teodora, a different person with different questions, was one,
three, one and two; the two aren't a controlled comparison.

Traps: **T2 sprang.** "How much is the car rego this year" served the budget
sheet's `est. 880 for the year` ahead of anything else, not the $912.40 bill.
**T5 held:** "aoifes birthday" served her granddaughter's 12 December, not
Aoife Brennan's 3 December. T1 (the fake tax refund), T3 (the 5 Nov
appointment the clinic cancelled) and T4 (the 48-week rent draft) never came
up.

## What each layer did

- **The readers earned their place.** All seven read something: 83 mail files,
  4 calendar files, 4 chats, 159 notes, 6 office files, 2 Kindle files and 2
  PDFs, with 14 files no reader took copied as they were. Three questions
  answered on the mirror found nothing on her raw files: the rent workbook
  (6), Mags's contact card (9) and the budget sheet (18). On 4, her raw files
  served three years of "your premium from 1 April" emails, and the mirror
  served the final notice.
- **But a reader can also crowd one out.** On 3, her raw files served the
  clinic's "your appointment has been cancelled" email, the evidence that
  defuses T3. The mirror served the referral PDF in its place.
- **`secrets-audit` found nothing, and `Desktop/passwords.txt` is all
  passwords.** No line of it matches: `netbank: client … pw …`,
  `myGov: <email> / <password>`, a bare `wifi: …`. Question 13 then served
  that file. `privacy`, over everything the twenty questions served, hid four
  email addresses and none of the passwords. Both add-ons look for shapes that
  this file doesn't use.
- **The look-ahead was right.** `coming-up` listed fourteen dates in the next
  30 days. `todo` listed the replaced-card email's "remember to update any
  recurring payments", which is N3's root. `on-this-day` found a board payment
  from a year ago.
- **The assistant is only as good as its approval.** The stand-in assistant
  asked question 1 through `mcp-lite` and suggested its top passage's first
  line, `2022-11-03 Car rego due`. That is the first date of a yearly calendar
  entry, not this year's. It waited, as it must. Sealed, it is now the answer
  to that question every time it's asked. The seal is where a person reads
  what they approve. Nothing else checks it.
- **The trust layer held.** `stale` found the one approval still standing;
  `changed` found nothing changed; `session-seal` bundled the session's 27
  rows for one seal; `backup` checked every byte and the chain; `diverge`
  found the box and its backup the same, byte for byte; `verify` held.

## What the stack missed, and what would close it

- **One word the kernel didn't know was common.** *Corrected 2026-10-25:
  this first said accents, and was wrong.* "siobhan" is in her files as typed,
  in her daughter's email address, so the kernel held it. Question 19 found
  nothing because "anything" wasn't among the kernel's common words, so it
  counted toward holding the question, and no file has it: no passage held
  two of "promise siobhan anything". Asked as "did i promise siobhan", it
  served the promise. The accent gap is real elsewhere (a "cafe" typed for a
  file's "café"), but not here.
- **Spelling.** "jeweler" against the jeweller's own "Jewellers", and
  "dermatoligist referal". The one script in willow-bot has a typo rung
  (`pile.py`, one edit away), and willow's `typos` idea is still on the list.
- **What a question about change means.** "Did lakeside take it" is answered
  by an absence: no debit after July. Nothing in the stack reads an absence,
  and the readings add-on, which looks for numbers over time, never spoke.
- **What wasn't asked.** N4 is the need she'd least put into words, and it
  came up only beside other questions. That is the same shape as every earlier
  demo's emotional need.

## After the fixes

Each finding above was taken up, and the stack run again, the same way, on
the same files and the same twenty questions:

- **The kernel's common words** now hold "anything", "someone" and their
  kin, which name no topic. On all sixty demo questions this changes two
  answers: Bernadette's 19 now serves the promise ("when she turns 21 she'll
  have Mum's engagement ring — Nana Peg's sapphire"), with Gerry's "Rego??"
  "Tomorrow, promise" beside it; Teodora's "does my work insurance need
  anything from me" drops a printing quote that held only "anything".
- **`typos`**, new, reads a misspelt word as her files spell it and offers the
  question as read; the stack then asks it, as she would. 20, "dermatoligist
  referal letter", read as "dermatologist referral letter", serves the GP's
  note and the referral PDF. 11, read as "what did the jeweller say", serves
  the jeweller's reply, but by its header and sign-off, not its $285 and four
  to six weeks.
- **`accents`**, new, does the same for a word typed without its accent. It
  reads none of her twenty differently: none needed it.
- **`secrets-audit`** finds all five places in `Desktop/passwords.txt`, and
  **`privacy`** now hides passwords: three in what the twenty served.
- **The calendar reader** says a recurring event repeats on its first line,
  so the stand-in assistant's suggestion, and the answer sealed from it, now
  read `2022-11-03  Car rego due  (yearly, from this date)`. **`coming-up`**
  counts each repeat and every birthday: her next thirty days hold the rego
  on 3 November and Mags's birthday on 30 October, eighteen dates against
  fourteen.

| Need | Before | After |
|---|---|---|
| N1 the rego | evidence served | evidence served; `coming-up` lists 3 November unasked |
| N2 the mole | evidence served | evidence served, now by 20 too |
| N3 the health fund | found, asked | found, asked |
| N4 Mags | an accident | an accident in the answers; `coming-up` lists her birthday unasked |
| N5 the ring | evidence served | **found, asked**: 19 serves the promise |
| N6 the tax | found, asked | found, asked |
| N7 the roof | found, asked | found, asked |

**Four of seven found as asked, two with evidence served, one by accident,
none missed**, against three, three, one and none. The traps are as they
were: T2 still springs (the budget's estimate first), T5 still holds.

`test_stack.py` runs all of this on every CI run and holds the stack to the
states after the fixes: what each question came to, what a few of them
served, and what each question read as her files spell it came to.
