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
    python demo/life-box/life_box.py ask    --table DIR
    python demo/life-box/life_box.py decide --table DIR
    python demo/life-box/life_box.py recap  --table DIR

| piece | what it is |
|---|---|
| [life_box.py](life_box.py) | the five steps: lay the life, run the week, ask the questions (each read the way the files spell it), decide them, say what was made true |
| [week.md](week.md) | the game box's prep sheet made for a life: what's coming in three weeks, what runs out, what the car and the house need, what's waiting on me, who owes me and whom I owe, what goes out every month, where things stand, the money in my files, what's new, does the box hold |
| [teodora.json](teodora.json) | Teodora's answer key: for each of her twenty questions, the files (and the words in them) she would seal as its answer, written from her [PLANTED.md](../teodora/PLANTED.md) |
| [bernadette.json](bernadette.json) | Bernadette's, the same for her twenty, written from [hers](../bernadette/PLANTED.md) and her files as willow's readers mirror them |

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
- 48 passages are offered for 19 of her twenty questions. She seals 20 and
  declines 28: sixteen questions answered (fifteen without pypdf, below).
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

**`ask` with piles.** Every pile's box is bitten for each question (the
question read in the files' spelling first, as before). What each served is
then dealt out in turns by [fair-merge](../../adapters/stdlib/fair-merge/)'s
own rule, which `life_box.py` calls rather than copies: the first of each
pile, then the second of each, a passage word for word in two piles shown
once, the question asked back left out. Up to ten are dealt: the kernel's 3
or fair-merge's 6 never reach the later piles of fifteen (3 loses the
recipe; 6 loses Bernadette's skin-check and pennant answers). Each is proposed in the box that
served it, citing only that box's last bite, and the claim's `from` is the
path in the whole life, so the answer keys read the same. `decide` and
`recap` walk every box; the recap names each answer's pile, and
`kernel.py verify` holds on every one.

**What it changes.** Bernadette opened with `--read --dates day-first
--piles` is laid as fifteen piles (the vault's loose notes, its Daily and
Recipes, and a pile for each other folder) and 99 passages are offered (98
without pypdf), against 48 in one box: she seals 24 and declines 75, and
sixteen questions are answered, as before. The scone recipe is in; "that
quote about loss I highlighted on the kindle" is out, because "kindle" was
only the folder's name and her one file of clippings no longer holds it. The
other gains are more of what her key names (the Tax note for the deadline,
the cancellation mail for her skin check, two more for Aoife's birthday) and
more declined beside them. Teodora, opened with `--dates day-first --piles`,
is laid as twelve piles; 62 passages are offered, she seals 19 and declines
43, and ten questions are answered, as before. "Did Hargreaves pay August"
now finds the remittance advice, which she seals, and still declines the
ledger line (T2); the phishing email stays declined (T1). "Which AAT exams
have I passed" is lost for the same reason as the kindle quote: `study/aat/`
is only the folder's name.

So a question that names the folder ("on the kindle") loses it. That is the
price of a folder's name no longer being free, and the answer is not to
loosen it.

[test_life_box.py](test_life_box.py) runs all of it in about a hundred
seconds.

## Where it comes from

The [game box](../game-box/), with the binder swapped for a life:
the record, the stack, the bite and the seal are the same pieces. Teodora,
her questions and her answer key's evidence are
[demo/teodora](../teodora/)'s, built blind against the starter words list;
the [starter-words](../../adapters/stdlib/starter-words/) add-on is what
makes "how much do I still owe dev" find anything at all.
