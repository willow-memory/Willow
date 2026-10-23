# adapters

Things built on top of `kernel.py`. The kernel is the base, and it runs alone:
delete this folder and it behaves the same, byte for byte.

The list of add-ons, built and planned, is in the main README under
[What you can build on it](../README.md#what-you-can-build-on-it). It is
generated from the cards here, so this page holds only the rules.

## The one rule: the arrow points one way

An add-on uses the kernel; the kernel never imports, loads or names an add-on.
An add-on that writes to a record writes only through the kernel's own
`append` (or its commands), so the chain holds; anything that writes around
it, `verify` catches.

What an add-on can rely on:

- **the record:** rows, canonical JSON, the hash chain from 64 zeros
- **the functions:** `chunks`, `rank`, `look`, `read`, `append`, `verify`,
  `bite_key`, `newest`, `words`, `holds`, `held_by`, `config`, `read_words`,
  `h256`, held to `vectors/`
- **the command line:** exit 0 a person said it, 42 not enough to say, 2
  refused

## Two folders

- [stdlib/](stdlib/): needs nothing beyond Python's standard library, like the
  kernel. Copy the folder and run it.
- [deps/](deps/): needs something installed. Its card names every install up
  front, and it carries a pinned `requirements.txt` and a
  `requirements-floor.txt`: it is tested at both, the floor being each
  package's last release of 2020, or its first, or a higher one the card
  gives a reason for; see [deps/README.md](deps/README.md).

## What a folder holds

- the code;
- a card, `README.md`: what it's for, which of the kernel's surface it uses,
  what it never does;
- its own tests (`test_*.py`), which CI runs.

The card opens with a header that the main README's list is generated from:

    <!-- willow-addon
    section: Keeping track
    line: Numbers over time and a date gone by, beside an answer.
    source: box
    added: 2026-10-22
    writes: nothing
    network: none
    tags: no-install, offline, read-only, tracking
    -->

`section` is one of the list's sections, `line` is one sentence, `source` is
`bot` (rebuilt from willow-bot's one script), `box` (built from what the
kernel has) or `new`, and `added` is the date it was built. An add-on in
`deps/` adds `needs` (what to install, and its licence) and `floor` (its
floor versions, and why when above the rule's).

`tags` are up to five, lowercase words joined by -, for finding it. When a
card or idea has none,

    python adapters/stdlib/readme/readme.py tags

fills in four from what the header already says (an install or none, where
it goes online, what it writes, its section), leaving the fifth for you. It
never touches tags that are there: change them as you like. Tags are for
finding things, never a promise: what it needs and where it goes are said
from `needs` and `network`, whatever the tags say.

## Its promises, checked

`writes` and `network` are promises, and CI holds every add-on to them:

| Line | Values |
|---|---|
| `writes` | `nothing` (it only prints); `record` (it writes the record, through the kernel); `to` (it writes only where `--to` points: a mirror folder, or one file); or a file of this repo by name, such as `README.md`. Several are joined with commas. |
| `network` | `none`; `loopback` (this machine only); or what it reaches and why, such as `api.anthropic.com, to ask for suggestions`. |

Three more hold for every add-on, whatever its card says: it never changes
an original (the folder given to `--from`, or a box's pile), never writes a
box but through the kernel, and never reads the key itself.

The add-ons' tests run under a guard, [ci/guard](stdlib/ci/guard/), loaded
into every Python process they start. It watches each file written, removed
or renamed, each read of the key, and each connection or name lookup, works
out whose code asked, and checks it against that add-on's card. A breach
stops the add-on and goes on a log, and a breach the add-on catches and
hides is still on the log; CI fails a run whose log isn't empty. The guard
sees what the tests run, so a promise is only as checked as the tests are
thorough.

## Adding an idea, or building one

Anyone can do either; [CONTRIBUTING.md](../CONTRIBUTING.md) says how. An idea is
an entry in [planned.json](planned.json) with the same fields as a card,
promises included, and a `kind` (`stdlib` or `deps`). Before adding one, see
what's near it:

    python adapters/stdlib/similar/similar.py near "your idea in a sentence"

To build one, make its folder, write its card with the header (the same
promises, or changed in the open with the reason in the pull request), and
take its entry out of [planned.json](planned.json) in the same change, then
run

    python adapters/stdlib/readme/readme.py write

CI fails if the main README is behind the cards, if a name is both built and
planned, if two entries have the same line, if a folder is missing its card
or tests, or if an add-on breaks a promise while its tests run.
