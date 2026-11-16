# the week, over a life

The game box's prep sheet, made for a life instead of a game master's
binder: run at the start of a week over a person's own record. Each step
has the want it answers above it. `life_box.py week` runs it at the
person's own today, keeping each run in a folder of its own.

    python adapters/stdlib/stack/stack.py --box DIR --stack week.md --to RUN

`{today}` is the person's today. life_box.py writes it in before the stack
runs, since a made-up life has a today of its own.

## what's coming

Want 1: "What's about to happen to me?" Every date in my files in the next
three weeks, soonest first: renewals, appointments, deadlines, what a
calendar holds. Three weeks, not two, so a test or a renewal a little way
out is seen while there is still time to book it.
- coming-up -- --box {box} --days 21 --now {today}

## what's waiting on me

Want 2: "What do I have to decide?" What's waiting on my seal, what I sealed
that has gone stale, and what's coming up, on one page.
- digest -- --box {box} --now {today}

## what I'm owed, and what I owe

Want 3: "Who hasn't paid me?" Every invoice I sent, by its number, held
against what my bank and my email say came in. A payment that matches by
sum but names no invoice is shown to check by hand, never counted as paid.
- invoices -- --box {box} --id 'INV-\d+' --now {today}

Want 4: "Who do I owe, and who owes me?" Every line that speaks of a debt
or a loan, in notes and messages, each cited.
- debts -- --box {box}

## what goes out every month

Want 5: "What am I paying for, and when does it go out next?" Every
standing payment in my statements, what it costs a month, and when it
comes next.
- subscriptions -- --box {box}

## where things stand

Want 6: "What did I mean to do?" Every line marked to do, oldest first,
the unticked boxes among them.
- todo -- --box {box}

Want 7: "What did the money come to?" Every sum of money in my files, with
its date and the line it is on.
- amounts -- --box {box}

## what's new

Want 8: "What changed in my files since I last looked?" Every file new,
edited or gone, put on the record as fingerprints, never words.
- what-changed -- --box {box}

## does the box hold

Want 9: "Is my box sound?" The record, the approvals, the files and the
words list, checked.
- box-health -- --box {box}
