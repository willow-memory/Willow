<!-- willow-addon
section: For maintainers
line: Builds ADDONS.md, and the README's one feature, from the add-ons' own cards.
source: new
added: 2026-10-23
writes: README.md, ADDONS.md
network: none
role: repo
uses: similar, skim
runs-in: repo
-->
# readme

The add-on list in ADDONS.md, and the one feature the README's front page
shows, built from the add-ons themselves, so neither can drift from what's in
the repo.

    python adapters/stdlib/readme/readme.py write [--week YYYY-Www]
    python adapters/stdlib/readme/readme.py check

| Section | What it shows |
|---|---|
| pools | how the add-ons spread: by section, built and ideas, how many need an install, with a progress bar |
| newest | the five most recently built add-ons, by the date on their card |
| pick | the add-on of the week, drawn by a hash of the week |
| list | every add-on, built (linked) and ideas, by section, then by [groups.py](groups.py)'s role and group (the UI's headings), the built ones first and the ideas under a heading of their own, A to Z. Each has an anchor (`ADDONS.md#pdf`) and two lines: its line; then what it needs and where it goes online in words, and its tags |

**Where each add-on goes:** [groups.py](groups.py), beside readme.py, is
the one grouping: the roles, their titles and order, and each role's second
level (readers by what their files come from, ways in by where you'd be,
suggesting in two). [ui/canvas.py](../../../ui/canvas.py) reads it for the
page, and the list for ADDONS.md; [test_groups.py](test_groups.py) fails a
built add-on it doesn't place, a name it places twice, and a UI that keeps a
copy of its own.

ADDONS.md holds all four, each between `<!-- willow:NAME -->` and
`<!-- /willow:NAME -->`. Everything outside the markers is written by hand
and never touched.

**The front page.** README.md holds two blocks. `summary` gives one line per
section: what it's for (the phrase in readme.py's `WHAT`), and a built
example or two, linked (readme.py's `EXAMPLES`, chosen by hand and checked to
be built and in that section). `front` shows
one of pools, newest or pick, as its `show=` says, and links to ADDONS.md. To
switch it, change `show=` in the marker (`<!-- willow:front show=newest -->`)
and run `write`; anything else there is refused.

**What it reads:** each built add-on's card header (the comment at the top of
its README.md: `section`, `line`, `source`, `added`, `writes`, `network`,
`tags`, `from`, and for one in `adapters/deps/`, `needs`), and `adapters/planned.json`
for the ones not built yet. A field no card has is refused. `from` is
checked as [adapters/README.md](../../README.md#what-a-folder-holds) says:
how (`shape`, `code`, `dep`), an https:// address and a licence, no code
from a copyleft or unlicensed project, `dep` only from a deps add-on, and
code taken refused until the source's notice is in the folder. The list
says it after the facts, "From: shape of wagtail/Willow, BSD-3-Clause.", the
name linked to its address. A name is built when its folder exists; then it
must not also be planned. Building an add-on is what turns an idea into a
built one.

**Tags:** up to five per add-on, worked out by
[similar](../similar/): `no-install` or `needs-install`; `offline`,
`this-machine`, `online`, or `to-a-model` for one that reaches nothing
itself but hands something to a model (its card's `hands:` line); two topic
words the add-on shares with its
nearest neighbours on the list; and the one tag its author chose, the card's
`tags:` line, if it has one. Each entry also names its three nearest
neighbours. It never writes a card or `adapters/planned.json`.

**The topic words and the neighbours stand for the week.** They're worked
out over every card's whole text, so a pull request that added an entry, or
edited any card, moved other entries' lines, and made every other open pull
request's list stale. The week's first `write` keeps them for every entry in
`adapters/stdlib/readme/week.json`; until the next week, an entry it names
keeps them, and a new one is worked out against the week's entries and
itself alone, so its line is its own whatever else lands. The counts are the
week's entries too: a new one counts from the next week. An entry's install
and online facts and its author's tag are read from its card every time, so
a card that starts going online says so the same day. `check` holds the file
to the page's week.

**Deterministic:** the same repo gives the same README. The week of the pick is
written into its section, `write` sets it, and `check` rebuilds with it, so the
draw changes only when someone writes. The draw is the SHA-256 of
"willow add-on of the week" and the week, modulo the built add-ons in name
order, so anyone can redo it.

**Checked on every push:** its tests run `check` against the real README.md
and fail if a generated section is out of date.

**Uses:** the kernel's `h256` and its exit codes.

**Never:** writes outside its markers, changes tags someone wrote, or decides
by hand whether an add-on is built.
