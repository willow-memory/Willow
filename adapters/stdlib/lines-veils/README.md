<!-- willow-addon
section: Play
line: What never happens at your table and what happens off-screen, checked before a part is read; the X-card kept with no one named.
source: new
added: 2026-11-23
version: 0.1.0
writes: record
network: none
role: tools
from: shape, https://github.com/rudi193-cmd/die-namic-games, Apache-2.0
-->
# lines-veils

What never happens at your table, and what happens only off-screen, written
once in your own words; and the X-card and the pause, kept on the record as
having happened and nothing more.

    python adapters/stdlib/lines-veils/lines_veils.py --page <pile>/our-lines.md show
    line  spiders
    line  a pet getting hurt
    veil  kissing

    python adapters/stdlib/lines-veils/lines_veils.py --page <pile>/our-lines.md touches "A spider drops from the beam."
    line  spiders: it doesn't happen; say what happens instead

    python adapters/stdlib/lines-veils/lines_veils.py --box DIR x --game 3 --at 2
    set aside, no reason asked and no one named   (row 41)

    python adapters/stdlib/lines-veils/lines_veils.py --box DIR pause
    paused, no reason asked and no one named   (row 42)

**The page** is markdown, a list under each of two headings, as a family
writes it:

    ## Lines
    - spiders
    - a pet getting hurt

    ## Veils
    - kissing

A heading with "line" or "lines" in it starts the lines, one with "veil" or
"veils" the veils, any other heading neither; an item is a line starting
`-` or `*`. No page, no lines and no veils.

**Touches.** A line or veil touches a text when every word of it that
carries meaning is there: "a pet getting hurt" needs pet and hurt, and
"the pet is hurt badly" has both. A plural or a possessive is the same word
(spiders, spider; the stall's hooks, hook). A line of only little words
("being") needs them all. So a line is never missed for a plural, and one
word alone from a longer line doesn't trip it. `touches` says which line or
veil, and what to do: a line's part isn't read and the person running the
game says what happens instead; a veil's happens off-screen, said in
passing. It reads the page and the text and writes nothing.

**The X-card and the pause.** Anyone at the table sets the next part aside
(`x`), or stops the whole night (`pause`), no reason asked. Each is a row,
`table-x` or `table-pause`, holding only where it happened: `--game`, the
row of the game it happened in, and `--at`, the part's place in it, and for
the X-card `--part`, what kind of part it was (a call, a moment). Never who
and never why: there is no option for either.

**Exit codes**, the kernel's: 0 done (`touches`: something touched); 42
`touches`: nothing touched; 2 refused, with why (a folder that isn't a box,
a record that doesn't verify, a place that isn't a whole number, a command
line it hasn't).

**Source:** Die-Namic's table, whose safety module this is, rebuilt here. Lines
and veils, and the X-card, are tabletop games' own safety tools; this only
reads a table's words for them.

**Uses:** the kernel's `append` and `read`.

**Never:** names who set a part aside or why, decides what happens instead,
reads your key, or goes online.
