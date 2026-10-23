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
    -->

`section` is one of the list's sections, `line` is one sentence, `source` is
`bot` (rebuilt from willow-bot's one script), `box` (built from what the
kernel has) or `new`, and `added` is the date it was built. An add-on in
`deps/` adds `needs` (what to install, and its licence), `floor` (its
floor versions, and why when above the rule's) and, if it goes online,
`network`.

## Building a planned one

Make its folder, write its card with the header, and take its entry out of
[planned.json](planned.json) in the same change, then run

    python adapters/stdlib/readme/readme.py write

CI fails if the main README is behind the cards, if a name is both built and
planned, or if a folder is missing its card or tests.
