<!-- willow-addon
section: Play
line: A daily horoscope keyed on your name and the date: same name, same day, same reading, always.
source: bot
added: 2026-10-24
writes: nothing
network: none
-->
# horoscope

A reading for the day that can't be rigged.

    python adapters/stdlib/horoscope/horoscope.py Ana
    Today, Ana: the letter you've been meaning to write is shorter than you think.

The reading is picked by the SHA-256 of "name:date". The same name on the
same day gets the same reading on any machine, always, and anyone can check
it. `--date 2026-12-25` reads another day. `--coder` uses willow-bot's own
lines ("today is not the day for a rebase"), kept as they were; the default
set is for everyone else.

It predicts nothing. It's a toy that can't be rigged, which is the point.

**Where it comes from:** [willow-bot's horoscope](https://github.com/willow-memory/willow-bot/blob/main/horoscope.py), the same rule and the same
coder lines.

**Never:** reads or writes anything.
