<!-- willow-addon
section: Play
line: What a game's table holds true, a heads-up when a new word meets it, and the GM's choice kept: replace it, keep both, take a yes back.
source: new
added: 2026-11-23
version: 0.1.0
writes: record
network: none
role: tools
uses: game-master, table, contradictions
from: shape, https://github.com/rudi193-cmd/die-namic-games, Apache-2.0
-->
# game-canon

What a table has made true across every game of
[game-master](../game-master/) on the record, and the heads-up a game master
needs before deciding something new: on such a day this table made this true,
and your new word is about the same thing.

    python adapters/stdlib/game-canon/game_canon.py --box DIR holds
    on 2026-11-20 (row 14): The egg is a real dragon's.
       proposal:3f9a…

    python adapters/stdlib/game-canon/game_canon.py --box DIR meets "The egg was never a real dragon's; it's a painted stone."
    on 2026-11-20 (row 14): The egg is a real dragon's.
       proposal:3f9a…

    python adapters/stdlib/game-canon/game_canon.py --box DIR replace --old proposal:3f9a… --new proposal:77c1… --fact "The egg was never a real dragon's; it's a painted stone."
    waiting on your seal: proposal:b20e…

| Command | What it does |
|---|---|
| `holds` | every call and offer you sealed, in every game, less what a sealed replacement stands over |
| `tonight` | the same, since the last session ended (session-seal's `session` row) |
| `meets FACT [--subject S]` | what the table holds true that FACT is about the same thing as |
| `replace --old S --new S --fact F` | "mine stands now": a replacement handed in, waiting on your seal |
| `take-back --old S` | a yes pressed by mistake: a replacement whose new word is nothing, waiting on your seal |
| `both --old S --new S --fact F` | "both are true": the pair isn't raised again |

`--json` gives `holds`, `tonight` and `meets` as a list, each truth's
`subject`, `fact`, `n` (the row of your seal) and `day`.

**About the same thing** is [table](../table/)'s heads-up, run over a game's
calls and offers, which is [contradictions](../contradictions/)' rule
unchanged: the two share at least two of their own words, and at least half
of the shorter one's. It can't tell whether they disagree and never picks a
side. Not raised: the word itself (`--subject`), the same words made true
again (a story played twice), and a pair you said are both true.

**Your choice is kept, and nothing here chooses.**

- **Mine stands now.** `replace` hands in, through the kernel's own `bite`
  and `propose`, a proposal that the new word stands in place of the old,
  and writes a `table-replaces` row naming it (`old`, `new`, `fact`,
  `subject`). It stops there, exit 42. The old one stops standing only when
  you seal that proposal with `kernel.py seal`; declined, it still stands.
  Either way the old one stays on the record, its seal untouched.
- **A yes taken back.** `take-back` is the same, with nothing as the new
  word. Nothing takes a seal back; a sealed take-back stands over it.
- **Both are true.** `both` writes a `table-both` row (`pair`, `facts`). It
  changes no truth, so it is a row and no seal.

Only something the table holds true now can be replaced or kept beside;
anything else is refused by name, and nothing is written.

**Rows:** [table](../table/)'s own `table-replaces` and `table-both`, in its
shape and read by its rule, so one record can hold a game's calls and a
table's words, and a replacement or a "both" made at either reads the same
at the other. A replacement's proposal is the table's too:
`table/replaces/<day>-<the old subject's first 16 hex>.md`. The one
difference is the seal: the table's host types a replacement at its terminal
and the table seals it there; here it waits on yours. Each row's `who` is
`game-canon`.

**Source:** Die-Namic's heads-up (its box's clash module), rebuilt here as an add-on
over game-master's record, with its seals left to you.

**Uses:** game-master's `games` and `ruling`; table's row kinds, `replaced`,
`meets`, `last_end`, `hand_in` and its slip; the kernel's `read`, `append`,
`bite` and `propose`.

**Never:** seals or declines anything, reads your key, writes the record
except through the kernel, or goes online.
