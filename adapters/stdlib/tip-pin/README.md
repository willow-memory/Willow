<!-- willow-addon
section: Trust and proof
line: Where your record ends, written down somewhere willow can't reach, so rows cut off the end or rewritten from some point on are caught where verify can't.
source: new
added: 2026-10-26
writes: to
network: none
-->
# tip-pin

Where a box's record ends, written to a file you keep out of the box's reach,
and checked later. The kernel's `verify` finds an edit to one past row; it
can't find rows cut off the end, or rows removed and then all re-hashed from
there on, because nothing outside the box says what the last hash or the
length should be. A pin does.

    python adapters/stdlib/tip-pin/tip_pin.py pin   --box DIR --to FILE
    python adapters/stdlib/tip-pin/tip_pin.py check --box DIR --pin FILE

    pinned 12 rows, tip 3f9a0c61d2b4…, to /media/usb/pin.json
    keep it where whoever writes the box can't reach

    holds       12 rows pinned; the box has 15 (3 added since)
    cut short   12 rows pinned; the box has 9
    rewritten   row 11 is not the one you pinned

A pin is two facts: how many rows the record had, and the hash of the last.
A record only grows, so a box that holds has the pinned row where it was and
may have more after it. It fails two ways:

- **cut short**: the box has fewer rows than were pinned.
- **rewritten**: the row where the pin ended isn't the pinned one. Every hash
  after an edited row changes with it, so re-hashing a record to hide an edit
  changes the hash that was pinned.

A pin only helps if whoever might rewrite the box can't rewrite it too: a
USB stick, another machine, a printed line. Pin again after you want the
new rows covered; a pin never moves by itself and `pin` never writes over a
file.

A record that doesn't verify is refused by both commands: the chain itself
says what is wrong, and a pin of a broken record would pin the break. Seals
need no pin: they can't be forged without your key, so what a pin guards is
the bites, suggestions and declines around them.

**Exit codes:** for `pin`, 0 written, 2 refused. For `check`, 0 holds; 42
cut short or rewritten, and waits on you; 2 refused (a pin that isn't one, a
record that doesn't verify, or a folder that isn't a box).

**Uses:** the kernel's `read`, `config` and its exit codes.

**Never:** reads your key; changes the box or your folder; writes anywhere
but FILE; writes FILE inside the box or your folder, over a file that's
there, or in a folder that doesn't exist. FILE is readable only by you.
