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

The list is this repo's add-ons and nothing else: each built one's card, and
each idea in [planned.json](../../planned.json).

| Command | What it does |
|---|---|
| `near` | Up to three entries the kernel's search serves for your words, each with the words it shares. A built one (✅) is something to connect to rather than build again; an idea (🛠) is already on the list, to pick up rather than add twice. |
| `check` | Refuses two entries with the same line, whatever the case or punctuation. CI runs it. An idea that is only near another is shown, never refused: only a person can say two ideas are one. |
| `new` | Markdown for a pull request: each add-on or idea added, or whose line changed, since REF, with what's near it. If nothing is near, it says so. willow-bot posts this on the pull request. |

## What it uses

`kernel.rank`, the same search a `bite` runs, so "similar" means what the
kernel means by it: an entry holding at least half your words, the rarer
words counting most. It reads the list through
[readme](../readme/), so an entry that doesn't hold together is refused
here too.

## What it never does

It never refuses an idea for being near another; it never reads anything
outside this repo; it writes nothing, and only prints.
