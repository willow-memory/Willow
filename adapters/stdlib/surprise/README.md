<!-- willow-addon
section: Finding things
line: One passage from your folder at random, seeded so it can be replayed.
source: bot
added: 2026-10-23
writes: record
network: none
-->
# surprise

One passage from your folder, drawn at random, and replayable: something you
wrote and forgot, brought back.

    python adapters/stdlib/surprise/surprise.py --box DIR [--seed HEX] [--now TS]

It draws one passage of at least eight words. With no seed, the seed is the
SHA-256 of "willow surprise" and the day, so it's the same passage all day and
a new one tomorrow; it prints the seed, and the same seed and folder always
draw the same passage.

**The draw:** [willow-bot's](https://github.com/willow-memory/willow-bot/blob/main/one-script/onescript/stream.py) `sha256-stream/v1`: SHA-256 over the seed and an
8-byte counter, the first four bytes as a number, and a pick by rejection so
no passage is likelier than another. Its tests hold it to the bot's stream,
draw for draw.

**On the record:** each draw is a `surprise` row, written through the kernel's
`append`: the seed, the generator, and the passage's id and place, never its
words.

**Uses:** the kernel's `chunks`, `words`, `config`, `read`, `append` and
`now`.

**Never:** writes anything but its row, or reads outside your folder.
