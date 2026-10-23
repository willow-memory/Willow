<!-- willow-addon
section: For maintainers
line: Builds this README's generated sections from the add-ons' own cards.
source: new
added: 2026-10-23
-->
# readme

README.md's generated sections, built from the add-ons themselves, so the
front page can't drift from what's in the repo.

    python adapters/stdlib/readme/readme.py write [--week YYYY-Www]
    python adapters/stdlib/readme/readme.py check

| Section | What it shows |
|---|---|
| pools | how the add-ons spread: by section, built and planned, 🐍 and 📦, with a progress bar |
| newest | the five most recently built add-ons, by the date on their card |
| pick | the add-on of the week, drawn by a hash of the week |
| list | every add-on, built (✅, linked) and planned (🛠), by section, A to Z |

Each sits between `<!-- willow:NAME -->` and `<!-- /willow:NAME -->` in
README.md. Everything outside the markers is written by hand and never touched.

**What it reads:** each built add-on's card header (the comment at the top of
its README.md: `section`, `line`, `source`, `added`, and for one in
`adapters/deps/`, `needs` and `network`), and `adapters/planned.json` for the
ones not built yet. A name is built when its folder exists; then it must not
also be planned. Building an add-on is what turns its 🛠 into ✅.

**Deterministic:** the same repo gives the same README. The week of the pick is
written into its section, `write` sets it, and `check` rebuilds with it, so the
draw changes only when someone writes. The draw is the SHA-256 of
"willow add-on of the week" and the week, modulo the built add-ons in name
order, so anyone can redo it.

**Checked on every push:** its tests run `check` against the real README.md
and fail if a generated section is out of date.

**Uses:** the kernel's `h256` and its exit codes.

**Never:** writes outside its markers, or decides by hand whether an add-on is
built.
