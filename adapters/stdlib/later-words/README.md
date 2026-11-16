<!-- willow-addon
section: Your own words
line: A box made again with a words list it lacked, its record kept as it was, since a box takes its words only when it is made.
source: new
added: 2026-11-16
version: 0.1.0
writes: record, to
network: none
role: words
-->
# later-words

A box made again with a words list it lacked, its record kept as it was.

    python adapters/stdlib/later-words/later_words.py --box DIR --words FILE --to NEWDIR

**Why again.** A box takes its words list only when the kernel makes it
(`init --words`, which writes the list's place into the box's settings); nothing
afterwards adds one. A person's own words are learned from what found nothing,
which is day two, after the box has a record. So the box is made again beside
the old one, and the old one's record goes with it.

**When it is not needed.** A box made *with* a words list points at the file,
and the kernel reads the file at every bite: add lines to that file and the
box has them from the next bite, with nothing made again (each bite row keeps
the SHA-256 of the list it read). This is for the box made with none.

**What carries over, and how.** The record is not copied as a file and not
rewritten. Its rows are laid down again in order through the kernel's own
`append`, each with the fields it had, so the chain comes out the same bytes
as before: every seal and decline still proves under your key, every proposal
still names its question. The proposals and the answers written under the box
are copied as they are. It checks that the new record is the old one's bytes
and that `kernel.py verify --box NEWDIR` holds before it says it is done, and
`verify` on the old box is run first: a record that doesn't hold isn't carried.

**What it changes.** One thing: the new box's settings name FILE as the
words list. From the next bite on, each bite row carries the list's SHA-256,
as `init --words` boxes always have; the rows before it, made without a list,
stay as they were.

**Refused**, writing nothing: a box that already has a words list; a list the
kernel's `read_words` refuses (readable beyond you, inside a box, a bad line);
a NEWDIR that isn't empty, is inside a box, or holds or sits inside the old
box; a record whose first row isn't the one this kernel's `init` would make
(another kernel version, another pile); a key that isn't where the box says.

**Uses:** the kernel's `init`, `read`, `append`, `verify` and `read_words`.

**Never:** reads or makes your key (a missing key stops it, rather than `init`
making a new one), changes the old box, or writes anything in the old
box's files.
