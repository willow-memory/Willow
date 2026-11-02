<!-- willow-addon
section: Ways to use it
line: An answer as a printable page with its sources, to take to an appointment; --large for big, high-contrast type.
source: new
added: 2026-10-24
writes: record, to
network: none
tags: everyday
-->
# print

An answer on paper, with where it came from.

    python adapters/stdlib/print/print.py --box DIR --to dentist.html "when is the dentist"

It asks the kernel (its own `bite`, on the record as if typed) and writes
one page with the question, the day it was asked, and the answer. That's
your approved answer if you approved one; otherwise it's the passages from
your files, each with its file and line. Open it in a browser and print it,
or save it as a PDF to take to an appointment.

`--large` sets it in large, high-contrast type, for reading without
glasses. That's the large-print idea, built as a switch here rather than as
a second add-on.

At the foot: the record's row and fingerprint for the question, so the
page can be checked against the record later. The page has no script and
loads nothing. A file already at `--to` is never overwritten.

**Uses:** the kernel's `bite` and `read`.

**Never:** overwrites a file, or puts anything on the page your files and
approvals didn't say.
