<!-- willow-addon
section: Play
line: A tabletop game's rolls and rulings as rows on the record, with the game master's calls sealed.
source: bot
added: 2026-11-01
writes: record
network: none
-->
# game-master

A story played beat by beat, with every roll and every ruling a row on the
record. The dice are [dice](../dice/)'s, the chances are [odds](../odds/)'s,
and the game master's calls are yours: this never makes one.

    python adapters/stdlib/game-master/game_master.py --box DIR open   --world night.json
    python adapters/stdlib/game-master/game_master.py --box DIR status --world night.json
    python adapters/stdlib/game-master/game_master.py --box DIR act Weird --world night.json
    python adapters/stdlib/game-master/game_master.py --box DIR ask    --world night.json
    python adapters/stdlib/game-master/game_master.py --box DIR settle --world night.json
    python adapters/stdlib/game-master/game_master.py --box DIR check

**An action beat** is rolled with `act STAT`: dice's own `2d6` roll (a `roll`
row, seeded by the record's tip, so nobody picks the faces), plus the acting
character's stat, read as **strong** (10 or more), **weak** (7 to 9) or
**miss** (6 or less). A `table-beat` row names the roll just before it, and
the beat's own line for that band is printed. `status` shows, for each stat,
the exact chance of each band, as odds counts them.

**A decision beat** is a ruling. `ask` hands the beat's fact in as a proposal
through the kernel's own `bite` and `propose`, and stops: the beat is waiting
on you. You answer with `kernel.py seal` (yes) or `kernel.py decline` (no).
Then `settle` reads your proof back through the kernel (`sealed`, `declined`,
`standing`) and writes a `table-beat` row naming your row. Until then nothing
moves, and nothing here can answer for you: a name, a seal made with another
key, a seal over some other proposal or another game's, or a proposal file
changed after you sealed it, moves nothing. A no moves the story on too;
what it records is the no.

**A world** is a JSON file:

    { "id", "title", "setting", "stats": ["Grit", ...], "base_stat": 1,
      "characters": [{ "id", "name", "role", "seat", "stats": {"Grit": 3} }],
      "places": [{ "id", "name" }],
      "scenes": [{ "id", "title", "place", "opening": ["..."], "beats": [
          { "id", "kind": "action", "prompt", "suggests": "Grit",
            "outcomes": { "strong", "weak", "miss" } },
          { "id", "kind": "decision", "prompt",
            "proposes": { "fact", "proposed_by" } } ] }] }

Stats are whole numbers; a stat missing from a sheet is `base_stat`. Seated
characters take the beats in turn. A world that isn't this is refused, naming
where. The game records the world's SHA-256 when it opens, and refuses the
file if it has changed since.

`check` needs no world file: it throws every roll again from its seed
(dice's check), then finds every `table-beat` that doesn't straight follow
the 2d6 it names, doesn't add up, or reports a ruling that no seal or
decline of yours stands behind. Given `--world` it also checks the order
of beats, whose turn it was, the stat and the line against the world.

Rows: `table-open` (the world's id and hash), `table-ask` (the proposal's
subject), `table-beat` (a roll's result, or a ruling), and the `roll`,
`bite` and `proposal` rows of dice and the kernel. Exit codes, the kernel's:
0 done, 42 waiting on your seal, 2 refused.

**Where it comes from:** the-table's story session in the SAFE App Store
(a world played beat by beat; action beats rolled 2d6 plus a stat; decision
beats that move only on the person's seal), rebuilt on the record: the
rolls are dice's rows, and the seal is the kernel's own.

**Left out:** the-table's puzzle beats (a world with one is refused), its
other games, and its sealed-fact tally outside the record. A record holds
one game of a world at a time.

**Never:** seals or declines anything, reads the key itself, or writes the
record except through the kernel (the rolls through dice, the proposals
through `kernel.py propose`).
