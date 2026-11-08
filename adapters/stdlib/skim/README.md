<!-- willow-addon
section: For maintainers
line: The lists this repo makes held to how a person reads them: a heading every screen, no line too long to read, and every add-on and folder a name to jump to.
source: new
added: 2026-11-08
writes: nothing
network: none
role: repo
runs-in: repo
-->
# skim

The lists this repo makes, held to how a person reads them. FILES.md and
ADDONS.md are made by scripts and checked against the repo, but nothing
checks that someone can read them: a name found with nowhere to jump to, a
screen with no heading to say where you are. skim says each place, so the
lists can be made easier to read and kept that way. The notes it came from,
with what leans on both lists' shape, are in
[docs/design/lists.md](../../../docs/design/lists.md).

    python adapters/stdlib/skim/skim.py check [FILE ...] [--screen N] [--width N]

With no file it reads FILES.md and ADDONS.md at the repo's root.

| Check | Fails on |
|---|---|
| `screen` | a run of lines with no heading longer than a screen (`--screen`, 60), code blocks included: a tree is still read |
| `width` | a line longer than one look (`--width`, 160), a table row aside |
| `jump` | an entry that opens with a bold name (`- **pdf**`, linked or not; one lower-case word, not a bold lead-in) with no anchor for it, and a folder at the top of a tree in a code block (`├── ui/`) with no heading naming it |

Each place is a line, `FILE:LINE: CHECK: what`, and each file ends with
its counts, or `reads within the bounds`. On main today FILES.md is one
run of 1,981 lines; ADDONS.md has 529 lines over 160 characters and 531
add-ons with no anchor.

**It reports; it refuses nothing.** A list that fails is one to make easier
to read, not a broken build, and no gate runs it until the lists pass.

**Never:** writes anything, goes online, or reads more than the files it's
given.

Exit codes, the kernel's: 0 every file reads within the bounds; 42 places
were found, each said; 2 refused (a file that isn't there, or a bad command
line).
