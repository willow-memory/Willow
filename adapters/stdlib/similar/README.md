<!-- willow-addon
section: For maintainers
line: What's already on the add-on list near a new idea, by the kernel's own search.
source: box
added: 2026-10-23
writes: nothing
network: none
-->
# similar

Before you build an add-on or add an idea, see what's already on the list.

    python adapters/stdlib/similar/similar.py near "your idea in a sentence"
    python adapters/stdlib/similar/similar.py check
    python adapters/stdlib/similar/similar.py new --base REF
    python adapters/stdlib/similar/similar.py tags [NAME...]

The list is this repo's add-ons and nothing else, built and planned: each
one's line, and the tag a person chose for it, if any. Not the card's whole
text, whose common words made unrelated add-ons look alike.

| Command | What it does |
|---|---|
| `near` | Up to three entries the kernel's search serves for your words, each with the words it shares, then any entry whose own words yours hold by the same rule, counted against the entry, so a long line still finds a short one it contains. A built one is something to connect to rather than build again; an idea is already on the list, to pick up rather than add twice. |
| `check` | Refuses two entries with the same line, whatever the case or punctuation. CI runs it. An idea that is only near another is shown, never refused: only a person can say two ideas are one. |
| `tags` | Each entry's tags and its three nearest entries, as the add-on list shows them, worked out from the cards every time and never stored: needs an install or not, goes online or not, two topic words, and the author's own tag. The topics come from the entries nearest it, ranked against the whole card by [pile-rank](../pile-rank/)'s BM25: words from their names and one-line descriptions that this card also uses, which a handful of entries share and most don't. Words that say how a card is written rather than what it's about (`HOW` in the code) are never topics: that list is the knob when a topic reads as noise. |
| `new` | Markdown for a pull request: each add-on or idea added, or whose line changed, since REF, with what's near it. If nothing is near, it says so. On GitHub, CI writes it to the run's summary and keeps it as the run's `similar` artifact, and willow-bot posts it in its status comment on the pull request. |

## What it uses

For `near`, `kernel.rank`, the same search a `bite` runs, so "similar" means what the
kernel means by it: an entry holding at least half your words, the rarer
words counting most. It reads the list through
[readme](../readme/), so an entry that doesn't hold together is refused
here too.

## What it never does

It never refuses an idea for being near another; it never reads anything
outside this repo; it writes nothing, and only prints.
