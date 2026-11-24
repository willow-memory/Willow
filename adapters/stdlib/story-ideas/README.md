<!-- willow-addon
section: Play
line: Story ideas between sessions, dealt from a game box's own words, with what was set up and never played and what's still open.
source: box
added: 2026-11-23
version: 0.1.0
writes: record
network: none
role: tools
uses: game-master, oracle-text, random-passage
-->
# story-ideas

Between sessions, for the game master's eyes: story seeds dealt from what
the box already holds, the people and monsters the binder sets up that no
night has met yet, every promise made for next time, and one passage you
wrote and forgot.

    python adapters/stdlib/story-ideas/story_ideas.py --box DIR --worlds <worlds folder> --pile <binder> --seed "between nights"
    # Ideas, for the GM's eyes

    ## Seeds (seed 'between nights': the same seed deals them again)

      - At the bridge, Ana comes face to face with the river hag.
      - What if Bo finds out where the toll money went, and doesn't tell the others?
      ...

    ## Set up, never played

      - River Hag  (monsters/)

    ## Still open

      sessions/night-1.md:2  Next time: where the toll money went.

    ## Something you wrote and forgot

      ...

`--box` is the game's record, `--worlds` the folder of
[game-master](../game-master/) worlds it plays, `--pile` the binder, laid
out as willow's game box lays one: `<binder>/people/` and
`<binder>/monsters/`, a page each whose first heading is its name, and
`<binder>/sessions/` and `<binder>/scanned/`, the notes of each night, typed
or scanned. `--count` is how many seeds (5).

**Seeds.** A [Tracery](https://tracery.io/) grammar of the box's own words:
the seated characters, the others and the places of the story last played
(every world in the folder, when none has been), the binder's people and
monsters, each thread promised after "next time", and each fact the GM
sealed in game-master, asked or offered. A declined fact is not canon and
never comes up. [oracle-text](../oracle-text/) deals from it on the seeded
stream, so the same seed deals the same ideas again; with no `--seed`, the
seed is the day's (`ideas YYYY-MM-DD`). A sentence shape is dealt only when
the box holds every part it needs; a box with too little says so.

**Set up, never played.** A person or monster with a page in the binder
none of whose name's words any night's notes have said yet.

**Still open.** Every line in the binder's Markdown and text files that says
"next time", by file and line, oldest file first.

**Something you wrote and forgot.** One passage drawn by
[random-passage](../random-passage/), which writes its `surprise` row, the
seed it can be drawn again from, on the record: the one row this writes,
through it.

**Source:** willow's game box, `demo/game-box/ideas.py`, and Die-Namic's
copy of it, rebuilt as an add-on that takes the box's folders as arguments.

**Uses:** game-master's `load_world`, `games` and `ruling`; oracle-text and
random-passage, each run as its own command.

**Never:** proposes, seals, reads your key, or goes online. Nothing it deals
is canon: an idea the GM likes, they write in their binder or a story.
