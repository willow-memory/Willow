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

- 46 passages are offered for 17 of them. She seals 16 and declines 30.
  Ten questions have an answer she made true. The three the kernel finds
  nothing for ("has kirsty paid me yet", "anything I'm about to forget
  before november", the Thai place) stay unanswered: it serves a passage
  only when it holds half the question's words. Ana's wedding is two
  questions in one breath, asked as each (below): five passages are offered
  and she declines them all.
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
- 54 passages are offered for 19 of her twenty questions. She seals 20 and
  declines 34: sixteen questions answered (fifteen without pypdf, below).
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
Recipes, and a pile for each other folder) and 86 passages are offered (85
without pypdf), against 54 in one box: she seals 23 and declines 63, and
seventeen questions are answered, one more than in one box. The scone
recipe is in, and so is "that quote about loss I highlighted on the kindle"
(below), and the stone-done email for question 14's second part (below). The
other gains are more of what her key names (the Tax note for the deadline,
the cancellation mail for her skin check, two more for Aoife's birthday) and
more declined beside them. Teodora, opened with `--dates day-first --piles`,
is laid as twelve piles; 57 passages are offered, she seals 19 and declines
38, and eleven questions are answered, one more than in one box. "Did
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

(Measured before a question could be asked in parts; the seven row is now
86 / 23 / 63 / 17, 85 / 23 / 62 / 16 and 57 / 19 / 38 / 11.) Seven is the
smallest deal that answers as many questions as ten. What ten
keeps over it is three more sealed passages on questions already answered (the
cancellation mail for her skin check, a calendar line for Aoife's birthday and
the jeweller's mail about the ring claws); at six, Bernadette loses two
questions. Teodora's eleven are there from three.

## A question that asks two things

"What did colleen say about mam's headstone, how much was my half" asks two
things, and the kernel serves a passage only when it holds half the question's
content words. The 2022 email about the stone holds "headstone" and more, and
is served; the 2024 email that says "Your half is EUR 725" holds one of the
five, and never was. So `ask` splits a question the way the
[ask-parts](../../adapters/stdlib/ask-parts/) add-on does (at a comma, "and"
or "also", and only where each side is itself a question) and asks each part
the whole way a question goes: spelling read, a pile it names, every pile
bitten, dealt in turns. Asked alone, "how much was my half" serves
`Mail/Inbox/2024-04-22 Stone done photos.eml.txt:6` in her Mail pile, and her
key names it ("Your half"): sealed.

A proposal reaches only the last bite of its box, so each part is bitten and
proposed in turn, a part's passages right after its own bite, never every
part bitten first. The claim still says `answers question 14, "what did
colleen say about mam's headstone, how much was my half"` with the whole
question, so her key, keyed by number, reads it; it ends with `, part 2 "how
much was my half"`, and recap shows each part under the question. A question
of one part is asked as it was and its claim has no part.

The parts share the question's deal (seven passages in all, four and three
for two parts) rather than each being dealt seven. Both measured, the whole
scenario (open, week, ask, decide, words, ask, decide, recap), offered /
sealed / declined / questions answered of 20:

| | Bernadette piles | without pypdf | Bernadette one box | without pypdf | Teodora piles |
|---|---|---|---|---|---|
| asked whole | 86 / 24 / 62 / 19 | 84 / 24 / 60 / 18 | 54 / 22 / 32 / 18 | 52 / 21 / 31 / 17 | 52 / 19 / 33 / 11 |
| each part dealt seven | 96 / 25 / 71 / 19 | 94 / 25 / 69 / 18 | 58 / 22 / 36 / 18 | 56 / 21 / 35 / 17 | 57 / 19 / 38 / 11 |
| the parts share seven | 91 / 25 / 66 / 19 | 89 / 25 / 64 / 18 | 58 / 22 / 36 / 18 | 56 / 21 / 35 / 17 | 57 / 19 / 38 / 11 |

The same is sealed either way, and no trap is. Sharing offers five fewer on
Bernadette's piles, so it is the rule. On one box the stone-done email is not
served: the kernel serves three passages from the whole life and others rank
above it. The two questions it splits are
Bernadette's 14 and Teodora's 17 ("what was I going to do for ana's wedding
and how far along am I"): part 2 of 14 is sealed, and Teodora's five are
offered and declined, since her key names none of them.

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
`financial = fy, eofy`, and a third for a question that is not a passage's to
answer at all, `electricity = energy, origin` (below). Then, with the table she
already has:

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
| piles | 86 / 23 / 63 / 17 | 91 / 25 / 66 / 19 | 85 / 23 / 62 / 16 | 89 / 25 / 64 / 18 |
| one box | 54 / 20 / 34 / 16 | 58 / 22 / 36 / 18 | 53 / 19 / 34 / 15 | 56 / 21 / 35 / 17 |

Question 2 is offered the 2026 notice's `Mail/Inbox/2026-10-06 Registration
renewal notice SUBARU FORESTER 1XY4KD.eml.txt:10`, which holds "$912.40", and
her key names it: sealed. With piles it is offered last year's notice too (the
trap, "2025-10-07 Registration...") and the budget's estimate, and both are
declined. Question 6 is offered `Documents/Rental unit 2025-26.xlsx.txt:3`,
which holds "21840", and her key names it: sealed. The statement's own scan
and the sheet's expenses are declined.

## A sum is a step's to give: question 18

"How much did we spend on electricity this year" has no one passage that
answers it. The answer is a sum over her bank lines, one `BPAY ORIGIN ENERGY
6631094` a quarter, written with a minus before the amount since the money went
out, in `Bank/CommBank_SmartAccess_FY*.csv`: $446.06 on 25 January, $479.80 on 25
April and $728.50 on 25 July, $1,654.36 for 2026 so far. The kernel serves a
passage only when it holds half the question's words, and no bank line holds
"spend" or "year"; the one passage it does serve, her household budget sheet (an
estimate: "Electricity & gas (Origin)", $215 a month), is declined.

The [route](../../adapters/stdlib/route/) add-on reads the question as `money
spent` (by "spend") and names three steps: [spent](../../adapters/stdlib/spent/),
which adds up the money-out lines that say what the question names, then
amounts and subscriptions. The week has no `spent` step, since a step of the
week takes no question of its own, so `ask` runs it itself, for each question
route sends it to (this is the only one of Bernadette's, and one of
Teodora's), over the box of the whole life (with piles, the box laid beside
them), on the question as her files spell it, at her today. It keeps what it
prints in DIR/spent/NN.txt, beside the week, and `recap` shows it the way it
shows every other step, as `see`:

    18. how much did we spend on electricity this year
          declined  Documents/Household budget 2026.xlsx.txt:3
          see       spent: 1,654.36 in 3 payments; calendar 2026, 2026-01-01 to 2026-10-24 (so far); spent/18.txt
                    2026-01-25     446.06  Bank/CommBank_SmartAccess_FY2025-26.csv:124
                    2026-04-25     479.80  Bank/CommBank_SmartAccess_FY2025-26.csv:50
                    2026-07-25     728.50  Bank/CommBank_SmartAccess_FY2026-27.csv:77
          see       amounts: week/001/10-amounts.txt
          see       subscriptions: week/001/08-subscriptions.txt

It needs her word. On day one, with the starter list, her bank says ORIGIN
ENERGY and not "electricity", and spent says so (`see       spent: No money-out
line in this period holds all of: electricity; ...`): it adds up nothing it
wasn't told is the thing. On day two `electricity = energy, origin` (her own
file's words: her budget's line is "Electricity & gas (Origin)" and her bank's
is ORIGIN ENERGY) finds the three. Asked "last financial year" it would find
the four of 2025-26, $2,206.28, and "this financial year" the one of 2026-27,
$728.50. Each line carries its file and line number, so she can check every one
against her statement.

**A sum is never sealed.** A total is not a passage, and a proposal can only
cite the passages one bite served, so nothing here is proposed: the record
never hears of it, `decide` never sees it, and the counts above are the same
with it and without it, with pypdf and without. (The new words line offers
nothing more either: measured on one box, 54 offered, 20 sealed and 34 declined
the first time and the same after, with and without the line.) What spent
gives is the step's answer, kept in a file and shown as `see`, for her to read;
her seal is for a passage she has read and agrees says it.

Teodora's twenty have one: "what did we end up paying for the new boiler" is
`money spent` (by "paying for"), so it is run through spent too, and spent finds
nothing. It asks for a sum over lines that say a thing, and she asks for one
purchase: spent needs every word of the question in one money-out line, "end",
"up" and "new" among them, and no line says them, so recap shows `see
spent: No money-out line in this period holds all of: end, up, new, boiler;
every date, up to 2026-10-22; spent/10.txt`, then amounts (which lists her
journal's "Boiler condemned. £3,680.") and subscriptions as before. The pointer
is the honest one: the bank's only BOILER lines are Dev's loan, £600 in and
£250 paid back, so "boiler" alone would add up 250.00 and call it what she paid
for the boiler. The warranty file's "Total cost £3,680.00. Paid: £1,840.00
card ..." is a file, not a bank line, and spent never adds it. "how much did I
actually make last year" is money made, so it is not sent to spent.

## The other demo lives

Four more demos have a `make_life.py`. The life box lays a person's life and
asks that person's own questions of it, so each was read for whether it is one
(laying them is [test_life_box_studies.py](test_life_box_studies.py), about
twenty seconds). `make_life.py` runs on the copy in the table, as it does for
Teodora, and nothing is written back: the test holds every file under the four
demos' folders by SHA-256 through the run, since three of them are frozen.

| demo | laid | why |
|---|---|---|
| [ofrenda](../ofrenda/) | yes | Marisol's life, and the first three of its seven questions are hers, asked of it. The other four are put to two books from Project Gutenberg, not to her files, and are left out |
| [money-hour](../money-hour/) | no | four people's folders (23 files), and its `questions.json` holds no question: facts, traps, wagers and pass rules, claims about the markets held to a record outside anyone's files. A box over the four would be nobody's life, and PLANTED.md's traps are what claim-check, misquote and pair-drift are for, not a person's answer key |
| [stewart-crossover](../stewart-crossover/) | no | Wren's files (8) held beside a real man's life: facts, quotes and traps held to publishers. She asks nothing of her own files; the questions are the study's, about him |
| [johnson](../johnson/) | no | five people's folders passed one report; Ines's four questions are inside `scene.py`, no file of theirs, and a box over `life/` would pile Walt's, Aurelie's, Tamsin's and Harold's with hers |

`open` refuses the three, before it makes anything, and says which: a
`questions.json` with no `questions` list, or a demo with neither a QUESTIONS.md
nor a questions.json.

### What `open` reads now

- **Questions.** QUESTIONS.md as before; failing that, the `questions` of
  questions.json, each `ask` in order and word for word, those put to the
  person's own files (a `box` of their own name, or none). Ofrenda's three.
- **Today.** The `TODAY = date(...)` of make_life.py as before; failing that, a
  `today` in questions.json (money-hour's, 2026-11-05); failing that, the `NOW`
  its run.py asks at. Ofrenda's make_life.py has no TODAY and its
  questions.json no `today`, so it is run.py's `NOW`, 2026-10-31: the same day
  as the last line of Marisol's diary, "Tomorrow the marigolds. I want to ask
  her files, not a guess." With none of the three the demo is refused.
- **The readers.** `--read` now also runs
  [shell-history](../../adapters/stdlib/shell-history/), but only on a life
  that holds a bash, zsh or fish history, so Teodora and Bernadette are read
  as they were.

### Ofrenda

Opened `--read`, at her today: 11 files, Femia's terminal history read into
dated lines. Options by what they changed, asked of the same three questions:

| laid | offered | questions with an offer |
|---|---|---|
| as written | 5 | 2 |
| `--read` | 5 | 2 |
| `--read --piles` | 8 | 2 |

`--read`, because it is how her life is read: the deleted file's command is a
line dated 2019-12-21 16:45:40 UTC, where raw bash history holds it under an
epoch number. `--piles` offers three passages more and answers nothing more:
the life is eleven files and three questions, and a pile per folder spreads
what one box already serves. `--dates` says nothing here: no file writes a
date that reads both ways.

- 1, "what was the secret in the biscochitos": three offered, the deleted
  file's command (`bash_history.txt:189`) first, then two diary lines.
- 2, "why does the old computer beep at midnight on november 2": two, Femia's
  note about cron (`notas/computadora.txt:9`) and a diary line.
- 3, "where did she hide the deed to the land": nothing in the life holds it,
  as demo/ofrenda froze it to be: the kernel serves a passage only when it
  holds half the question's words.

Five passages wait, none sealed. Ofrenda has no answer key and no PLANTED.md,
so `decide` refuses ("no answer key beside this"), and Marisol's answers wait
on her own seal. The record verifies. Nothing was declined, so no question is
answered.

**Gaps.** None that an add-on would close. The box offers the passage; whether
the command at line 189 is the secret, and whether Marisol's diary lines say
the same thing, is hers to read and seal. The week already runs over her files:
coming-up finds her 2026-10-31 line, and people finds Joaquín in four files and
Rosa in three. The one line missing is for money-hour: a questions list for one
of its four people, written in a new freeze, before the box could lay that
person's folder.

## Odile

Odile Varga ([demo/odile](../odile/)) is a piano tuner and beekeeper of sixty-one
who keeps her father in her house: 254 files of tuning log, hive notes, a care
log, voice memos, texts, mail, her money and one calendar. Her
[odile.json](odile.json) is her answer key, written from her
[PLANTED.md](../odile/PLANTED.md). Her eleven questions are
[QUESTIONS.md](../odile/QUESTIONS.md): lifted unchanged from the first pass of
her [STRIP.md](../odile/STRIP.md), where they were asked of her folder with no
key, in the order they appear there, each once (eleven, not twenty).

    python demo/life-box/life_box.py open --who odile --table DIR --read --piles

### The options, by evidence

- `--read`: her calendar is an `.ics`, which only the calendar reader turns into
  dated lines (`2026-10-28  Tune - Benedikt Ybarra`, not a `VEVENT`); the other
  253 files are text and csv, copied as they are. It changes no count.
- No `--dates`. She lives in the US, so month-first, but her files write dates
  as `2026-10-16`, `Oct 2027` and `March 20, 2026`; the only numbered dates are
  her father's date of birth and a hospital stay, which no question reads. And
  [month-first](../../adapters/stdlib/month-first/) mirrors only `.txt`, `.md`
  and pages, so it drops her care log, her card reader's export and Teo's
  sheet: opened with it she is answered on none of her eleven questions in one
  box (0 sealed), one in piles.
- `--piles`: her folders are one per matter (`tuning/`, `hives/`, `dad/`,
  `mail/`, `memos/`, `money/`, `texts/`, and her calendar loose at the top).

|  | one box | piles |
|---|---|---|
| offered / sealed / declined | 30 / 7 / 23 | 41 / 9 / 32 |
| questions answered | 4 (3, 4, 7, 8) | 4 (3, 4, 7, 10) |

Piles are chosen for one question, "I'm tired": in one box it serves her tuning
log (a Steinway M, a client named Weight), and her night memo "Tired." and what
she told Kati ("fine, tired") are never offered; her memos and
texts are piles of their own, and both are, and she seals them. The cost is
"is anything wrong with the hives": "hives" names the pile, and what is left,
"is anything wrong with the", is not in her hive notes, so that question, which
one box answers with hive 4's no eggs, no brood, is left unanswered.

### What happens

At her today, 2026-10-22: 41 passages are offered for seven
of her eleven questions (nothing is held for the other four), and she seals 9
and declines 32. Four questions are answered:

- "Dad's weight": the cardiologist's line, *call the office if weight goes up
  more than 2 kg in a week* (N2). The care log's first rows are offered and
  declined: they are 2025's, and the rise to 75.1 is at its end.
- "what do I need to do": the county's notice, *you may file a response within
  180 days*, which ran out on 2026-09-16 (N3), and her memo of selling Teo's
  van, *need to call Mesa Mutual and take it off the policy* (N6). The 2024
  letter, already answered (T2), is never offered.
- "how are the bees": the two passages that hold hive 4's September and October
  inspections, *eggs none, brood none* (N5), which she reads as a queenless hive;
  nothing says so.
- "I'm tired": her memo "Tired." and three stretches of her texts to Kati, each
  "me: fine, tired" (N7).

### The traps hold

 Harriet Weight (T1) is offered for "I'm tired" and declined.
The Dry Creek order paid in cash (T3), which only her memo says, is offered for
"invoice not paid" and declined: it is not one of the unpaid. Hers are two
other orders, and no passage says so.

### Her father
"how's Dad doing" and "is Dad okay" are nothing at all as piles ("Dad" names
`dad/`, and the files say *Laszlo*), and in one box the first is offered her
calendar's *Dad - pharmacy refills* and the second her own memo, "Okay.", which
is hers and not his. All of it is declined.

### Her words

 There is no `odile-words.txt` and `words` is refused for her.
Her one-line list in STRIP.md, `due = next`, is already in the starter list
(its `due` line says *deadline, expires, expiry, renewal, next*), and `dad =
laszlo`, tried with it for the two questions about her father, served the same
passages. Nothing she said was a word her files said another way; what is
missing is a reading, not a word.

### What is left, and what would close it

 Seven questions are unanswered.
Each is a gap an existing add-on or a line in her stack already points at; none
is built here.

| question | why | closes it |
|---|---|---|
| 1 "something that tells me who's due" | the right file, the wrong rows: her latest `next: Oct 2027` visits. Who is due is a date passed with no visit since | the [readings](../../adapters/stdlib/readings/) add-on, which on this box (STRIP.md's second pass) says the seven, *gone by, nothing written since*, four truly due |
| 2, 11 "how's Dad doing", "is Dad okay" | a trend is not a word; and as piles "Dad" names `dad/` | readings (STRIP.md's second pass): *75.1 on 2026-10-21, up 2.5 in one week*, beside the cardiologist's 2 kg |
| 5, 6 "did the schools pay me", "invoice not paid" | an unpaid order is a deposit that isn't there; her invoices say `PO 2026-095`, not `INV-` | [invoices](../../adapters/stdlib/invoices/) takes the id pattern, but her payments never name the PO, so no step matches them: a line she can add to a stack, not a word |
| 8 "is anything wrong with the hives" | in piles the question loses "hives" and asks for "wrong" | one box answers it; her notes never say "queenless" |
| 9 "how am I doing" | nothing holds it, and her answer is "fine" | none: [gaps](../../adapters/stdlib/gaps/) says where a log stops; her memos shrink and no add-on says so |

## Where it comes from

The [game box](../game-box/), with the binder swapped for a life:
the record, the stack, the bite and the seal are the same pieces. Teodora,
her questions and her answer key's evidence are
[demo/teodora](../teodora/)'s, built blind against the starter words list;
the [starter-words](../../adapters/stdlib/starter-words/) add-on is what
makes "how much do I still owe dev" find anything at all.
