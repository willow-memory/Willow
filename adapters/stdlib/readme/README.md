<!-- willow-addon
section: For maintainers
line: Builds this README's generated sections from the add-ons' own cards.
source: new
added: 2026-10-23
writes: README.md, adapters/planned.json, adapters/*/*/README.md
network: none
tags: no-install, offline, writes-output, maintainers
-->
# readme

README.md's generated sections, built from the add-ons themselves, so the
front page can't drift from what's in the repo.

    python adapters/stdlib/readme/readme.py write [--week YYYY-Www]
    python adapters/stdlib/readme/readme.py check
    python adapters/stdlib/readme/readme.py tags

| Section | What it shows |
|---|---|
| pools | how the add-ons spread: by section, built and ideas, how many need an install, with a progress bar |
| newest | the five most recently built add-ons, by the date on their card |
| pick | the add-on of the week, drawn by a hash of the week |
| list | every add-on, built (linked) and ideas, by section, A to Z: its line, what it needs and where it goes online in words, and its tags |

Each sits between `<!-- willow:NAME -->` and `<!-- /willow:NAME -->` in
README.md. Everything outside the markers is written by hand and never touched.

**What it reads:** each built add-on's card header (the comment at the top of
its README.md: `section`, `line`, `source`, `added`, `writes`, `network`,
`tags`, and for one in `adapters/deps/`, `needs`), and `adapters/planned.json`
for the ones not built yet. A name is built when its folder exists; then it
must not also be planned. Building an add-on is what turns an idea into a
built one.

**Tags:** up to five per add-on. `tags` fills in four for any card or idea
that has none, from what its header already says (`no-install` or
`needs-install`; `offline`, `this-machine` or `online`; `read-only`,
`records` or `writes-output`; its section), and leaves the fifth for a
person. It never touches tags that are there: once written, they are the
card's. That is why its card says it writes the cards and
`adapters/planned.json`, as well as README.md.

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
