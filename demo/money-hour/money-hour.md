# the money hour, for its host

Teo's stack, run on her own box before each call: what was said and by
whom, who comes up, every sum her notes hold, what's due, and what's still
on her list, what waits on her seal, and what she has asked. The clock is set to the demo's today, so the run is the same every
time; drop `--now` to use your own. It reads her files only, and suggests nothing; the market
figures are checked against the sources by run.py, not here.

    python adapters/stdlib/stack/stack.py --box DIR --stack demo/money-hour/money-hour.md

## who said what, and when
- said -- --box {box}

## who comes up
- people -- --box {box}

## every sum in the notes
- amounts -- --box {box}

## what's due
- coming-up -- --box {box} --days 30 --now 2026-11-05T12:00:00Z

## still to do
- todo -- --box {box}

## what waits on her seal
- digest -- --box {box} --now 2026-11-05T12:00:00Z

## what she has asked, and what found nothing
- history -- --box {box} --now 2026-11-05T12:00:00Z
