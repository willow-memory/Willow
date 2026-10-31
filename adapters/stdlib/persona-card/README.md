<!-- willow-addon
section: Assistants
line: A persona written as a card and compiled into the same system-prompt bytes every time, with the prompt's hash on the record.
source: box
added: 2026-10-31
writes: record
network: none
tags: no-install, offline, records, assistant
-->
# persona-card

A persona card compiled into the same system-prompt bytes every time, with
the prompt's hash on the record.

    python adapters/stdlib/persona-card/persona_card.py \
        --box DIR --from FILE [--now TS]
    python adapters/stdlib/persona-card/persona_card.py \
        check --box DIR --from FILE

    compiled  Binder  sha256=…  (row 1)
    # Binder

    You file everything.

A card is a markdown file. An optional header names it:

    <!-- willow-persona
    name: Binder
    -->

Without one, the file's stem is the name. The compiled prompt is always
`# name`, a blank line, the body, one trailing newline: the same card
gives the same bytes. That SHA-256 is appended through the kernel, never
the prompt itself. `--from` a folder compiles every markdown card in it
(hidden parts skipped).

`check` holds a card to its latest row: `same`, `changed`, or
`never compiled`.

It cannot approve anything. Exit codes, the kernel's: 0 compiled, or
every card the same; 42 a card changed or was never compiled; 2 refused.

**Uses:** the kernel's `append`, `read`, and exit codes.

**Never:** writes the prompt onto the record, reads the key, or seals.
