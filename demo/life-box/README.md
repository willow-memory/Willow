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
    python demo/life-box/life_box.py week   --table DIR
    python demo/life-box/life_box.py ask    --table DIR
    python demo/life-box/life_box.py decide --table DIR
    python demo/life-box/life_box.py recap  --table DIR

| piece | what it is |
|---|---|
| [life_box.py](life_box.py) | the five steps: lay the life, run the week, ask the questions, decide them, say what was made true |
| [week.md](week.md) | the game box's prep sheet made for a life: what's coming in three weeks, what runs out, what the car and the house need, what's waiting on me, who owes me and whom I owe, what goes out every month, where things stand, the money in my files, what's new, does the box hold |
| [teodora.json](teodora.json) | Teodora's answer key: for each of her twenty questions, the files (and the words in them) she would seal as its answer, written from her [PLANTED.md](../teodora/PLANTED.md) |

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

[test_life_box.py](test_life_box.py) runs all of it in about ten seconds.

## Where it comes from

The [game box](../game-box/), with the binder swapped for a life:
the record, the stack, the bite and the seal are the same pieces. Teodora,
her questions and her answer key's evidence are
[demo/teodora](../teodora/)'s, built blind against the starter words list;
the [starter-words](../../adapters/stdlib/starter-words/) add-on is what
makes "how much do I still owe dev" find anything at all.
