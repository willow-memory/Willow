# the life box: the game box, with a person's life for its binder

What happens when a life goes into the game box? The game box is a game
master's binder, read through their words, prepped with a stack, and
nothing in it stands until the one who holds the key seals it. A life is
the same shape: a person's files, read through their words, a week to get
ready for, and nothing an answer until they say so.

This lays one of willow's made-up people (demo/NAME, written by their
`make_life.py`) as the binder, reads it through the starter words list
everyone begins with, runs a week's prep at their own today, asks their
own questions (their `QUESTIONS.md`), and lets them decide each answer
with a key made for them.

    python demo/life-box/life_box.py open   --who teodora --table DIR --dates day-first
    python demo/life-box/life_box.py open   --who bernadette --table DIR --read --dates day-first
    python demo/life-box/life_box.py open   --who bernadette --table DIR --read --dates day-first --piles
    python demo/life-box/life_box.py week   --table DIR
    python demo/life-box/life_box.py words  --table DIR
    python demo/life-box/life_box.py ask    --table DIR
    python demo/life-box/life_box.py decide --table DIR
    python demo/life-box/life_box.py recap  --table DIR

| piece | what it is |
|---|---|
| [life_box.py](life_box.py) | the six steps: lay the life, run the week, add her own words on day two, ask the questions (each read the way the files spell it), decide them, say what was made true |
| [week.md](week.md) | the game box's prep sheet made for a life: what's coming in three weeks, what runs out, what the car and the house need, what's waiting on me, who owes me and whom I owe, what goes out every month, where things stand, the money in my files, what's new, does the box hold |
| [teodora.json](teodora.json) | Teodora's answer key: for each of her twenty questions, the files (and the words in them) she would seal as its answer, written from her [PLANTED.md](../teodora/PLANTED.md) |
| [bernadette.json](bernadette.json) | Bernadette's, the same for her twenty, written from [hers](../bernadette/PLANTED.md) and her files as willow's readers mirror them |
| [bernadette-words.txt](bernadette-words.txt) | Bernadette's own words, kept beside her answer key: only her lines, each with a comment saying whose file uses her word and what it says instead. `words` adds them to the starter list on day two |

## The seal, for someone made up

Teodora is made up, so her key is too: `open` makes it at DIR/teodora.key,
outside the record, and `decide` seals with it. That is the only seal this
demo writes, and only for a person with an answer key beside it. `decide`
refuses anyone without one. A real person's key is never made, read or
used here: their answers wait on their own seal.

What `decide` does is what she would: every passage offered for a question
is sealed if her answer key names its file, and what it must say, for that
question, and declined if not. A passage is offered only by `ask`, through
the kernel's own bite and propose, citing what was served.

## What happens

Her 308 files, laid at her today (2026-10-22), asked her twenty questions:

- 41 passages are offered for 16 of them. She seals 16 and declines 25.
  Ten questions have an answer she made true. The four the kernel finds
  nothing for ("has kirsty paid me yet", "anything I'm about to forget
  before november", the Thai place, Ana's wedding) stay unanswered: it
  serves a passage only when it holds half the question's words.
- The traps hold. "Did Hargreaves pay August?" is offered the ledger, which
  shows the invoice unpaid; it was paid, and she declines it (PLANTED.md's
  T2). "Is that HMRC refund thing legit?" is offered only the phishing email
  itself, and she declines all three of its passages (T1). Last year's
  insurance renewal is declined beside this year's card change.
- A question one passage can't answer is a sum over many, and an add-on
  already does that sum. The route add-on reads what kind each question is
  and points it at the week's step whose job it is: "has kirsty paid me
  yet" is money owed, and the week's invoices step has Bramble & Bean's
  three invoices overdue, £2,140, and Hargreaves' August payment found by
  its sum but never counted as paid, since it names no invoice. "How far
  along am I" with Ana's wedding is where it stands, and the week's todo
  step has the nineteen recipes not yet typed up. The week also finds Dev's
  £600, her eight standing payments, and last year's turnover.
- Her life is written day first, and only she would know: 03/11/2026 reads
  both ways, and coming-up never guesses. `--dates day-first` says it for
  her: the life is mirrored through the [day-first](../../adapters/stdlib/day-first/)
  add-on, every date given its ISO form beside it, and the box laid over
  the mirror. Then her week finds her two most urgent dates, her cover
  ending 03/11/2026 and the MOT running out 09/11/2026, in coming-up and in
  renewals, beside the insurer collecting on 27/10, half term and three
  invoices due 30/10. Opened without it, the same week finds neither; the
  test holds both.
- car reads the MOT certificate as the test's: its advisories (both front
  tyres, a corroded brake pipe) keep the test's day, not the expiry's, now
  that the expiry is readable above them.

## A life that isn't plain files

Bernadette's life is mail, calendars, WhatsApp, an Obsidian vault,
spreadsheets, a kindle and scans: the kernel reads none of it as it is.
`--read` runs willow's readers over it first, as a person who had them
would, each mirroring what it reads into one folder, and the files no reader
took copied beside them. Her dates are day first too (Ballarat), so the
mirror is then mirrored again through day-first.

- Her week finds what she most needs at her today (2026-10-24): the rego
  lapsing 03/11/2026, last year's gone by beside it; her health cover's last
  day, 14 November 2026, from the insurer's final notice; Mags's birthday on
  the 30th and the tax due the 31st. Her one thing marked to do is the bank's
  "update any recurring payments", which she didn't, which is why the cover
  is ending.
- 50 passages are offered for 19 of her twenty questions. She seals 20 and
  declines 30: sixteen questions answered (fifteen without pypdf, below).
- She spells some questions her own way, and `ask` reads each the way her
  files spell it before it asks, as her stack does: the typos add-on, then
  accents, each over the box. "What did the jeweler say" is asked as "what
  did the jeweller say", and the jeweller's quote is sealed. "Dermatoligist
  referal letter" is asked as "dermatologist referral letter" and is served
  her referral letter, which she seals, with two notes that only mention it,
  which she declines. A question already spelt as her files spell it is
  asked once, as written. The claim and the recap say `asked as "..."`.
- Her traps hold. "How much is the car rego this year" is offered only the
  budget's estimate, which she declines (PLANTED.md's T2); the true notice
  is in her week's renewals. "When is my skin appointment" seals the check
  she cancelled; the 5 Nov booking the calendar still shows, which the clinic
  cancelled, is never sealed (T3). "Aoifes birthday" is her granddaughter's,
  not Aoife Brennan's from bowls (T5). "Did I promise Siobhán anything" seals
  the ring and the mole; "Tomorrow, promise" was to Gerry.
- What it can't do yet, and says so: laid as one big pile, "scone recipe"
  is served the right file's wrong passage (its backlinks); [piles](#a-life-as-the-piles-its-person-keeps)
  below serve the recipe itself.
- Her week's subscriptions lists eight things she pays, about 4596.28 a
  month, and three that come in, written with a plus as her bank writes a
  credit: her super pension, the unit's rent and a tax refund, never added
  to what she pays. Lakeside's premium shows its last payment in July, a
  month that has gone by. The 4000.00 a month to her own saver is still
  counted as paid: nothing in the line says it stays hers.
- The scans are read by the pdf add-on, which needs pypdf. Without it, her
  referral letter isn't read, and the cancelled 5 Nov booking is offered in
  its place, and declined; "dermatoligist referal letter" then has no answer
  to seal. The test holds both.

## A life as the piles its person keeps

Real people keep their files a folder per matter, and each folder is its own
pile. `open --piles` lays the life that way: each top-level folder is a pile
with a box of its own (DIR/records/SLUG), all under the one key made for the
person; a folder holding exactly one folder and no files is only a way in and
is walked through (`Notes/` to `Notes/Bernie's Vault/`, and the folders
inside the vault are the piles); the files loose at a level are one more
pile, named for that level (`Notes/Bernie's Vault/.`, `.` for the top).
DIR/piles.json says which folder each box is. A folder that holds two
folders (`Mail/` with `Inbox/` and `Sent/`) is one pile. DIR/record is laid
beside them over the whole life: the week and the spelling add-ons each read
one box, so the week runs over that one, as it did, and nothing is ever
asked of it.

**Why it matters.** In one big pile a passage's path counts toward its
words, so every passage under `Notes/Bernie's Vault/Recipes/Scones.md.txt`
holds both "scone" and "recipe" from the path alone. They all tie, and the
tie-break (fewest copies, then newest) puts the undated recipe itself
("3 cups SR flour ... #recipe") behind dated chatter: five chat lines saying
"send me your scone recipe" and the note's own dated backlinks. As its own
pile the folder's name stops being a word every passage in it gets for free:
the recipe holds "recipe" from its `#recipe` tag and "scone" from its file
name, and comes first.

| "scone recipe" | the one pile | piles |
|---|---|---|
| offered | the backlinks, two chat lines | the recipe, a chat line, a recipe from another folder, ... |
| sealed | nothing | `Notes/Bernie's Vault/Recipes/Scones.md.txt:5` |

**`ask` with piles.** Every pile's box is bitten for each question, unless it names a pile
(below) (the question read in the files' spelling first, as before). What each served is
then dealt out in turns by [fair-merge](../../adapters/stdlib/fair-merge/)'s
own rule, which `life_box.py` calls rather than copies: the first of each
pile, then the second of each, a passage word for word in two piles shown
once, the question asked back left out. Up to seven are dealt: the kernel's 3
or fair-merge's 6 never reach the later piles of fifteen (see
[the deal](#the-deal)). Each is proposed in the box that
served it, citing only that box's last bite, and the claim's `from` is the
path in the whole life, so the answer keys read the same. `decide` and
`recap` walk every box; the recap names each answer's pile, and
`kernel.py verify` holds on every one.

**What it changes.** Bernadette opened with `--read --dates day-first
--piles` is laid as fifteen piles (the vault's loose notes, its Daily and
Recipes, and a pile for each other folder) and 81 passages are offered (80
without pypdf), against 50 in one box: she seals 22 and declines 59, and
seventeen questions are answered, one more than in one box. The scone
recipe is in, and so is "that quote about loss I highlighted on the kindle"
(below). The
other gains are more of what her key names (the Tax note for the deadline,
the cancellation mail for her skin check, two more for Aoife's birthday) and
more declined beside them. Teodora, opened with `--dates day-first --piles`,
is laid as twelve piles; 52 passages are offered, she seals 19 and declines
33, and eleven questions are answered, one more than in one box. "Did
Hargreaves pay August" now finds the remittance advice, which she seals, and
still declines the ledger line (T2); the phishing email stays declined (T1).

### A question that names a pile

A person says where to look: "on the kindle", "the scone recipe", "which AAT
exams". Inside its own pile a folder's name is no longer a word its passages
hold, so the word cannot be matched in the text, and it should not be: it
says which pile. A word of the question that a pile's own name holds (the
pile's folder, its last part, or for a loose pile the level's; the way the
kernel holds a word, so "recipe" names `Recipes/`, and "aat" names
`study/aat/`) sends the question to that pile alone, and is left out of what
that pile is asked. The other piles are not asked. The claim and the recap
say so: `asked of Kindle as "that quote about loss i highlighted on the"`. A
question left with no content word is asked as it is, and the top level's
loose files are named for nothing, so no word names them.

Why only the named pile, not every pile with the naming word dropped from
the one that has it. Measured on both lives at the same deal of ten:

| the question that names a pile is | Bernadette offered / sealed / declined / answered | without pypdf | Teodora |
|---|---|---|---|
| asked as it was (no rule) | 99 / 24 / 75 / 16 | 98 / 24 / 74 / 15 | 62 / 19 / 43 / 10 |
| asked of every pile, the named one without the word | 99 / 23 / 76 / 15 | 98 / 23 / 75 / 14 | 66 / 21 / 45 / 11 |
| asked of the named pile alone | 92 / 24 / 68 / 16 | 91 / 24 / 67 / 15 | 54 / 20 / 34 / 11 |

These three rows were measured before the Kindle reader kept `highlight`, which
moves only Bernadette: the last is now 93 / 25 / 68 / 17, and 92 / 25 / 67 / 16
without pypdf; the first two were not measured again.

Asking every pile fills the deal with the other piles' echoes of the same
word and crowds out the named pile's own turns: "scone recipe" asks the
Recipes pile for "scone", where all of Scones.md ties on its file name and
the recipe comes third, and with ten turns shared between all the piles
(Chats' "send me your scone recipe" lines among them) the third never comes.
Asked of that pile alone it is sealed, as before the rule. Teodora's "which
AAT exams have I passed" finds `study/aat/progress.md:3` again, and "does my
work insurance need anything from me" now finds the PI schedule.

Every question of both lives that names a pile, and what happens to it:

| question | names | asked as |
|---|---|---|
| Bernadette 12, scone recipe | `Notes/Bernie's Vault/Recipes` | "scone"; the recipe sealed |
| Bernadette 17, that quote about loss i highlighted on the kindle | `Kindle` | "that quote about loss i highlighted on the"; the clipping sealed |
| Teodora 1, when's the car due its mot | `car` | "when's the due its mot"; sealed as before |
| Teodora 7, when is maisie off school for half term | `maisie` | "when is off school for half term"; sealed as before |
| Teodora 14, which aat exams have I passed | `study/aat/.` | "which exams have I passed"; sealed |
| Teodora 18, does my work insurance need anything from me | `work` | "does my insurance need anything from me"; the PI schedule sealed |

No other question names a pile. The common names will be named by ordinary
questions ("what's my home wifi password" is asked of Home alone), which is
what saying "home" means here; a person whose wifi password is not in Home
has asked a pile that cannot answer, and is told nothing is held.

The kindle quote is found because the reader says what the file says. The
clipping, "Loss is nothing else but change", was written by books.py without
the word Kindle saved beside it, `Your Highlight`, so it held one of the three
content words left ("quote", "loss", "highlighted"), short of the half the
kernel serves at. Its header now says `highlight at location 288-290`, as the
file does, and the clipping holds "loss" and "highlighted", two of three: the
rule is not loosened and the named pile is not given its folder's name back
(that gives the scone recipe back to its tie). The reader had dropped what the
file said; the mirror now keeps it.

### The deal

How many passages are dealt for one question, with the rule in
(`--dates day-first --piles`). Offered / sealed / declined / questions
answered, of 20:

| deal | Bernadette | without pypdf | Teodora |
|---|---|---|---|
| 3 | 48 / 14 / 34 / 11 | 47 / 13 / 34 / 10 | 37 / 14 / 23 / 11 |
| 6 | 74 / 20 / 54 / 15 | 73 / 20 / 53 / 15 | 49 / 18 / 31 / 11 |
| 7 | 81 / 22 / 59 / 17 | 80 / 22 / 58 / 16 | 52 / 19 / 33 / 11 |
| 10 | 93 / 25 / 68 / 17 | 92 / 25 / 67 / 16 | 54 / 20 / 34 / 11 |

Seven is the smallest deal that answers as many questions as ten. What ten
keeps over it is three more sealed passages on questions already answered (the
cancellation mail for her skin check, a calendar line for Aoife's birthday and
the jeweller's mail about the ring claws); at six, Bernadette loses two
questions. Teodora's eleven are there from three.

[test_life_box.py](test_life_box.py) runs all of it in about a hundred
seconds.

## Day two: her own words

A starter list is general, and a person's own words are theirs: learned from
what found nothing, which is only known once the questions have been asked.
Two of Bernadette's twenty found nothing useful on day one, because she says
one thing and her files another:

- 2, "how much is the car rego this year": her calendar says "Car rego due"
  and her chat "Did you do the rego love?", but the notice VicRoads sent says
  Registration, and the amount, $912.40, is in the notice.
- 6, "total rent from the geelong unit last financial year": her own sheet,
  "Rental unit 2025-26", says FY and the agent's statement says EOFY, and the
  amount, 21840, is on the sheet.

The starter list is not tuned to a folder (its card says why), so these two
lines are hers, in `bernadette-words.txt`: `rego = registration` and
`financial = fy, eofy`. Then, with the table she already has:

    python demo/life-box/life_box.py words  --table DIR
    python demo/life-box/life_box.py ask    --table DIR
    python demo/life-box/life_box.py decide --table DIR
    python demo/life-box/life_box.py recap  --table DIR

`words` writes DIR/words.txt again, the starter list and then her lines,
readable only by her, and says what it added. It remakes no box: every box
of the life was laid pointing at that one file, and the kernel reads the file
at each bite, so each box keeps its record exactly as it was (every seal and
decline still there, `kernel.py verify` holding) and from its next bite on says
which list it read, by SHA-256. A box laid pointing at no list at all is what
the [later-words](../../adapters/stdlib/later-words/) add-on makes again. A
person with no words file of their own is refused, and nothing changes.

`ask` asked again asks only the questions with no sealed answer: the seventeen (sixteen on one
box) she already has are said to be answered and left alone (the kernel would only
answer each from its seal, a bite that serves nothing). The rest are asked
again with her words; a passage she already declined is refused by the
kernel (V.10), not offered twice. A flag would have made the person say what the box
already knows; asking only what is open is the same on a first ask, where
nothing is sealed, so nothing about day one changed.

Measured (offered / sealed / declined / questions answered,
of 20), the first ask and then the second:

| | first | after her words | without pypdf: first | after |
|---|---|---|---|---|
| piles | 81 / 22 / 59 / 17 | 86 / 24 / 62 / 19 | 80 / 22 / 58 / 16 | 84 / 24 / 60 / 18 |
| one box | 50 / 20 / 30 / 16 | 54 / 22 / 32 / 18 | 49 / 19 / 30 / 15 | 52 / 21 / 31 / 17 |

Question 2 is offered the 2026 notice's `Mail/Inbox/2026-10-06 Registration
renewal notice SUBARU FORESTER 1XY4KD.eml.txt:10`, which holds "$912.40", and
her key names it: sealed. With piles it is offered last year's notice too (the
trap, "2025-10-07 Registration...") and the budget's estimate, and both are
declined. Question 6 is offered `Documents/Rental unit 2025-26.xlsx.txt:3`,
which holds "21840", and her key names it: sealed. The statement's own scan
and the sheet's expenses are declined.

## Where it comes from

The [game box](../game-box/), with the binder swapped for a life:
the record, the stack, the bite and the seal are the same pieces. Teodora,
her questions and her answer key's evidence are
[demo/teodora](../teodora/)'s, built blind against the starter words list;
the [starter-words](../../adapters/stdlib/starter-words/) add-on is what
makes "how much do I still owe dev" find anything at all.
