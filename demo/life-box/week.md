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

## what's new

Want 3: "What changed in my files since I last looked?" Every file new,
edited or gone, put on the record as fingerprints, never words.
- what-changed -- --box {box}

## does the box hold

Want 4: "Is my box sound?" The record, the approvals, the files and the
words list, checked.
- box-health -- --box {box}
